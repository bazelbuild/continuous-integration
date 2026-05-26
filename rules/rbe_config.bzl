# rules/rbe_config.bzl

def _resolve_preset(repository_ctx, preset_name, container_image, cpp_env):
    """Downloads and resolves standard RBE presets.

    Returns:
        Tuple of (container_image, cpp_env_dict).
    """
    if not preset_name:
        return container_image, cpp_env

    presets_json_path = "rbe_presets.json"
    # Download dynamic presets from GitHub master branch
    repository_ctx.download(
        output = presets_json_path,
        url = ["https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/rules/rbe_presets.json"],
    )
    presets = json.decode(repository_ctx.read(presets_json_path))
    resolved_preset = presets.get(preset_name)
    if not resolved_preset:
        fail("rbe_config: Preset configuration not found for '{}'.".format(preset_name))

    return resolved_preset["container"], resolved_preset["cpp_env"]


def _download_bazel_toolchains(repository_ctx):
    """Downloads and extracts the bazel-toolchains source repository."""
    repo_zip_url = "https://github.com/bazelbuild/bazel-toolchains/archive/refs/heads/master.zip"
    if repository_ctx.attr.bazel_toolchains_url:
        repo_zip_url = repository_ctx.attr.bazel_toolchains_url

    print("rbe_config: Downloading bazel-toolchains source from {}...".format(repo_zip_url))
    repository_ctx.download_and_extract(
        url = [repo_zip_url],
        output = "bazel-toolchains-src",
        stripPrefix = "bazel-toolchains-master",
    )
    return repository_ctx.path("bazel-toolchains-src")


def _compile_generator(repository_ctx, src_dir):
    """Compiles rbe_configs_gen inside a sibling Go container.

    Returns:
        Path to the compiled generator executable.
    """
    rbe_gen_path = repository_ctx.path("bazel-toolchains-src/rbe_configs_gen")
    print("rbe_config: Compiling rbe_configs_gen via Go container...")
    compile_res = repository_ctx.execute([
        "docker", "run", "--rm",
        "-v", "{}:/srcdir".format(src_dir),
        "-w", "/srcdir",
        "golang:1.21",
        "go", "build", "-o", "/srcdir/rbe_configs_gen", "./cmd/rbe_configs_gen"
    ])

    if compile_res.return_code != 0:
        fail("rbe_config: compilation of rbe_configs_gen failed:\nStdout: {}\nStderr: {}".format(compile_res.stdout, compile_res.stderr))
    return rbe_gen_path


def _generate_toolchains(repository_ctx, rbe_gen_path, bazel_version, bazel_path, container_image, cpp_env):
    """Runs the generator inside the sandboxed container and extracts RBE files."""
    # Serialize C++ environment dict to JSON inside sandbox
    cpp_env_json = "cpp_env.json"
    repository_ctx.file(cpp_env_json, json.encode(cpp_env))

    output_tarball = "rbe_default.tar"
    output_manifest = "manifest.json"

    args = [
        rbe_gen_path,
        "--toolchain_container=" + container_image,
        "--cpp_env_json=" + str(repository_ctx.path(cpp_env_json)),
        "--output_tarball=" + str(repository_ctx.path(output_tarball)),
        "--output_manifest=" + str(repository_ctx.path(output_manifest)),
        "--exec_os=linux",
        "--target_os=linux",
    ]

    if bazel_version:
        args.append("--bazel_version=" + bazel_version)
    elif bazel_path:
        args.append("--host_bazel_path=" + str(bazel_path))
    else:
        fail("rbe_config: Neither bazel_version nor bazel_path is available.")

    print("rbe_config: Executing generator to detect toolchains inside {}...".format(container_image))
    exec_res = repository_ctx.execute(args)

    if exec_res.return_code != 0:
        fail("rbe_config: Dynamic generation failed:\nStdout: {}\nStderr: {}".format(exec_res.stdout, exec_res.stderr))

    # Extract the generated configs directly into the repository's directory
    repository_ctx.extract(archive = output_tarball)


