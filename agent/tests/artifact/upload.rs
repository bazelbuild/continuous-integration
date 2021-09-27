use anyhow::Result;
use assert_cmd::prelude::*;
use std::process::Command;

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
        .stdout(predicates::str::contains("buildkite-agent artifact upload bazel-out\\x64_windows-fastbuild\\testlogs\\src\\test\\shell\\bazel\\resource_compiler_toolchain_test\\test.log"));

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
        .stdout(predicates::str::contains("buildkite-agent artifact upload bazel-out/darwin-fastbuild/testlogs/src/test/shell/bazel/starlark_repository_test/shard_4_of_6/test_attempts/attempt_1.log"));

    Ok(())
}
