use anyhow::Result;
use clap::arg_enum;
use std::{path::PathBuf, time::Duration};
use structopt::StructOpt;

use bazelci_agent::artifact::upload;

arg_enum! {
    #[allow(non_camel_case_types)]
    enum UploadMode {
        // Don't upload to any place. (For debug purpose)
        dry,
        // Upload as Buildkite's artifacts
        buildkite,
    }
}

/// Upload/download artifacts from Bazel CI tasks
#[derive(StructOpt)]
enum ArtifactCommand {
    /// Upload artifacts (e.g. test logs for failed tests) from Bazel CI tasks
    #[structopt(rename_all = "snake")]
    Upload {
        // Upload various files for debug purpose
        #[structopt(long)]
        debug: bool,
        /// The file contains the JSON serialisation of the build event protocol.
        /// The agent "watches" this file until "last message" encountered
        #[structopt(long, parse(from_os_str))]
        build_event_json_file: PathBuf,
        /// The mode the artifacts should be uploaded to
        #[structopt(long, possible_values = &UploadMode::variants(), case_insensitive = true)]
        mode: Option<UploadMode>,
        /// The seconds to wait before watching the BEP file
        #[structopt(long)]
        delay: Option<u64>,
        /// BEP json file is uploaded if there are flaky tests
        #[structopt(long)]
        monitor_flaky_tests: bool,
    },
}

#[derive(StructOpt)]
#[structopt(rename_all = "snake")]
enum Command {
    Artifact(ArtifactCommand),
}

fn main() -> Result<()> {
    let cmd = Command::from_args();

    let subscriber = tracing_subscriber::FmtSubscriber::new();
    tracing::subscriber::set_global_default(subscriber).unwrap();

    match cmd {
        Command::Artifact(cmd) => match cmd {
            ArtifactCommand::Upload {
                debug,
                build_event_json_file,
                mode,
                delay,
                monitor_flaky_tests,
            } => {
                let mode = match mode {
                    Some(UploadMode::dry) => upload::Mode::Dry,
                    Some(UploadMode::buildkite) => upload::Mode::Buildkite,
                    None => upload::Mode::Dry,
                };
                upload::upload(
                    debug,
                    &build_event_json_file,
                    mode,
                    delay.map(|secs| Duration::from_secs(secs)),
                    monitor_flaky_tests,
                )?;
            }
        },
    }

    Ok(())
}