# --- Private Repository Rule Entrypoint ---
def _rbe_config_impl(repository_ctx):
    # 1. Resolve presets/custom image container and environment
    container_image, cpp_env = _resolve_preset(
        repository_ctx,
        repository_ctx.attr.preset_name,
        repository_ctx.attr.container,
        repository_ctx.attr.cpp_env
    )

    # 2. Download bazel-toolchains source code
    src_dir = _download_bazel_toolchains(repository_ctx)

    # 3. Compile rbe_configs_gen
    rbe_gen_path = _compile_generator(repository_ctx, src_dir)

    # 4. Resolve Bazel version or locate host Bazel
    bazel_version = None
    bazel_path = repository_ctx.os.environ.get("RBE_CONFIG_BAZEL_PATH")

    if bazel_path:
        print("rbe_config: RBE_CONFIG_BAZEL_PATH env var is set, using host bazel path: {}".format(bazel_path))
    else:
        bazel_path = repository_ctx.os.environ.get("BAZEL_REAL")
        if bazel_path:
            print("rbe_config: BAZEL_REAL env var is set, using host bazel path: {}".format(bazel_path))
        else:
            bazel_version = getattr(native, "bazel_version", None)
            if bazel_version:
                print("rbe_config: Using detected bazel_version: {}".format(bazel_version))
            else:
                print("rbe_config: native.bazel_version not available, falling back to host bazel from PATH")
                bazel_path = repository_ctx.which("bazel")
                if bazel_path:
                    print("rbe_config: Using Bazel binary at {} for toolchain generation".format(bazel_path))
                else:
                    fail("rbe_config: Bazel executable not found in PATH. If you are using a custom-named binary or non-standard layout, please export RBE_CONFIG_BAZEL_PATH=/path/to/your/binary or use a tools/bazel wrapper script.")

    # 5. Run the generator and extract configurations
    _generate_toolchains(repository_ctx, rbe_gen_path, bazel_version, bazel_path, container_image, cpp_env)


# Private repository rule
_rbe_config = repository_rule(
    implementation = _rbe_config_impl,
    attrs = {
        "preset_name": attr.string(mandatory = False),
        "container": attr.string(mandatory = False),
        "cpp_env": attr.string_dict(mandatory = False),
        "bazel_toolchains_url": attr.string(mandatory = False),
    },
    environ = [
        "RBE_CONFIG_BAZEL_PATH",
        "BAZEL_REAL",
    ], # Propagate custom Bazel path environment variables
)

# --- Public WORKSPACE wrapper macro ---
def rbe_config(name, preset = None, spec = None, bazel_toolchains_url = None):
    """Unified RBE toolchain generator rule (for WORKSPACE).

    Args:
        name: The name of the repository (usually 'rbe_ubuntu').
        preset: The string name of a standard preset (e.g. "ubuntu").
        spec: A custom config dictionary containing "container" and "cpp_env" keys.
        bazel_toolchains_url: Optional URL override for fetching the bazel-toolchains repository source.
    """
    if preset and spec:
        fail("rbe_config: 'preset' and 'spec' are mutually exclusive. Please specify only one of them.")
    if not preset and not spec:
        fail("rbe_config: Either 'preset' or 'spec' must be specified.")

    if preset:
        _rbe_config(
            name = name,
            preset_name = preset,
            bazel_toolchains_url = bazel_toolchains_url,
        )
    else:
        if "container" not in spec or "cpp_env" not in spec:
            fail("rbe_config: 'spec' dictionary must contain both 'container' and 'cpp_env' keys.")
        _rbe_config(
            name = name,
            container = spec["container"],
            cpp_env = spec["cpp_env"],
            bazel_toolchains_url = bazel_toolchains_url,
        )

# --- Bzlmod Module Extension ---
def _rbe_config_extension_impl(module_ctx):
    for mod in module_ctx.modules:
        for tag in mod.tags.config:
            if tag.preset and (tag.container or tag.cpp_env):
                fail("rbe_config extension: 'preset' and custom specifications are mutually exclusive.")
            if not tag.preset and not tag.container:
                fail("rbe_config extension: Either 'preset' or custom specifications must be provided.")

            if tag.preset:
                _rbe_config(
                    name = tag.name,
                    preset_name = tag.preset,
                )
            else:
                _rbe_config(
                    name = tag.name,
                    container = tag.container,
                    cpp_env = tag.cpp_env,
                )

rbe_config_extension = module_extension(
    implementation = _rbe_config_extension_impl,
    tag_classes = {
        "config": tag_class(
            attrs = {
                "name": attr.string(mandatory = True),
                "preset": attr.string(mandatory = False),
                "container": attr.string(mandatory = False),
                "cpp_env": attr.string_dict(mandatory = False),
            }
        )
    }
)
