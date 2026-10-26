# CI Images & Instance Groups Runbook

This runbook explains which files in `bazelbuild/continuous-integration` are baked into container images, GCE VM disk images, or GCE instance templates, and how to build, test, promote, and roll back each one.

When a pull request modifies any of these paths, `.github/workflows/image-rebuild-reminder.yml` (configured via `.github/image-rebuild-map.yml`) posts a sticky comment linking to the relevant section below.

## Quick Reference

| Change Scope | Action Required | Pipeline / Command |
| :--- | :--- | :--- |
| `buildkite/docker/<distro>/*`, `build.sh`, `push.sh` | Rebuild Docker image(s) → push `:latest` → update `@sha256` digests | [`Create Linux Docker Images`](https://buildkite.com/bazel-trusted/create-linux-docker-images) → `python3 buildkite/update_docker_image_hashes.py` |
| `buildkite/create_images.py`, `buildkite/setup-docker.sh` | Rebuild Linux VM image (`x86_64` & `arm64`) → test → promote → recreate MIGs | [`Create Linux VM image`](https://buildkite.com/bazel-trusted/create-linux-vm-image) |
| `buildkite/create_images.py`, `buildkite/setup-windows.ps1` | Rebuild Windows VM image → test → promote → recreate MIGs | [`Create Windows VM image`](https://buildkite.com/bazel-trusted/create-windows-vm-image) |
| `buildkite/instances.yml`, `buildkite/startup-*.sh`, `buildkite/startup-*.ps1`, `buildkite/create_instances.py`, `buildkite/create_instance_template.py` | **No image rebuild needed** — recreate GCE instance groups only | `cd buildkite && ./create_instances.py <group>` |
| `mintlify/*` | Build & push container (`testing/mintlify` on branch → `mintlify` on `master`) | `./mintlify/build.sh` |
| `docgen/Dockerfile`, `docgen/build.sh`, `docgen/Gemfile*` | Build & push `gcr.io/bazel-public/docgen` → update `@sha256` digest | `./docgen/build.sh` → `python3 buildkite/update_docker_image_hashes.py` |
| `buildifier/*` | Build & push `gcr.io/bazel-public/buildifier:latest` | `./buildifier/build.sh` |
| `bazel/oci/*`, `pipelines/docker-update.yml` | Build & push `gcr.io/bazel-public/bazel:<version>` | [`Docker Update`](https://buildkite.com/bazel-trusted/docker-update) or `./bazel/oci/build.sh <version> push` |
| `gitbundle/*` | Update git mirror tarball (`gs://bazel-git-mirror/bazelbuild-mirror.{tar,zip}`) | [`Update Git Mirror Tar Ball`](https://buildkite.com/bazel-trusted/update-git-mirror-tar-ball) |
| `dashboard/{client,server}/*` | Build & push `gcr.io/bazel-public/dashboard/{client,server}:<git-rev>` | `./dashboard/client/build.sh` / `./dashboard/server/build.sh` |
| `slack-bazel-build/docker/*` | Auto-deployed by Cloud Run on merge to `master` | Automatic on `master` |
| `rbe-configs/*` | Regenerate & upload RBE toolchain tarballs to `gs://bazel-ci/rbe-configs/` | `python3 rbe-configs/generate.py --upload` |
| macOS (`MacService`) | Managed outside this repo in Google-internal `MacService` (`google3`) | See [macOS Images](#macos-images-macservice) |

---

## Linux CI Docker Images

Linux CI jobs run inside containers hosted in `gcr.io/bazel-public/<image>` on the `bk-docker` (`x86_64`) and `bk-docker-arm64` (`arm64`) GCE fleets.

### What They Contain

`buildkite/docker/build.sh` downloads `bazelisk` and `buildifier` into a named build context (`tools`) and builds 20 container targets across 8 distribution directories:

| Directory | Targets Built (`gcr.io/bazel-public/...`) | Architectures | Downstream Dependents |
| :--- | :--- | :--- | :--- |
| `buildkite/docker/ubuntu2404/` | `ubuntu2404`, `ubuntu2404-kythe` | `linux/amd64`, `linux/arm64` | Base image for `mintlify/Dockerfile` and `docgen/Dockerfile`; used by `rbe-configs/generate.py` |
| `buildkite/docker/ubuntu2204/` | `ubuntu2204-java17`, `ubuntu2204`, `ubuntu2204-kythe`, `ubuntu2204-bazel-java17` | `linux/amd64`, `linux/arm64` | Used by `gitbundle/` pipeline and `rbe-configs/generate.py` |
| `buildkite/docker/rockylinux8/` | `rockylinux8`, `rockylinux8-java8`, `rockylinux8-java11`, `rockylinux8-java11-devtoolset10`, `rockylinux8-releaser` | `linux/amd64`, `linux/arm64` | Release & legacy glibc CI jobs |
| `buildkite/docker/debian10/` | `debian10-java11` | `linux/amd64` | Debian 10 CI jobs |
| `buildkite/docker/debian12/` | `debian12` | `linux/amd64`, `linux/arm64` | Debian 12 CI jobs |
| `buildkite/docker/debian13/` | `debian13` | `linux/amd64`, `linux/arm64` | Debian 13 CI jobs |
| `buildkite/docker/fedora39/` | `fedora39-java17`, `fedora39-bazel-java17` | `linux/amd64` | Fedora 39 CI jobs |
| `buildkite/docker/fedora40/` | `fedora40-java21`, `fedora40-bazel-java21` | `linux/amd64` | Fedora 40 CI jobs |
| `buildkite/docker/fedora43/` | `fedora43-java25`, `fedora43-bazel-java25` | `linux/amd64` | Fedora 43 CI jobs |

### How to Build & Push (`:latest`)

- **Buildkite pipeline (preferred)**: After merging Dockerfile changes to `master`, trigger [`Create Linux Docker Images`](https://buildkite.com/bazel-trusted/create-linux-docker-images) in `bazel-trusted` (or wait for its nightly schedule at `04:00 UTC`). The pipeline runs `buildkite/docker/build.sh` followed by `buildkite/docker/push.sh`, publishing `gcr.io/bazel-public/<target>:latest`.
- **Manual CLI**:
  ```bash
  cd buildkite/docker
  ./build.sh
  ./push.sh
  ```

### How to Promote to Production (Pin `@sha256` Digests)

Pushing `:latest` to `gcr.io/bazel-public` does **not** change what CI runs on its own. All container references in `buildkite/bazelci.py` (`IMAGE_HASHES`), `buildkite/setup-docker.sh`, `buildkite/terraform/`, `pipelines/*.yml`, and `rules/rbe_presets.json` are pinned by `@sha256:<digest>`.

To promote newly pushed images:

1. Run the digest updater from the repository root (requires [`crane`](https://github.com/google/go-containerregistry/blob/main/cmd/crane/README.md)):
   ```bash
   python3 buildkite/update_docker_image_hashes.py
   ```
2. Update `buildkite/digests.json` to match the new digests so subsequent runs of `update_docker_image_hashes.py` know the current baseline hashes:
   ```bash
   git checkout -- buildkite/digests.json
   # Update the changed entries in buildkite/digests.json to match buildkite/bazelci.py
   ```
3. **Optional follow-ups**:
   - **VM pre-pull cache**: `buildkite/setup-docker.sh` pre-pulls the pinned digests into the Linux VM image (`bk-docker`). Existing VMs will pull the new digest on demand when a job starts; rebuild the [Linux GCE VM image](#linux-gce-vm-images) when convenient to bake the new layer cache onto disk.
   - **RBE toolchain configs**: If compiler or library packages changed in `ubuntu2204` or `ubuntu2404`, regenerate the [RBE toolchain configs](#rbe-toolchain-configs).

### How to Test

1. Open a pull request containing the updated `@sha256` digests.
2. Add the `CI:run` label to the PR (triggers `.github/workflows/testing.yml` to push the PR commit to the `testing` branch), or push the branch to `testing` directly.
3. Run a test build in the `bazel-testing` Buildkite organization (for example, [`bazel-testing/bazel-bazel`](https://buildkite.com/bazel-testing/bazel-bazel)) and verify that jobs pull the new digest and pass.

### How to Roll Back

Revert the PR that updated the `@sha256` digests. Because previous image manifests remain in `gcr.io/bazel-public` by digest, reverting the hash change immediately restores the previous container version without rebuilding.

---

## Linux GCE VM Images

Linux GCE VM images host the `bk-docker`, `bk-docker-arm64`, `bk-trusted-docker`, `bk-testing-docker`, and `bk-testing-docker-arm64` Managed Instance Groups (MIGs).

### What They Contain

- `buildkite/create_images.py`: Defines `bk-testing-docker` (`ubuntu-2204-lts` on `x86_64`) and `bk-testing-docker-arm64` (`ubuntu-2204-lts-arm64` on `c4a-standard-8`).
- `buildkite/setup-docker.sh`: Installs system packages, `buildkite-agent`, Docker CE, `gcloud`, Azul Zulu JDK, `bazelisk`, the local git mirror (`gs://bazel-git-mirror/bazelbuild-mirror.tar`), and pre-pulled `gcr.io/bazel-public/*` Docker images (`x86_64`).

> **Note**: Changes that only touch `buildkite/startup-docker-pdssd.sh` or `buildkite/instances.yml` do **not** require a VM image rebuild — see [GCE Instance Templates & Startup Scripts](#gce-instance-templates-and-startup-scripts).

### How to Build

- **Buildkite pipeline (preferred)**: After merging changes to `master`, trigger [`Create Linux VM image`](https://buildkite.com/bazel-trusted/create-linux-vm-image) in `bazel-trusted` (defined by `pipelines/publish-vm-image.yml` with `VM_FAMILIES="docker docker-arm64"`).
- **Manual CLI**:
  ```bash
  cd buildkite
  ./create_images.py bk-testing-docker bk-testing-docker-arm64
  ```
  This creates new timestamped images in the `bk-testing-docker` and `bk-testing-docker-arm64` image families in GCP project `bazel-public`.

### How to Test (`bazel-testing`)

1. In the [`Create Linux VM image`](https://buildkite.com/bazel-trusted/create-linux-vm-image) pipeline, unblock **Deploy image to testing instances**, or run manually:
   ```bash
   cd buildkite
   ./create_instances.py bk-testing-docker bk-testing-docker-arm64
   ```
2. Trigger representative builds in `bazel-testing` (such as [`bazel-testing/bazel-bazel`](https://buildkite.com/bazel-testing/bazel-bazel)) covering both `default` (`x86_64`) and `arm64` queues.
3. Verify that agents register cleanly, mount the local SSD, start Docker, and complete jobs.
4. In the pipeline, unblock **Confirm testing instances have been tested**.

### How to Promote to Production

> **Warning**: Recreating production instance groups terminates running VMs immediately. Check Buildkite queue activity and promote during a quiet window.

- **Via pipeline**: Unblock **Promote tested image to prod** (runs `buildkite/promote_images.py bk-docker bk-docker-arm64`, creating `bk-docker` and `bk-docker-arm64` images from the tested `bk-testing-docker*` images) and then unblock **Deploy prod image to prod instances** (runs `buildkite/create_instances.py bk-docker bk-docker-arm64 bk-trusted-docker`).
- **Via CLI**:
  ```bash
  cd buildkite
  ./promote_images.py bk-docker bk-docker-arm64
  ./create_instances.py bk-docker bk-docker-arm64 bk-trusted-docker
  ```

### How to Roll Back

`create_instances.py` resolves the latest non-deprecated image in the `bk-docker` and `bk-docker-arm64` families. To roll back to the previous image:

1. List recent images in the family:
   ```bash
   gcloud compute images list --project=bazel-public \
     --filter="family:(bk-docker bk-docker-arm64)" \
     --sort-by=~creationTimestamp
   ```
2. Deprecate the broken image and point it to the previous good image:
   ```bash
   gcloud compute images deprecate <bad-image-name> \
     --project=bazel-public \
     --state=DEPRECATED \
     --replacement=<previous-good-image-name>
   ```
3. Recreate the affected instance groups:
   ```bash
   cd buildkite
   ./create_instances.py bk-docker bk-docker-arm64 bk-trusted-docker
   ```

---

## Windows GCE VM Images

Windows GCE VM images host the `bk-windows`, `bk-trusted-windows`, and `bk-testing-windows` Managed Instance Groups.

### What They Contain

- `buildkite/create_images.py`: Defines `bk-testing-windows` and `windows-playground` (`windows-2022` base image).
- `buildkite/setup-windows.ps1`: Installs Chocolatey packages (Git, MSYS2, Python 3, Azul Zulu JDKs 8/11/17/21, CMake, Ninja, Bazelisk), Visual Studio 2019 & 2022 Build Tools, Windows SDK, LLVM/Clang, `buildkite-agent`, and the local git mirror (`gs://bazel-git-mirror/bazelbuild-mirror.zip`).

> **Note**: Changes that only touch `buildkite/startup-windows-pdssd.ps1` or `buildkite/instances.yml` do **not** require a Windows VM image rebuild — see [GCE Instance Templates & Startup Scripts](#gce-instance-templates-and-startup-scripts).

### How to Build

- **Buildkite pipeline (preferred)**: After merging changes to `master`, trigger [`Create Windows VM image`](https://buildkite.com/bazel-trusted/create-windows-vm-image) in `bazel-trusted` (`pipelines/publish-vm-image.yml` with `VM_FAMILIES="windows"`).
- **Manual CLI**:
  ```bash
  cd buildkite
  ./create_images.py bk-testing-windows
  ```

### How to Test (`bazel-testing`)

1. Unblock **Deploy image to testing instances** in [`Create Windows VM image`](https://buildkite.com/bazel-trusted/create-windows-vm-image), or run:
   ```bash
   cd buildkite
   ./create_instances.py bk-testing-windows
   ```
2. Trigger a build on [`bazel-testing/bazel-bazel`](https://buildkite.com/bazel-testing/bazel-bazel) and verify that Windows steps succeed.
3. Unblock **Confirm testing instances have been tested**.

### How to Promote to Production

During a quiet window:

- **Via pipeline**: Unblock **Promote tested image to prod** (`./promote_images.py bk-windows`) and **Deploy prod image to prod instances** (`./create_instances.py bk-windows bk-trusted-windows`).
- **Via CLI**:
  ```bash
  cd buildkite
  ./promote_images.py bk-windows
  ./create_instances.py bk-windows bk-trusted-windows
  ```

### How to Roll Back

1. Find the bad image and previous good image:
   ```bash
   gcloud compute images list --project=bazel-public \
     --filter="family:bk-windows" \
     --sort-by=~creationTimestamp
   ```
2. Deprecate the bad image and recreate the Windows instance groups:
   ```bash
   gcloud compute images deprecate <bad-windows-image> \
     --project=bazel-public \
     --state=DEPRECATED \
     --replacement=<previous-good-windows-image>
   cd buildkite
   ./create_instances.py bk-windows bk-trusted-windows
   ```

---

## GCE Instance Templates and Startup Scripts

### What They Contain

- `buildkite/instances.yml`: Instance counts, machine types, boot disks, local SSDs, service accounts, and metadata mappings for all MIGs (`bk-docker`, `bk-docker-arm64`, `bk-windows`, `bk-trusted-*`, `bk-testing-*`).
- `buildkite/startup-docker-pdssd.sh`: Linux boot-time script attached via `metadata_from_file: startup-script=startup-docker-pdssd.sh`. Formats/mounts the local NVMe scratch disk, starts the Docker service, fetches the Buildkite token from GCS, and starts `buildkite-agent`.
- `buildkite/startup-windows-pdssd.ps1`: Windows boot-time script attached via `metadata_from_file: windows-startup-script-ps1=startup-windows-pdssd.ps1`. Initializes scratch storage, sets environment variables, fetches the Buildkite token, and starts `buildkite-agent`.
- `buildkite/create_instances.py`, `buildkite/create_instance_template.py`, `buildkite/update_instances.py`: Scripts that create GCE instance templates and replace Managed Instance Groups.

**No VM image rebuild is required** when only these files change, because startup scripts and instance template settings are read directly from this repository when `create_instances.py` creates a new GCE instance template.

### How to Test (`bazel-testing`)

```bash
cd buildkite
# For Linux startup script or instance config changes:
./create_instances.py bk-testing-docker bk-testing-docker-arm64

# For Windows startup script or instance config changes:
./create_instances.py bk-testing-windows
```

Then run a build in `bazel-testing` to verify instance boot and job execution.

### How to Promote to Production

During a quiet window after merging to `master`:

```bash
cd buildkite
# Linux production & trusted fleets:
./create_instances.py bk-docker bk-docker-arm64 bk-trusted-docker

# Windows production & trusted fleets:
./create_instances.py bk-windows bk-trusted-windows
```

### How to Roll Back

Check out the previous commit on `master` (or revert the PR) and re-run `./create_instances.py` for the affected instance groups.

---

## Standalone Utility and Service Images

### Mintlify

- **Images**: `gcr.io/bazel-public/testing/mintlify:latest` (branches) and `gcr.io/bazel-public/mintlify:latest` (`master`).
- **Files**: `mintlify/Dockerfile`, `mintlify/build.sh`, `mintlify/check_docs.sh`, `mintlify/download_json.sh`, `mintlify/annotation.html`, `mintlify/package.json`, `mintlify/package-lock.json`.
- **How to build & test**: Run `./mintlify/build.sh` on a non-`master` branch. The script detects the branch name and pushes to `gcr.io/bazel-public/testing/mintlify:latest`. Test doc validation jobs in `bazel-testing`.
- **How to promote to prod**: After merging to `master`, checkout `master` and run `./mintlify/build.sh` to push `gcr.io/bazel-public/mintlify:latest` (used by `buildkite/bazelci.py`).
- **How to roll back**: Check out the prior commit on `master` and re-run `./mintlify/build.sh`.

### Docgen

- **Image**: `gcr.io/bazel-public/docgen` (pinned by `@sha256` digest).
- **Files**: `docgen/Dockerfile`, `docgen/build.sh`, `docgen/Gemfile`, `docgen/Gemfile.lock`.
  - *Note*: `docgen/docgen.py` is fetched from `master` at runtime by `pipelines/bazel-docgen.yml` and does not require rebuilding the container image.
- **How to build**:
  ```bash
  cd docgen
  ./build.sh
  ```
  Builds and pushes `gcr.io/bazel-public/docgen:latest`.
- **How to test & promote**: Run `python3 buildkite/update_docker_image_hashes.py` (and update `buildkite/digests.json`) to update the `@sha256` digest pinned in `pipelines/bazel-docgen.yml` and `buildkite/bazelci.py`. Test on a PR with `CI:run` or in `bazel-testing` before merging.
- **How to roll back**: Revert the digest update commit in `pipelines/bazel-docgen.yml` and `buildkite/bazelci.py`.

### Buildifier

- **Image**: `gcr.io/bazel-public/buildifier:latest`.
- **Files**: `buildifier/Dockerfile`, `buildifier/build.sh`, `buildifier/buildifier.py`.
- **How to build & promote**:
  ```bash
  cd buildifier
  ./build.sh
  ```
  Builds and pushes `gcr.io/bazel-public/buildifier:latest` (consumed directly by `buildkite/bazelci.py`).
- **How to roll back**: Check out the prior commit and re-run `./buildifier/build.sh`.

### Bazel Release Container

- **Image**: `gcr.io/bazel-public/bazel:<bazel_version>` and `:latest`.
- **Files**: `bazel/oci/Dockerfile`, `bazel/oci/build.sh`, `bazel/oci/install_bazel.sh`, `bazel/oci/install_packages.sh`, `pipelines/docker-update.yml`.
- **How to build, test & promote**:
  - **Buildkite pipeline**: Trigger [`Docker Update`](https://buildkite.com/bazel-trusted/docker-update) in `bazel-trusted` (`pipelines/docker-update.yml`).
  - **Manual CLI**:
    ```bash
    ./bazel/oci/build.sh <bazel_version>        # local build only
    ./bazel/oci/build.sh <bazel_version> push   # build and push :<bazel_version> and :latest
    ```
- **How to roll back**: Re-run `./bazel/oci/build.sh <bazel_version> push` from the previous known-good commit.

### Git Mirror Bundle

- **Archive**: `gs://bazel-git-mirror/bazelbuild-mirror.tar` and `bazelbuild-mirror.zip`.
- **Files**: `gitbundle/gitbundle.sh`, `gitbundle/Dockerfile`.
- **How to build & promote**: The [`Update Git Mirror Tar Ball`](https://buildkite.com/bazel-trusted/update-git-mirror-tar-ball) pipeline in `bazel-trusted` runs `gitbundle/gitbundle.sh` inside the `ubuntu2204` container daily at `04:00 UTC` on `master`, uploading `gs://bazel-git-mirror/bazelbuild-mirror.tar` and `bazelbuild-mirror.zip`. Subsequent [Linux](#linux-gce-vm-images) and [Windows](#windows-gce-vm-images) VM image builds bake that archive onto the agent disk.

### Dashboard

- **Images**: `gcr.io/bazel-public/dashboard/client:<git-rev>` and `gcr.io/bazel-public/dashboard/server:<git-rev>`.
- **Files**: `dashboard/client/Dockerfile`, `dashboard/client/build.sh`, `dashboard/server/Dockerfile`, `dashboard/server/build.sh`.
- **How to build & promote**:
  ```bash
  ./dashboard/client/build.sh   # pushes gcr.io/bazel-public/dashboard/client:<git-rev>
  ./dashboard/server/build.sh   # pushes gcr.io/bazel-public/dashboard/server:<git-rev>
  ```
- **How to roll back**: Redeploy the previous `<git-rev>` image tag.

### Slack Inviter

- **Files**: `slack-bazel-build/docker/Dockerfile`, `slack-bazel-build/docker/nginx.conf`, `slack-bazel-build/docker/run.sh`.
- **How to build & promote**: Cloud Run automatically builds and deploys `slack-bazel-build/docker/Dockerfile` when changes merge to `master` (see `slack-bazel-build/README.md`).
- **How to roll back**: Revert the commit on `master` or route traffic to the previous Cloud Run revision.

### RBE Toolchain Configs

- **Archive**: `gs://bazel-ci/rbe-configs/*.tar`.
- **Files**: `rbe-configs/generate.py`, `rbe-configs/data.py`, `rbe-configs/cpp_env/*.json`.
- **How to build & promote**:
  ```bash
  python3 rbe-configs/generate.py --upload
  ```
  Generates RBE toolchain configuration tarballs against `gcr.io/bazel-public/ubuntu2404:latest` and `ubuntu2204:latest`, uploads them to `gs://bazel-ci/rbe-configs/`, and prints sha256 digests for `rules/rbe_presets.json`.
- **How to roll back**: Revert the `rules/rbe_presets.json` digest update PR.

---

## macOS Images (MacService)

macOS CI machines (`bk-mac` and `bk-trusted-mac` queues) are managed outside this repository through Google-internal **MacService** (`google3/devtools/macservice/...`):

- Base OS/Xcode images (`tahoe-xcode-*`) and the provisioning scripts ISO are built and rolled out in `google3` (see internal playbook `go/bazel-ci-playbook`).
- No paths in `bazelbuild/continuous-integration` are baked into macOS VM images.
