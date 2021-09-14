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
use tracing::warn;

#[derive(Clone, Copy)]
pub enum Destination {
    // Don't upload to any place. (For debug purpose)
    Dry,
    // Upload as Buildkite's artifacts
    Buildkite,
}

/// Upload artifacts (e.g. test logs) by reading the BEP JSON file.
///
/// The file is read in a loop until "last message" is reached or encountered consective errors.
pub fn upload(build_event_json_file: &Path, destination: Destination) -> Result<()> {
    let tmpdir = make_tmpdir();
    let status = ["FAILED", "TIMEOUT", "FLAKY"];
    let mut parser = BepJsonParser::new(build_event_json_file);
    let max_retries = 5;
    let mut retries = max_retries;
    let mut test_log_offset = 0;

    loop {
        match parser.parse() {
            Ok(_) => {
                // If we made progress, reset the retry counter
                retries = max_retries;

                let test_logs_to_upload: Vec<_> = parser.test_logs[test_log_offset..]
                    .iter()
                    .filter(|test_log| status.contains(&test_log.status.as_str()))
                    .collect();
                if let Err(error) = upload_test_logs(&tmpdir, &test_logs_to_upload, destination) {
                    warn!("{:?}", error);
                }
                test_log_offset = parser.test_logs.len();

                if parser.done {
                    return Ok(());
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
}

fn buildkite_artifact_upload(cwd: &Path, artifacts: &[PathBuf]) -> Result<()> {
    let artifacts: Vec<String> = artifacts
        .iter()
        .map(|path| path.display().to_string())
        .collect();
    process::Command::new("buildkite-agent")
        .current_dir(cwd)
        .args(["artifact", "upload", artifacts.join(";").as_str()])
        .output()?;
    Ok(())
}

fn upload_artifacts(cwd: &Path, artifacts: &[PathBuf], destination: Destination) -> Result<()> {
    match destination {
        Destination::Dry => {
            for artifact in artifacts {
                println!("{}", artifact.display());
            }
        }
        Destination::Buildkite => {
            buildkite_artifact_upload(cwd, artifacts)?;
        }
    }

    Ok(())
}

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

fn make_tmpdir() -> PathBuf {
    let base = env::temp_dir();
    loop {
        let i: u32 = rand::random();
        let tmpdir = base.join(format!("bazelci-agent-{}", i));
        if !tmpdir.exists() {
            return tmpdir;
        }
    }
}

fn upload_test_logs(tmpdir: &Path, test_logs: &[&TestLog], destination: Destination) -> Result<()> {
    let mut artifacts = Vec::new();
    // Rename the test.log files to the target that created them
    // so that it's easy to associate test.log and target.
    for test_log in test_logs.iter() {
        let mut attempt = 0;
        if test_log.paths.len() > 1 {
            attempt = 1;
        }

        const FILE_PROTOCOL: &'static str = "file://";
        for path in &test_log.paths {
            if !path.starts_with(FILE_PROTOCOL) {
                warn!("Failed to upload file {}", path);
                continue;
            }
            let path = &path[FILE_PROTOCOL.len()..];
            let new_path = test_label_to_path(&tmpdir, &test_log.target, attempt);
            fs::create_dir_all(new_path.parent().unwrap_or(&new_path)).with_context(|| {
                format!("Failed to create directories for {}", new_path.display())
            })?;
            fs::copy(path, &new_path).with_context(|| {
                format!("Failed to copy file {} to {}", path, new_path.display())
            })?;

            artifacts.push(new_path.strip_prefix(&tmpdir).unwrap().to_path_buf());

            attempt += 1
        }
    }

    upload_artifacts(&tmpdir, &artifacts, destination)?;

    Ok(())
}

struct TestLog {
    target: String,
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
        }
    }

    /// Parse the BEP JSON file until "last message" encounted or EOF reached.
    ///
    /// Errors encounted before "last message", e.g.
    ///   1. Can't open/seek the file
    ///   2. Can't decode the line into a JSON object
    /// are propagated.
    pub fn parse(&mut self) -> Result<()> {
        let mut file = File::open(&self.path)?;
        file.seek(SeekFrom::Start(self.offset))?;

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
                    }

                    if build_event.is_test_summary() {
                        let test_target = build_event
                            .get("id.testSummary.label")
                            .and_then(|v| v.as_str())
                            .unwrap_or("")
                            .to_string();
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
                            target: test_target,
                            status: test_status,
                            paths: test_logs,
                        };
                        self.test_logs.push(test_log);
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
