# Dynamic RBE Toolchain Generator (`bazel_ci_rules`)

This folder contains the unified, GCS-free, and Remote Build Execution (RBE) toolchain generator rule (`rbe_config`).

It automates the generation of RBE toolchain configurations dynamically on-the-fly, eliminating the maintenance overhead of pre-generating and uploading configurations to Google Cloud Storage (GCS) buckets when new Bazel versions are released.

---

## 1. Design & Architectural Highlights

- **Dual Execution Modes (`docker` vs `host`)**: Supports both standard Docker-out-of-Docker generation (default when `RBE_CONFIG_CONTAINER` is unset) and direct host environment generation (automatically enabled when `RBE_CONFIG_CONTAINER` is set).
- **Direct Host Toolchain Detection**: When `RBE_CONFIG_CONTAINER` is exported, `rbe_configs_gen` compiles natively on the host using `go build` and runs with `--exec_mode=host`, executing C++ and Java auto-detection (`@@rules_cc...`, `java -version`) against the host filesystem without Docker. The target container image is authoritative from the `RBE_CONFIG_CONTAINER` environment variable.
- **Decoupled Presets Rollout**: Standard environment configurations are stored in a public JSON file (`rules/rbe_presets.json`) on the `master` branch of this repository. At runtime, the repository rule dynamically downloads this file. If the CI maintainers update a container image tag or environment parameter on `master`, **all projects immediately receive the update without modifying their pinned ruleset commit hashes!**

---

## 2. Bzlmod Usage (`MODULE.bazel`)

To configure RBE toolchains using Bzlmod (Bazel 8.0.0+), load and use the `rbe_config_extension` module extension:

### Option A: Using Standard Presets (Recommended)
Simply pass the name of a standard preset (e.g. `"ubuntu"`):
```bazel
bazel_dep(name = "bazel_ci_rules", version = "2.0.0")

# Load and instantiate the RBE config module extension
rbe = use_extension("@bazel_ci_rules//:rbe_config.bzl", "rbe_config_extension")

rbe.config(
    name = "rbe_ubuntu", # Standard target repository name
    preset = "ubuntu",   # Request the generic latest Ubuntu preset
)

use_repo(rbe, "rbe_ubuntu")
```

### Option B: Using Custom Specifications
If you are using a custom compiler container or customized settings, specify the target image and C++ compiler environment directly inside the tag:
```bazel
bazel_dep(name = "bazel_ci_rules", version = "2.0.0")

rbe = use_extension("@bazel_ci_rules//:rbe_config.bzl", "rbe_config_extension")

rbe.config(
    name = "rbe_ubuntu",
    container = "gcr.io/my-custom/image:latest",
    cpp_env = {
        "CC": "gcc",
        "ABI_LIBC_VERSION": "glibc_2.39",
        "ABI_VERSION": "gcc",
        "BAZEL_COMPILER": "gcc",
        "BAZEL_HOST_SYSTEM": "i686-unknown-linux-gnu",
        "BAZEL_TARGET_CPU": "k8",
        "BAZEL_TARGET_LIBC": "glibc_2.39",
        "BAZEL_TARGET_SYSTEM": "x86_64-unknown-linux-gnu",
        "CC_TOOLCHAIN_NAME": "linux_gnu_x86"
    }
)

use_repo(rbe, "rbe_ubuntu")
```

---

## 3. Legacy WORKSPACE Usage

If your repository has not migrated to Bzlmod yet, load and call the `rbe_config` macro inside your `WORKSPACE` file:

### Option A: Using Standard Presets
```python
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "bazel_ci_rules",
    strip_prefix = "bazel_ci_rules-2.0.0", # Pre-packaged release prefix
    url = "https://github.com/bazelbuild/continuous-integration/releases/download/rules-2.0.0/bazel_ci_rules-2.0.0.tar.gz", # Official 2.0.0 tarball release
)

load("@bazel_ci_rules//:rbe_config.bzl", "rbe_config")

rbe_config(
    name = "rbe_ubuntu",
    preset = "ubuntu", # Request the standard 'ubuntu' preset dynamically
)
```

### Option B: Using Custom Specifications
```python
load("@bazel_ci_rules//:rbe_config.bzl", "rbe_config")

rbe_config(
    name = "rbe_ubuntu",
    spec = {
        "container": "gcr.io/my-custom/image:latest",
        "cpp_env": {
            "CC": "gcc",
            "CC_TOOLCHAIN_NAME": "linux_gnu_x86",
            # ...
        }
    }
)
```

---

## 4. Running Builds on Remote Execution (RBE)

Once your workspace is configured with the `rbe_ubuntu` repository, you can compile and test your targets remotely on GCP by passing the standard Remote Execution flags:

```bash
bazel build \
  --extra_toolchains=@rbe_ubuntu//config:cc-toolchain \
  --extra_execution_platforms=@rbe_ubuntu//config:platform \
  --host_platform=@rbe_ubuntu//config:platform \
  --platforms=@rbe_ubuntu//config:platform \
  --javabase=@rbe_ubuntu//java:jdk \
  --host_javabase=@rbe_ubuntu//java:jdk \
  --remote_executor=remotebuildexecution.googleapis.com \
  --remote_instance_name=projects/YOUR_GCP_PROJECT/instances/YOUR_RBE_INSTANCE \
  --google_default_credentials \
  //path/to:your_target
```

### Flag Descriptions:
- `--extra_toolchains=@rbe_ubuntu//config:cc-toolchain`: Registers the dynamically auto-detected C++ compiler toolchain.
- `--extra_execution_platforms` / `--platforms`: Configures Bazel to execute actions and target outputs inside the container's platform environment.
- `--javabase` / `--host_javabase=@rbe_ubuntu//java:jdk`: Resolves Java compilations and host execution using the JDK detected inside the container.
- `--remote_executor`: The gRPC endpoint of the Google Remote Build Execution service.
- `--remote_instance_name`: The RBE instance mapped specifically to your Google Cloud Platform (GCP) project.
- `--google_default_credentials`: Authenticates your remote requests natively using your Google Application Default Credentials (ADC) or system gcloud login.

---

## 5. Execution Modes (`docker` vs `host`)

`rbe_config` supports two execution modes for toolchain auto-detection, automatically selected based on your environment:

### 5.1 Docker Mode (`--exec_mode=docker`, Default)
When `RBE_CONFIG_CONTAINER` is **unset** (e.g., on developer workstations running macOS or Linux):
- **Go Compilation**: `rbe_configs_gen` is compiled inside a sibling `golang:1.21` Docker container using Docker-out-of-Docker (`/var/run/docker.sock`). No local Go compiler is required.
- **Toolchain Detection**: `rbe_configs_gen` pulls and runs the target toolchain container image (from `preset` or `spec["container"]`), mounts host Bazel, and runs C++ and Java auto-detection inside the sandboxed container.

### 5.2 Host Mode (`--exec_mode=host`, Automatic in Container CI)
When the **`RBE_CONFIG_CONTAINER`** environment variable is exported (e.g., in containerized CI workers or Buildkite pipelines):
- **Automatic Activation**: `rbe_config` automatically switches to `host` mode.
- **Go Compilation**: `rbe_configs_gen` is compiled natively on the host using `go build` (requires Go installed in `PATH`; no Docker required).
- **Direct Host Detection**: `rbe_configs_gen` runs with `--exec_mode=host`, discovering C++ compilers (`gcc`/`clang`) and JDK runtimes directly from the host filesystem without invoking Docker.
- **Host Container Authority**: In `host` mode, because detection happens against the host filesystem, the RBE execution platform image in `@rbe_ubuntu//config:platform` is **authoritatively determined by `RBE_CONFIG_CONTAINER`** (overriding any requested preset container image to prevent ABI or toolchain discrepancies).

---

## 6. Advanced: Bazel Version & Binary Resolution Strategy

To generate toolchain configurations, `rbe_config` must determine which Bazel version to target and potentially mount a host Bazel binary inside the compiler container. It resolves this using the following **four-tier precedence lookup strategy**:

1. **`RBE_CONFIG_BAZEL_PATH` Environment Variable**: *(Highest Precedence)* Explicitly forces the generator to use this host Bazel binary (passes `--host_bazel_path` to the generator).
2. **`BAZEL_REAL` Environment Variable**: Forces the generator to use this real host Bazel binary (usually set by wrappers like Bazelisk) and passes it as `--host_bazel_path`.
3. **`native.bazel_version` Detection**: Automatically detects the version string of the running Bazel (e.g., `"9.1.0"` or `"8.4.2"`). If found, it passes `--bazel_version` to `rbe_configs_gen`, which allows the generator to fetch the matching Bazel release inside the container cleanly without copying host binaries.
4. **System `PATH` scan**: *(Fallback)* If no explicit path is set and version detection fails (e.g., on untagged development builds), it scans the host `PATH` for `bazel` and copies it into the container.

If you run custom development layouts or want to force a specific Bazel binary override, choose one of the following methods:

### Method 1: Shell Export (Explicit Override)
Export the path to your executable in your active terminal session before running the build:
```bash
export RBE_CONFIG_BAZEL_PATH=/path/to/your/custom_bazel
bazel build //...
```

### Method 2: Using a `tools/bazel` Wrapper (Recommended)
Creating a wrapper script at **`tools/bazel`** at the root of your workspace is the cleanest, zero-configuration way. Bazel and Bazelisk automatically execute this wrapper, which can capture the real running binary path (`BAZEL_REAL`). Our rule will automatically pick up `BAZEL_REAL` and prioritize it over `native.bazel_version`:
```bash
#!/bin/bash
# tools/bazel
# This wrapper script is executed automatically by Bazelisk

# BAZEL_REAL will be automatically detected and prioritized by rbe_config
exec "${BAZEL_REAL}" "$@"
```
