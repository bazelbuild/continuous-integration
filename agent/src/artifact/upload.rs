use anyhow::{anyhow, Context, Result};
use quick_xml::events::{BytesCData, BytesStart, BytesEnd};
use serde_json::Value;
use sha1::{Digest, Sha1};
use std::{
    collections::HashSet,
    env, fs,
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
            let build_event =
                match line.with_context(|| format!("Failed to read {}", self.path.display())) {
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
                        for output in test_result.test_action_outputs.iter() {
                            match output.name.as_str() {
                                "test.log" => {
                                    if ["FAILED", "TIMEOUT", "FLAKY"]
                                        .contains(&test_result.status.as_str())
                                    {
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
                                "test.xml" => {
                                    if !test_result.cached {
                                        if let Err(error) = upload_test_xml(
                                            &mut uploader,
                                            dry,
                                            local_exec_root.as_ref().map(|p| p.as_path()),
                                            &output.uri,
                                            test_result.label.as_ref(),
                                            mode,
                                        ) {
                                            error!("{:?}", error);
                                        }
                                    }
                                }
                                _ => {}
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

fn gen_error_content(bazelci_task: &str, label: &str, name: &str, test_log: &str) -> String {
    let mut buf = String::new();
    buf.push_str(&format!("BAZELCI_TASK={}\n", bazelci_task));
    buf.push_str(&format!("TEST_LABEL={}\n", label));
    buf.push_str(&format!("TEST_NAME={}\n", name));
    buf.push_str("\n");
    buf.push_str(&format!("bazel test {} --test_filter={}\n", &label, &name));
    buf.push_str("\n\n");
    buf.push_str(test_log);
    buf
}

fn parse_test_xml(path: &Path, bazelci_task: &str, label: &str) -> Result<Option<Vec<u8>>> {
    use quick_xml::{events::Event, reader::Reader, writer::Writer};
    use std::io::Cursor;

    let mut writer = Writer::new(Cursor::new(Vec::new()));
    let mut has_testcase = false;
    let mut buf = Vec::new();
    let mut reader = Reader::from_file(&path)?;
    let fallback_classname = label.replace("//", "").replace("/", ".").replace(":", ".");
    let mut in_error_tag = false;
    let mut error_tag_stack = 0;
    let mut name = String::new();
    loop {
        match reader.read_event_into(&mut buf)? {
            Event::Eof => break,
            Event::Start(tag) => {
                if in_error_tag {
                    error_tag_stack += 1;
                }

                let tag = match tag.name().as_ref() {
                    b"testcase" => {
                        has_testcase = true;

                        let mut new_tag = BytesStart::new("testcase");
                        let mut has_classname = false;

                        // Provide a fallback classname if it is missing or empty
                        for attr in tag.attributes() {
                            let mut attr = attr?;
                            if attr.key.as_ref() == b"classname" {
                                has_classname = true;
                                if attr.value.len() == 0 {
                                    attr.value = fallback_classname.clone().into_bytes().into();
                                }
                            } else if attr.key.as_ref() == b"name" {
                                name = String::from_utf8_lossy(&attr.value).to_string();
                            }
                            new_tag.push_attribute(attr);
                        }

                        if !has_classname {
                            new_tag.push_attribute(("classname", fallback_classname.as_ref()));
                        }

                        new_tag
                    }
                    b"failure" => {
                        in_error_tag = true;
                        // replace failure with error
                        let mut new_tag = BytesStart::new("error");
                        new_tag.push_attribute(("message", ""));
                        new_tag
                    }
                    b"error" => {
                        in_error_tag = true;
                        tag
                    }
                    _ => tag,
                };
                writer.write_event(Event::Start(tag))?;
            }
            Event::CData(mut cdata) => {
                if in_error_tag {
                    let test_log = String::from_utf8_lossy(&*cdata);
                    let new_content = gen_error_content(bazelci_task, label, &name, &test_log);
                    cdata = BytesCData::new(new_content);
                }

                writer.write_event(Event::CData(cdata))?;
            }
            Event::Text(text) => {
                if in_error_tag {
                    let test_log = String::from_utf8_lossy(&*text);
                    let new_content = gen_error_content(bazelci_task, label, &name, &test_log);
                    let cdata = BytesCData::new(new_content);
                    writer.write_event(Event::CData(cdata))?;
                } else {
                    writer.write_event(Event::Text(text))?;
                }
            }
            Event::End(mut tag) => {
                if in_error_tag {
                    if error_tag_stack > 0 {
                        error_tag_stack -= 1;
                    } else {
                        in_error_tag = false;
                        tag = BytesEnd::new("error");
                    }
                }

                writer.write_event(Event::End(tag))?;
            }
            e => writer.write_event(e)?,
        }
    }

    if !has_testcase {
        return Ok(None);
    }

    Ok(Some(writer.into_inner().into_inner()))
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

fn sha1_digest(buf: &[u8]) -> Result<Sha1Digest> {
    let mut hasher = Sha1::new();
    hasher.update(buf);
    let hash = hasher.finalize();
    Ok(hash.into())
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
            let buf = match std::fs::read(&file) {
                Ok(buf) => buf,
                Err(err) => match err.kind() {
                    // For test
                    std::io::ErrorKind::NotFound => file.display().to_string().into_bytes(),
                    _ => anyhow::bail!(err),
                },
            };
            let digest = sha1_digest(&buf)?;
            if !self.uploaded_digests.insert(digest) {
                return Ok(());
            }
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

    fn upload_test_analytics(
        &mut self,
        dry: bool,
        cwd: Option<&Path>,
        token: &str,
        bazelci_task: &str,
        test_xml: &Path,
        label: &str,
        format: &str,
        forms: &[(impl AsRef<str>, impl AsRef<str>)],
    ) -> Result<()> {
        let full_path = if let Some(cwd) = cwd {
            cwd.join(test_xml)
        } else {
            test_xml.to_path_buf()
        };

        let content = parse_test_xml(&full_path, &bazelci_task, label)?;
        if content.is_none() {
            return Ok(());
        }
        let content = content.unwrap();

        let digest = sha1_digest(&content)?;
        if !self.uploaded_digests.insert(digest) {
            return Ok(());
        }

        println!("Uploading to Test Analytics: data={}", full_path.display());

        let filename = full_path
            .file_name()
            .map(|s| s.to_string_lossy().into_owned());
        let data =
            reqwest::blocking::multipart::Part::bytes(content).mime_str("application/xml")?;
        let data = if let Some(filename) = filename {
            data.file_name(filename)
        } else {
            data
        };
        if !dry {
            let client = reqwest::blocking::Client::new();
            let mut form = reqwest::blocking::multipart::Form::new()
                .part("data", data)
                .text("format", format.to_string());

            for form_value in forms {
                form = form.text(
                    form_value.0.as_ref().to_string(),
                    form_value.1.as_ref().to_string(),
                );
            }

            let request = client
                .post("https://analytics-api.buildkite.com/v1/uploads")
                .header(
                    reqwest::header::AUTHORIZATION,
                    format!("Token token={}", token),
                )
                .multipart(form);
            let mut resp = request.send()?;
            if !resp.status().is_success() {
                let mut msg = String::new();
                resp.read_to_string(&mut msg)?;
                anyhow::bail!(format!("status={}, body={}", resp.status(), msg));
            }
        }

        Ok(())
    }

    pub fn upload_test_xml(
        &mut self,
        dry: bool,
        cwd: Option<&Path>,
        test_xml: &Path,
        label: &str,
    ) -> Result<()> {
        let token = maybe_get_env("BUILDKITE_ANALYTICS_TOKEN");
        let build_id = maybe_get_env("BUILDKITE_BUILD_ID");
        let step_id = maybe_get_env("BUILDKITE_STEP_ID");
        let bazelci_task = maybe_get_env("BAZELCI_TASK");
        if token.is_none() || build_id.is_none() || step_id.is_none() || bazelci_task.is_none() {
            return Ok(());
        }

        let token = token.unwrap();
        let build_id = build_id.unwrap();
        let step_id = step_id.unwrap();
        let bazelci_task = bazelci_task.unwrap();

        let mut forms = vec![
            ("run_env[CI]", "buildkite".to_string()),
            ("run_env[key]", format!("{}/{}", &build_id, &step_id)),
            ("run_env[build_id]", build_id),
            ("run_env[tags][]", bazelci_task.clone()),
        ];

        for (name, env) in [
            ("run_env[url]", "BUILDKITE_BUILD_URL"),
            ("run_env[branch]", "BUILDKITE_BRANCH"),
            ("run_env[commit_sha]", "BUILDKITE_COMMIT"),
            ("run_env[number]", "BUILDKITE_BUILD_NUMBER"),
            ("run_env[job_id]", "BUILDKITE_JOB_ID"),
            ("run_env[message]", "BUILDKITE_MESSAGE"),
        ] {
            if let Some(value) = maybe_get_env(env) {
                forms.push((name, value));
            }
        }

        self.upload_test_analytics(
            dry,
            cwd,
            &token,
            &bazelci_task,
            test_xml,
            label,
            "junit",
            &forms,
        )
    }
}

fn maybe_get_env(key: &str) -> Option<String> {
    std::env::var(key).ok()
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

fn resolve_artifact(
    uri: &str,
    local_exec_root: Option<&Path>,
) -> Result<(Option<PathBuf>, PathBuf)> {
    let path = uri_to_file_path(uri)?;
    if let Some((first, second)) = split_path_inclusive(&path, "testlogs") {
        return Ok((Some(first), second));
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
    Ok((
        local_exec_root.map(|p| p.to_path_buf()),
        artifact.to_path_buf(),
    ))
}

fn upload_test_log(
    uploader: &mut Uploader,
    dry: bool,
    local_exec_root: Option<&Path>,
    test_log: &str,
    mode: Mode,
) -> Result<()> {
    let (cwd, artifact) = resolve_artifact(test_log, local_exec_root)?;
    return uploader.upload_artifact(dry, cwd.as_ref().map(|pb| pb.as_path()), &artifact, mode);
}

fn upload_test_xml(
    uploader: &mut Uploader,
    dry: bool,
    local_exec_root: Option<&Path>,
    test_xml: &str,
    label: &str,
    _mode: Mode,
) -> Result<()> {
    let (cwd, artifact) = resolve_artifact(test_xml, local_exec_root)?;
    return uploader.upload_test_xml(dry, cwd.as_ref().map(|pb| pb.as_path()), &artifact, label);
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
    cached: bool,
    label: String,
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
        let label = self
            .get("id.testResult.label")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
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
        let cached_locally = self
            .get("testResult.cachedLocally")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
        let cached_remotely = self
            .get("testResult.executionInfo.cachedRemotely")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
        let cached = cached_locally || cached_remotely;
        TestResult {
            test_action_outputs,
            status,
            cached,
            label,
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
