use anyhow::{anyhow, Context, Result};
use serde_json::Value;
use sha1::{Digest, Sha1};
use std::{
    collections::HashSet,
    env,
    fs::{self, File},
    io::{BufRead, BufReader, Lines, Read},
    path::{Path, PathBuf, MAIN_SEPARATOR},
    process,
    thread::sleep,
    time::Duration,
};
use tracing::error;

use crate::utils::{follow::follow, split_path_inclusive};

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    // Upload as Buildkite's artifacts
    Buildkite,
}

/// Upload artifacts (e.g. test logs) by reading the BEP JSON file.
///
/// The file is read in a loop until "last message" is reached, encountered consective errors.
pub fn upload(
    dry: bool,
    debug: bool,
    build_event_json_file: Option<&Path>,
    mode: Mode,
    delay: Option<Duration>,
    monitor_flaky_tests: bool,
) -> Result<()> {
    if let Some(build_event_json_file) = build_event_json_file {
        watch_bep_json_file(
            dry,
            debug,
            build_event_json_file,
            mode,
            delay,
            monitor_flaky_tests,
        )?;
    }

    Ok(())
}

/// Follow the BEP JSON file until "last message" encounted.
///
/// Errors encounted before "last message", e.g.
///   1. Can't open/seek the file
///   2. Can't decode the line into a JSON object
/// are propagated.
fn build_events(path: &Path) -> impl Iterator<Item = Result<BuildEvent>> {
    let path = path.to_path_buf();
    BuildEventIter {
        path: path.clone(),
        lines: BufReader::new(follow(path)).lines(),
        reached_end: false,
    }
}

struct BuildEventIter<B> {
    path: PathBuf,
    lines: Lines<B>,
    reached_end: bool,
}

impl<B: BufRead> Iterator for BuildEventIter<B> {
    type Item = Result<BuildEvent>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.reached_end {
            return None;
        }

        if let Some(line) = self.lines.next() {
            let build_event = match line {
                Ok(line) => match BuildEvent::from_json_str(&line) {
                    Ok(build_event) => Ok(build_event),
                    Err(error) => Err(anyhow!("{}: {} `{}`", self.path.display(), line, error)),
                },
                Err(err) => Err(anyhow!(err)),
            };
            if let Ok(ref build_event) = build_event {
                self.reached_end = build_event.is_last_message();
            }
            return Some(build_event);
        }

        None
    }
}

fn watch_bep_json_file(
    dry: bool,
    debug: bool,
    build_event_json_file: &Path,
    mode: Mode,
    delay: Option<Duration>,
    monitor_flaky_tests: bool,
) -> Result<()> {
    if let Some(delay) = delay {
        sleep(delay);
    }

    let max_retries = 5;
    let status = ["FAILED", "TIMEOUT", "FLAKY"];
    let mut retries = max_retries;
    let mut local_exec_root = None;
    let mut test_summaries = vec![];
    let mut uploader = Uploader::new();

    'parse: loop {
        for build_event in build_events(build_event_json_file) {
            match build_event {
                Ok(build_event) => {
                    // We have made progress, reset the retry counter
                    retries = max_retries;

                    if build_event.is_workspace() {
                        local_exec_root = build_event
                            .get("workspaceInfo.localExecRoot")
                            .and_then(|v| v.as_str())
                            .map(|str| Path::new(str).to_path_buf());
                    } else if build_event.is_test_result() {
                        let test_result = build_event.test_result();
                        if status.contains(&test_result.status.as_str()) {
                            for output in test_result.test_action_outputs.iter() {
                                if output.name == "test.log" {
                                    if let Err(error) = upload_test_log(
                                        &mut uploader,
                                        dry,
                                        local_exec_root.as_ref().map(|p| p.as_path()),
                                        &output.uri,
                                        mode,
                                    ) {
                                        error!("{:?}", error);
                                    }
                                }
                            }
                        }
                    } else if build_event.is_test_summary() {
                        let test_summary = build_event.test_summary();
                        test_summaries.push(test_summary);
                    }
                }
                Err(err) => {
                    error!("{:?}", err);

                    retries -= 1;
                    if retries > 0 {
                        // Continue from start
                        continue 'parse;
                    } else {
                        // Abort since we keep getting errors
                        return Err(err);
                    }
                }
            }
        }

        break 'parse;
    }

    let should_upload_bep_json_file =
        debug || (monitor_flaky_tests && has_overall_test_status(&test_summaries, "FLAKY"));
    if should_upload_bep_json_file {
        if let Err(error) = upload_bep_json_file(&mut uploader, dry, build_event_json_file, mode) {
            error!("{:?}", error);
        }
    }

    Ok(())
}

