def _available_bazel_versions(manifests):
    bazel_versions = []
    for manifest in manifests:
        bazel_versions.append("'{}'".format(manifest["bazel_version"]))
    return ", ".join(bazel_versions)

def _available_toolchain_names(manifest):
    names = []
    for toolchain in manifest["toolchains"]:
        names.append("'{}'".format(toolchain["name"]))
    return ", ".join(names)

def _find_manifest(manifests, bazel_version):
    for manifest in manifests:
        if manifest["bazel_version"] == bazel_version:
            return manifest

    return None

def _find_toolchain(manifest, toolchain_name):
    for toolchain in manifest["toolchains"]:
        if toolchain["name"] == toolchain_name:
            return toolchain

    return None

def _auto_detect_bazel_version(manifests):
    bazel_version = "UNKNOWN"
    if "bazel_version" in dir(native) and native.bazel_version:
        bazel_version = native.bazel_version

    manifest = _find_manifest(manifests, bazel_version)
    if not manifest:
        manifest = manifests[0]
        print("\nrbe_preconfig: Unsupported version '{}' (Values: {}), using '{}'.\n".format(bazel_version, _available_bazel_versions(manifests), manifest["bazel_version"]))

    return manifest

def _rbe_preconfig_impl(repository_ctx):
    """Download pre-generated RBE toolchain configs based on current Bazel version.

    The manifest is fetched everytime running this repo rule so we can get the
    latest configs without upgrading this rule.

    Args:
      toolchain: The name of the pre-generated toolchain.
    """

    toolchain_name = repository_ctx.attr.toolchain

    manifest_json = 'manifest.json'
    # Omit sha256 since remote file can be changed
    repository_ctx.download(
        output = manifest_json,
        url = ["https://storage.googleapis.com/bazel-ci/rbe-configs/manifest.json"]
    )

    manifests = json.decode(repository_ctx.read(manifest_json))

    manifest = _auto_detect_bazel_version(manifests)

    toolchain = _find_toolchain(manifest, toolchain_name)
    if not toolchain:
        fail("\nrbe_preconfig: Unsupported toolchain '{}' (Values: {}).\n".format(toolchain_name, _available_toolchain_names(manifest)))

    repository_ctx.download_and_extract(
        url = toolchain["urls"],
        sha256 = toolchain["sha256"],
    )

rbe_preconfig = repository_rule(
    implementation = _rbe_preconfig_impl,
    attrs = {
        "toolchain": attr.string(
            mandatory = True,
        ),
    },
)
