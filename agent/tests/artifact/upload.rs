use anyhow::Result;
use assert_cmd::prelude::*;
use std::fs::File;
use std::io::{Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;

#[cfg(target_os = "windows")]
#[test]
fn test_logs_uploaded_to_buildkite() -> Result<()> {
    let mut cmd = Command::cargo_bin("bazelci-agent")?;
    cmd.args([
        "artifact",
        "upload",
        "--dry",
        "--mode=buildkite",
        "--build_event_json_file=tests\\data\\test_bep_win.json",
    ]);
    cmd.assert()
        .success()
        .stdout(predicates::str::contains("buildkite-agent artifact upload src\\test\\shell\\bazel\\resource_compiler_toolchain_test\\test.log"));

    Ok(())
}

#[cfg(not(target_os = "windows"))]
#[test]
fn test_logs_uploaded_to_buildkite() -> Result<()> {
    let mut cmd = Command::cargo_bin("bazelci-agent")?;
    cmd.args([
        "artifact",
        "upload",
        "--dry",
        "--mode=buildkite",
        "--build_event_json_file=tests/data/test_bep.json",
    ]);
    cmd.assert()
        .success()
        .stdout(predicates::str::contains("buildkite-agent artifact upload src/test/shell/bazel/starlark_repository_test/shard_4_of_6/test_attempts/attempt_1.log"));

    Ok(())
}

fn with_tmpfile<F>(f: F) -> Result<()>
where
    F: Fn(File, &Path) -> Result<()>,
{
    let file = tempfile::NamedTempFile::new()?;
    let path = PathBuf::from(file.path());
    let file = file.persist(&path)?;
    // Keep the tmp file if callback failed
    f(file, &path)?;
    std::fs::remove_file(path)?;
    Ok(())
}

/// Test that if the BEP json file is truncated and the file size is less
/// than current read cursor, the parser can detect that and reread from the start.
#[test]
fn truncate_build_event_json_file_restart() -> Result<()> {
    with_tmpfile(|mut file, path| {
        writeln!(
            file,
            "{}",
            r#"{"id":{"workspace":{}},"workspaceInfo":{"localExecRoot":"/private/var/tmp/_bazel_buildkite/78a0792bf9bb0133b1a4a7d083181fcb/execroot/io_bazel"}}"#
        )?;

        std::thread::spawn(move || {
            std::thread::sleep(Duration::from_secs(1));
            file.set_len(0).unwrap();
            file.seek(SeekFrom::Start(0)).unwrap();
            writeln!(
                file,
                "{}",
                r#"{"id":{"progress":{}},"progress":{},"lastMessage":true}"#,
            )
            .unwrap();
        });

        let mut cmd = Command::cargo_bin("bazelci-agent")?;
        cmd.args([
            "artifact",
            "upload",
            "--dry",
            "--mode=buildkite",
            format!("--build_event_json_file={}", path.display()).as_str(),
        ]);

        cmd.assert().success();
        Ok(())
    })
}

/// Test that if the BEP json file is truncated and the current read cursor
/// is in the middle of a line (instead of beginning), the parser can detect
/// that and reread from the start.
#[test]
fn truncate_build_event_json_file_recover_from_middle() -> Result<()> {
    with_tmpfile(|mut file, path| {
        writeln!(file, "{}", r#"{}"#)?;

        std::thread::spawn(move || {
            std::thread::sleep(Duration::from_secs(1));
            file.set_len(0).unwrap();
            file.seek(SeekFrom::Start(0)).unwrap();
            writeln!(
                file,
                "{}",
                r#"{"id":{"progress":{}},"progress":{},"lastMessage":true}"#,
            )
            .unwrap();
        });

        let mut cmd = Command::cargo_bin("bazelci-agent")?;
        cmd.args([
            "artifact",
            "upload",
            "--dry",
            "--mode=buildkite",
            format!("--build_event_json_file={}", path.display()).as_str(),
        ]);

        cmd.assert().success();
        Ok(())
    })
}

#[cfg(not(target_os = "windows"))]
#[test]
fn test_logs_deduplicated() -> Result<()> {
    let mut cmd = Command::cargo_bin("bazelci-agent")?;
    cmd.args([
        "artifact",
        "upload",
        "--dry",
        "--mode=buildkite",
        "--build_event_json_file=tests/data/test_bep_duplicated.json",
    ]);
    cmd.assert()
        .success()
        .stdout(predicates::str::contains("buildkite-agent artifact upload src/test/shell/bazel/starlark_repository_test/shard_4_of_6/test_attempts/attempt_1.log").count(1));

    Ok(())
}

#[cfg(not(target_os = "windows"))]
#[test]
fn test_running_json_file() -> Result<()> {
    with_tmpfile(|mut file, path| {
        std::thread::spawn(move || {
            std::thread::sleep(Duration::from_secs(1));
            writeln!(file, "{}", r#"{"id":{"workspace":{}},"workspaceInfo":{"localExecRoot":"/private/var/tmp/_bazel_buildkite/78a0792bf9bb0133b1a4a7d083181fcb/execroot/io_bazel"}}"#).unwrap();

            std::thread::sleep(Duration::from_secs(1));
            writeln!(file, "{}", r#"{"id":{"testSummary":{"label":"//src/test/shell/bazel:starlark_repository_test","configuration":{"id":"7479eaa1eeb472e5c3fdd9f0b604289ffbe45a36edb8a7f474df0c95501b4d00"}}},"testSummary":{"totalRunCount":7,"failed":[{"uri":"file:///private/var/tmp/_bazel_buildkite/78a0792bf9bb0133b1a4a7d083181fcb/execroot/io_bazel/bazel-out/darwin-fastbuild/testlogs/src/test/shell/bazel/starlark_repository_test/shard_4_of_6/test_attempts/attempt_1.log"}],"overallStatus":"FLAKY","firstStartTimeMillis":"1630444947193","lastStopTimeMillis":"1630445154997","totalRunDurationMillis":"338280","runCount":1,"shardCount":6}}"#).unwrap();

            std::thread::sleep(Duration::from_secs(1));
            writeln!(file, "{}", r#"{"id":{"testResult":{}},"testResult":{"testActionOutput":[{"name":"test.log","uri":"file:///private/var/tmp/_bazel_buildkite/78a0792bf9bb0133b1a4a7d083181fcb/execroot/io_bazel/bazel-out/darwin-fastbuild/testlogs/src/test/shell/bazel/starlark_repository_test/shard_4_of_6/test_attempts/attempt_1.log"}],"status":"FAILED"}}"#).unwrap();

            std::thread::sleep(Duration::from_secs(1));
            writeln!(
                file,
                "{}",
                r#"{"id":{"progress":{}},"progress":{},"lastMessage":true}"#
            )
            .unwrap();
        });

        let mut cmd = Command::cargo_bin("bazelci-agent")?;
        cmd.args([
            "artifact",
            "upload",
            "--dry",
            "--mode=buildkite",
            format!("--build_event_json_file={}", path.display()).as_str(),
        ]);

        cmd.assert()
        .success()
        .stdout(predicates::str::contains("buildkite-agent artifact upload src/test/shell/bazel/starlark_repository_test/shard_4_of_6/test_attempts/attempt_1.log"));
        Ok(())
    })
}