fn has_overall_test_status(test_summaries: &[TestSummary], status: &str) -> bool {
    for test_log in test_summaries.iter() {
        if test_log.overall_status == status {
            return true;
        }
    }

    false
}

fn upload_bep_json_file(
    uploader: &mut Uploader,
    dry: bool,
    build_event_json_file: &Path,
    mode: Mode,
) -> Result<()> {
    uploader.upload_artifact(dry, None, build_event_json_file, mode)
}

fn execute_command(dry: bool, cwd: Option<&Path>, program: &str, args: &[&str]) -> Result<()> {
    println!("{} {}", program, args.join(" "));

    if dry {
        return Ok(());
    }

    let mut command = process::Command::new(program);
    if let Some(cwd) = cwd {
        command.current_dir(cwd);
    }
    command.args(args);

    let status = command
        .status()
        .with_context(|| format!("Failed to execute command `{} {}`", program, args.join(" ")))?;

    if !status.success() {
        return Err(anyhow!(
            "Failed to execute command `{} {}`: exit status {}",
            program,
            args.join(" "),
            status
        ));
    }

    Ok(())
}

type Sha1Digest = [u8; 20];

fn read_entire_file(path: &Path) -> Result<Vec<u8>> {
    let mut file = File::open(path)?;
    let mut buf = Vec::new();
    file.read_to_end(&mut buf)?;
    Ok(buf)
}

fn sha1_digest(path: &Path) -> Sha1Digest {
    let buf = match read_entire_file(path) {
        Ok(buf) => buf,
        _ => path.display().to_string().into_bytes(),
    };

    let mut hasher = Sha1::new();
    hasher.update(buf);
    let hash = hasher.finalize();
    hash.into()
}

struct Uploader {
    uploaded_digests: HashSet<Sha1Digest>,
}

impl Uploader {
    pub fn new() -> Self {
        Self {
            uploaded_digests: HashSet::new(),
        }
    }

    pub fn upload_artifact(
        &mut self,
        dry: bool,
        cwd: Option<&Path>,
        artifact: &Path,
        mode: Mode,
    ) -> Result<()> {
        {
            let file = match cwd {
                Some(cwd) => cwd.join(artifact),
                None => PathBuf::from(artifact),
            };
            let digest = sha1_digest(&file);
            if self.uploaded_digests.contains(&digest) {
                return Ok(());
            }
            self.uploaded_digests.insert(digest);
        }

        match mode {
            Mode::Buildkite => self.upload_artifact_buildkite(dry, cwd, artifact),
        }
    }

    fn upload_artifact_buildkite(
        &mut self,
        dry: bool,
        cwd: Option<&Path>,
        artifact: &Path,
    ) -> Result<()> {
        let artifact = artifact.display().to_string();
        execute_command(
            dry,
            cwd,
            "buildkite-agent",
            &["artifact", "upload", artifact.as_str()],
        )
    }
}

#[allow(dead_code)]
fn test_label_to_path(tmpdir: &Path, label: &str, attempt: i32) -> PathBuf {
    // replace '/' and ':' with path separator
    let path: String = label
        .chars()
        .map(|c| match c {
            '/' | ':' => MAIN_SEPARATOR,
            _ => c,
        })
        .collect();
    let path = path.trim_start_matches(MAIN_SEPARATOR);
    let mut path = PathBuf::from(path);

    if attempt == 0 {
        path.push("test.log");
    } else {
        path.push(format!("attempt_{}.log", attempt));
    }

    tmpdir.join(&path)
}

#[allow(dead_code)]
fn make_tmpdir_path(should_create_dir_all: bool) -> Result<PathBuf> {
    let base = env::temp_dir();
    loop {
        let i: u32 = rand::random();
        let tmpdir = base.join(format!("bazelci-agent-{}", i));
        if !tmpdir.exists() {
            if should_create_dir_all {
                fs::create_dir_all(&tmpdir)?;
            }
            return Ok(tmpdir);
        }
    }
}

fn uri_to_file_path(uri: &str) -> Result<PathBuf> {
    const FILE_PROTOCOL: &'static str = "file://";
    if uri.starts_with(FILE_PROTOCOL) {
        if let Ok(path) = url::Url::parse(uri)?.to_file_path() {
            return Ok(path);
        }
    }

    Err(anyhow!("Invalid file URI: {}", uri))
}

