use anyhow::Result;
use clap::arg_enum;
use std::path::PathBuf;
use structopt::StructOpt;

use bazelci_agent::artifact::upload::{upload, Destination};

arg_enum! {
    #[derive(Clone, Copy)]
    enum UploadDestination {
        // Don't upload to any place. (For debug purpose)
        Dry,
        // Upload as Buildkite's artifacts
        Buildkite,
    }
}

/// Upload/download artifacts from Bazel CI tasks
#[derive(StructOpt)]
enum ArtifactCommand {
    /// Upload artifacts (e.g. logs for failed tests) from Bazel CI tasks
    #[structopt(rename_all = "snake")]
    Upload {
        /// The file contains the JSON serialisation of the build event protocol.
        /// The agent "watches" this file until "last message" encountered
        #[structopt(long, parse(from_os_str))]
        build_event_json_file: PathBuf,
        /// The destination the artifacts should be uploaded to
        #[structopt(long, possible_values = &UploadDestination::variants(), case_insensitive = true)]
        destination: UploadDestination,
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
                build_event_json_file,
                destination,
            } => {
                let destination = match destination {
                    UploadDestination::Dry => Destination::Dry,
                    UploadDestination::Buildkite => Destination::Buildkite,
                };
                upload(&build_event_json_file, destination)?;
            }
        },
    }

    Ok(())
}
