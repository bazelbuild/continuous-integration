use anyhow::{anyhow, Context, Result};
use serde_json::Value;
use std::{
    env,
    fs::{self, File},
    io::{BufRead, BufReader, Seek, SeekFrom},
    path::{Path, PathBuf, MAIN_SEPARATOR},
    process,
    thread::sleep,
    time::Duration,
};
use tracing::error;

use crate::utils::split_path_inclusive;

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
    let status = ["FAILED", "TIMEOUT", "FLAKY"];
    let mut parser = BepJsonParser::new(build_event_json_file);
    let max_retries = 5;
    let mut retries = max_retries;
    let mut last_offset = 0;

    'parse_loop: loop {
        match parser.parse() {
            Ok(_) => {
                if parser.offset != last_offset {
                    // We have made progress, reset the retry counter
                    retries = max_retries;
                    last_offset = parser.offset;

                    let local_exec_root = parser.local_exec_root.as_ref().map(|str| Path::new(str));
                    for test_summary in parser
                        .test_summaries
                        .iter()
                        .filter(|test_result| status.contains(&test_result.overall_status.as_str()))
                    {
                        for failed_test in test_summary.failed.iter() {
                            if let Err(error) =
                                upload_test_log(dry, local_exec_root, &failed_test.uri, mode)
                            {
                                error!("{:?}", error);
                            }
                        }
                    }
                    parser.test_summaries.clear();
                }

                if parser.done {
                    break 'parse_loop;
                }
            }
            Err(error) => {
                retries -= 1;
                // Abort since we keep getting errors
                if retries == 0 {
                    return Err(error);
                }

                error!("{:?}", error);
            }
        }

        sleep(Duration::from_secs(1));
    }

    let should_upload_bep_json_file =
        debug || (monitor_flaky_tests && parser.has_overall_test_status("FLAKY"));
    if should_upload_bep_json_file {
        if let Err(error) = upload_bep_json_file(dry, build_event_json_file, mode) {
            error!("{:?}", error);
        }
    }

    Ok(())
}

fn upload_bep_json_file(dry: bool, build_event_json_file: &Path, mode: Mode) -> Result<()> {
    upload_artifact(dry, None, build_event_json_file, mode)
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

fn upload_artifact_buildkite(dry: bool, cwd: Option<&Path>, artifact: &Path) -> Result<()> {
    let artifact = artifact.display().to_string();
    execute_command(
        dry,
        cwd,
        "buildkite-agent",
        &["artifact", "upload", artifact.as_str()],
    )
}

fn upload_artifact(dry: bool, cwd: Option<&Path>, artifact: &Path, mode: Mode) -> Result<()> {
    match mode {
        Mode::Buildkite => upload_artifact_buildkite(dry, cwd, artifact),
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
    dry: bool,
    local_exec_root: Option<&Path>,
    test_log: &str,
    mode: Mode,
) -> Result<()> {
    let path = uri_to_file_path(test_log)?;

    if let Some((first, second)) = split_path_inclusive(&path, "testlogs") {
        return upload_artifact(dry, Some(&first), &second, mode);
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

    upload_artifact(dry, local_exec_root, &artifact, mode)
}

#[derive(Debug)]
struct TestSummary {
    overall_status: String,
    failed: Vec<FailedTest>,
}

#[derive(Debug)]
struct FailedTest {
    uri: String,
}

struct BepJsonParser {
    path: PathBuf,
    offset: u64,
    line: usize,
    done: bool,
    buf: String,

    local_exec_root: Option<PathBuf>,
    test_summaries: Vec<TestSummary>,
}

impl BepJsonParser {
    pub fn new(path: &Path) -> BepJsonParser {
        Self {
            path: path.to_path_buf(),
            offset: 0,
            line: 1,
            done: false,
            buf: String::new(),

            local_exec_root: None,
            test_summaries: Vec::new(),
        }
    }

    fn reset(&mut self) {
        self.offset = 0;
        self.line = 1;
        self.done = false;
        self.local_exec_root = None;
        self.test_summaries.clear();
    }

    /// Parse the BEP JSON file until "last message" encounted or EOF reached.
    ///
    /// Errors encounted before "last message", e.g.
    ///   1. Can't open/seek the file
    ///   2. Can't decode the line into a JSON object
    /// are propagated.
    pub fn parse(&mut self) -> Result<()> {
        let mut file = File::open(&self.path)
            .with_context(|| format!("Failed to open file {}", self.path.display()))?;

        let eof = file.seek(SeekFrom::End(0))?;
        if self.offset == 0 || self.offset >= eof {
            // The file is truncated, reset to read from the start
            self.reset();
        }

        file.seek(SeekFrom::Start(self.offset)).with_context(|| {
            format!(
                "Failed to seek file {} to offset {}",
                self.path.display(),
                self.offset
            )
        })?;

        let mut reader = BufReader::new(file);
        loop {
            self.buf.clear();
            let bytes_read = reader.read_line(&mut self.buf)?;
            if bytes_read == 0 {
                return Ok(());
            }
            match BuildEvent::from_json_str(&self.buf) {
                Ok(build_event) => {
                    self.line += 1;
                    self.offset = self.offset + bytes_read as u64;

                    if build_event.is_last_message() {
                        self.done = true;
                        return Ok(());
                    } else if build_event.is_workspace() {
                        self.on_workspace(&build_event);
                    } else if build_event.is_test_summary() {
                        self.on_test_summary(&build_event);
                    }
                }
                Err(error) => {
                    // Newline should always start with '{', otherwise we read from the start next time
                    if !self.buf.starts_with('{') {
                        self.offset = 0;
                    }

                    return Err(anyhow!(
                        "{}:{}: {:?} `{}`",
                        self.path.display(),
                        self.line,
                        &self.buf,
                        error
                    ));
                }
            }
        }
    }

    fn on_workspace(&mut self, build_event: &BuildEvent) {
        self.local_exec_root = build_event
            .get("workspaceInfo.localExecRoot")
            .and_then(|v| v.as_str())
            .map(|str| Path::new(str).to_path_buf());
    }

    fn on_test_summary(&mut self, build_event: &BuildEvent) {
        let overall_status = build_event
            .get("testSummary.overallStatus")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
        let failed = build_event
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
        self.test_summaries.push(TestSummary {
            overall_status,
            failed,
        })
    }

    pub fn has_overall_test_status(&self, status: &str) -> bool {
        for test_log in self.test_summaries.iter() {
            if test_log.overall_status == status {
                return true;
            }
        }

        false
    }
}

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