fn upload_test_log(
    uploader: &mut Uploader,
    dry: bool,
    local_exec_root: Option<&Path>,
    test_log: &str,
    mode: Mode,
) -> Result<()> {
    let path = uri_to_file_path(test_log)?;

    if let Some((first, second)) = split_path_inclusive(&path, "testlogs") {
        return uploader.upload_artifact(dry, Some(&first), &second, mode);
    }

    let artifact = if let Some(local_exec_root) = local_exec_root {
        if let Ok(relative_path) = path.strip_prefix(local_exec_root) {
            relative_path
        } else {
            &path
        }
    } else {
        &path
    };

    uploader.upload_artifact(dry, local_exec_root, &artifact, mode)
}

#[derive(Debug)]
pub struct TestActionOutput {
    pub name: String,
    pub uri: String,
}

#[derive(Debug)]
pub struct TestResult {
    test_action_outputs: Vec<TestActionOutput>,
    status: String,
}

#[derive(Debug)]
pub struct TestSummary {
    pub overall_status: String,
    pub failed: Vec<FailedTest>,
}

#[derive(Debug)]
pub struct FailedTest {
    pub uri: String,
}

#[derive(Debug)]
pub struct BuildEvent {
    value: Value,
}

impl BuildEvent {
    pub fn from_json_str(str: &str) -> Result<Self> {
        let value = serde_json::from_str::<Value>(str)?;
        if !value.is_object() {
            return Err(anyhow!("Not a JSON object"));
        }

        Ok(Self { value })
    }

    pub fn is_test_summary(&self) -> bool {
        self.get("id.testSummary").is_some()
    }

    pub fn is_test_result(&self) -> bool {
        self.get("id.testResult").is_some()
    }

    pub fn is_workspace(&self) -> bool {
        self.get("id.workspace").is_some()
    }

    pub fn is_last_message(&self) -> bool {
        self.get("lastMessage")
            .and_then(|value| value.as_bool())
            .unwrap_or(false)
    }

    pub fn get(&self, path: &str) -> Option<&Value> {
        let mut value = Some(&self.value);
        for path in path.split(".") {
            value = value.and_then(|value| value.get(path));
        }
        value
    }

    pub fn test_result(&self) -> TestResult {
        let test_action_outputs = self
            .get("testResult.testActionOutput")
            .and_then(|v| v.as_array())
            .map(|test_action_output| {
                test_action_output
                    .iter()
                    .map(|entry| TestActionOutput {
                        name: entry
                            .get("name")
                            .and_then(|v| v.as_str())
                            .unwrap_or("")
                            .to_string(),
                        uri: entry
                            .get("uri")
                            .and_then(|v| v.as_str())
                            .unwrap_or("")
                            .to_string(),
                    })
                    .collect()
            })
            .unwrap_or(vec![]);
        let status = self
            .get("testResult.status")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
        TestResult {
            test_action_outputs,
            status,
        }
    }

    pub fn test_summary(&self) -> TestSummary {
        let overall_status = self
            .get("testSummary.overallStatus")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
        let failed = self
            .get("testSummary.failed")
            .and_then(|v| v.as_array())
            .map(|failed| {
                failed
                    .iter()
                    .map(|entry| FailedTest {
                        uri: entry
                            .get("uri")
                            .and_then(|v| v.as_str())
                            .unwrap_or("")
                            .to_string(),
                    })
                    .collect::<Vec<_>>()
            })
            .unwrap_or(vec![]);

        TestSummary {
            overall_status,
            failed,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_label_to_path_works() {
        let tmpdir = std::env::temp_dir();

        assert_eq!(
            test_label_to_path(&tmpdir, "//:test", 0),
            tmpdir.join("test/test.log")
        );

        assert_eq!(
            test_label_to_path(&tmpdir, "//foo/bar", 0),
            tmpdir.join("foo/bar/test.log")
        );

        assert_eq!(
            test_label_to_path(&tmpdir, "//foo/bar", 1),
            tmpdir.join("foo/bar/attempt_1.log")
        );
    }

    #[cfg(target_os = "windows")]
    #[test]
    fn uri_to_file_path_works() {
        assert_eq!(
            &uri_to_file_path("file:///c:/foo/bar").unwrap(),
            Path::new("c:/foo/bar")
        );
    }

    #[cfg(not(target_os = "windows"))]
    #[test]
    fn uri_to_file_path_works() {
        assert_eq!(
            &uri_to_file_path("file:///foo/bar").unwrap(),
            Path::new("/foo/bar")
        );
    }
}
