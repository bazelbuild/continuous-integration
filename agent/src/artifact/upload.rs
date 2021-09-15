use anyhow::{anyhow, Context, Result};
use serde_json::Value;
use std::{
    env,
    fs::{self, File},
    io::{BufRead, BufReader, Seek, SeekFrom},
    path::{Path, PathBuf, MAIN_SEPARATOR},
    process,
    thread::sleep,
    time::{Duration, SystemTime},
};
use tracing::warn;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    // Don't upload to any place. (For debug purpose)
    Dry,
    // Upload as Buildkite's artifacts
    Buildkite,
}

/// Upload artifacts (e.g. test logs) by reading the BEP JSON file.
///
/// The file is read in a loop until "last message" is reached, encountered consective errors or timed out.
pub fn upload(
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
    let mut test_log_offset = 0;
    let mut last_offset = 0;
    let mut last_time = SystemTime::now();
    let timeout = Duration::from_secs(60);

    'parse_loop: loop {
        match parser.parse() {
            Ok(_) => {
                if parser.offset == last_offset {
                    // Didn't make progress, check timeout
                    if let Ok(diff) = SystemTime::now().duration_since(last_time) {
                        if diff > timeout {
                            break 'parse_loop;
                        }
                    }
                } else {
                    last_offset = parser.offset;
                    last_time = SystemTime::now();
                    // We have made progress, reset the retry counter
                    retries = max_retries;

                    let test_logs_to_upload: Vec<_> = parser.test_logs[test_log_offset..]
                        .iter()
                        .filter(|test_log| status.contains(&test_log.status.as_str()))
                        .collect();
                    let local_exec_root = parser.local_exec_root.as_ref().map(|str| Path::new(str));
                    if let Err(error) = upload_test_logs(local_exec_root, &test_logs_to_upload, mode) {
                        warn!("{:?}", error);
                    }
                    test_log_offset = parser.test_logs.len();
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

                warn!("{:?}", error);
            }
        }

        sleep(Duration::from_secs(1));
    }

    if monitor_flaky_tests && parser.has_test_status("FLAKY") {
        upload_bep_json_file(mode, build_event_json_file)?;
    }

    Ok(())
}

fn upload_bep_json_file(mode: Mode, build_event_json_file: &Path) -> Result<()> {
    upload_artifacts(None, &[build_event_json_file], mode)
}

fn execute_command(program: &str, args: &[&str], cwd: Option<&Path>) -> Result<()> {
    let mut command = process::Command::new(program);
    if let Some(cwd) = cwd {
        command.current_dir(cwd.canonicalize()?);
    }
    command.args(args);

    command
        .output()
        .with_context(|| format!("Failed to execute command {:?}", command))?;

    Ok(())
}

fn buildkite_artifact_upload<P: AsRef<Path>>(cwd: Option<&Path>, artifacts: &[P]) -> Result<()> {
    let artifacts: Vec<String> = artifacts
        .iter()
        .map(|path| path.as_ref().display().to_string())
        .collect();

    execute_command(
        "buildkite-agent",
        &["artifact", "upload", artifacts.join(";").as_str()],
        cwd,
    )
}

fn upload_artifacts<P: AsRef<Path>>(cwd: Option<&Path>, artifacts: &[P], mode: Mode) -> Result<()> {
    match mode {
        Mode::Dry => {
            for artifact in artifacts {
                let path = if let Some(cwd) = cwd {
                    cwd.join(artifact)
                } else {
                    artifact.as_ref().to_path_buf()
                };
                println!("Upload artifact: {}", path.display());
            }
        }
        Mode::Buildkite => {
            buildkite_artifact_upload(cwd, artifacts)?;
        }
    }

    Ok(())
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

fn upload_test_logs(local_exec_root: Option<&Path>, test_logs: &[&TestLog], mode: Mode) -> Result<()> {
    if test_logs.is_empty() {
        return Ok(());
    }

    let mut artifacts = Vec::new();
    for test_log in test_logs.iter() {
        const FILE_PROTOCOL: &'static str = "file://";
        for path in &test_log.paths {
            if !path.starts_with(FILE_PROTOCOL) {
                warn!("Failed to upload test log {}: not a local file", path);
                continue;
            }
            let path = Path::new(&path[FILE_PROTOCOL.len()..]);
            if let Some(local_exec_root) = local_exec_root {
                if let Ok(relative_path) = path.strip_prefix(local_exec_root) {
                    artifacts.push(relative_path.to_path_buf());
                } else {
                    artifacts.push(path.to_path_buf());
                }
            } else {
                artifacts.push(path.to_path_buf());
            }
        }
    }

    upload_artifacts(local_exec_root, &artifacts, mode)?;

    Ok(())
}

struct TestLog {
    status: String,
    paths: Vec<String>,
}

struct BepJsonParser {
    path: PathBuf,
    offset: u64,
    line: usize,
    done: bool,
    buf: String,

    test_logs: Vec<TestLog>,
    local_exec_root: Option<String>,
}

impl BepJsonParser {
    pub fn new(path: &Path) -> BepJsonParser {
        Self {
            path: path.to_path_buf(),
            offset: 0,
            line: 1,
            done: false,
            buf: String::new(),

            test_logs: Vec::new(),
            local_exec_root: None,
        }
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
                    return Err(anyhow!(
                        "{}:{}: {:?}",
                        self.path.display(),
                        self.line,
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
            .map(|str| str.to_string());
    }

    fn on_test_summary(&mut self, build_event: &BuildEvent) {
        let test_status = build_event
            .get("testSummary.overallStatus")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
        let failed_outputs = build_event
            .get("testSummary.failed")
            .and_then(|v| v.as_array())
            .cloned()
            .unwrap_or(vec![]);
        let test_logs: Vec<_> = failed_outputs
            .into_iter()
            .map(|output| {
                output
                    .get("uri")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string()
            })
            .collect();
        let test_log = TestLog {
            status: test_status,
            paths: test_logs,
        };
        self.test_logs.push(test_log);
    }

    pub fn has_test_status(&self, status: &str) -> bool {
        for test_log in self.test_logs.iter() {
            if test_log.status == status {
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
    fn test_test_label_to_path() {
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
}
