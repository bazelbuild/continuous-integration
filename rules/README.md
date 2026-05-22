# Dynamic RBE Toolchain Generator (`bazel_ci_rules`)

This folder contains the unified, GCS-free, and Remote Build Execution (RBE) toolchain generator rule (`rbe_config`).

It automates the generation of RBE toolchain configurations dynamically on-the-fly, eliminating the maintenance overhead of pre-generating and uploading configurations to Google Cloud Storage (GCS) buckets when new Bazel versions are released.

---

## 1. Design & Architectural Highlights

- **Self-Compiling Go (DooD)**: The repository rule downloads the upstream `bazel-toolchains` source repository and dynamically compiles `rbe_configs_gen` inside a sibling `golang:1.21` Docker container via the host's Docker socket (Docker-out-of-Docker). This eliminates any local Go compiler installation requirements.
- **On-Demand Auto-Detection**: The compiled Go binary launches your target toolchain container, mounts your running host Bazel binary, auto-detects the compiler and JDK runtimes inside the container sandbox, and extracts the generated C++ and Java toolchain configurations directly into Bazel's `output_base`.
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

## 5. Advanced: Custom & Non-Standard Bazel Layouts

To run compiler auto-detection, the repository rule must mount the running Bazel executable inside the container. It resolves this path using a **two-tier lookup strategy**:

1. **`RBE_CONFIG_BAZEL_PATH` Environment Variable**: Checks for a custom environment variable first.
2. **System `PATH` scan**: Checks for a `bazel` executable on the host `PATH` second.

If you have a custom-named Bazel binary (e.g., `my_bazel`), or run custom development layouts where Bazel is not on the system `PATH`, choose one of the following methods:

### Method 1: Shell Export
Explicitly export the path to your executable in your active terminal session before running the build:
```bash
export RBE_CONFIG_BAZEL_PATH=/path/to/your/custom_bazel
bazel build //...
```

### Method 2: Using a `tools/bazel` Wrapper (Recommended)
Creating a wrapper script at **`tools/bazel`** at the root of your workspace is the cleanest, zero-configuration way. Bazel and Bazelisk automatically execute this wrapper, which can capture the real running binary path and propagate it cleanly:
```bash
#!/bin/bash
# tools/bazel
# This wrapper script is executed automatically by Bazelisk

# Propagate Bazel's real path to the repository rule
export RBE_CONFIG_BAZEL_PATH="${BAZEL_REAL}"

exec "${BAZEL_REAL}" "$@"
```
