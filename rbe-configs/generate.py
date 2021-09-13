#!/usr/bin/env python3

import subprocess
import os
from os import path
import json
import argparse


def load_json(file: str):
  with open(file, 'r') as f:
    return json.load(f)


def get_output_dir(output_root: str, bazel_version: str,
                   toolchain_name: str) -> str:
  return '{}/{}/{}'.format(output_root, bazel_version, toolchain_name)


def get_upload_dir(upload_root: str, bazel_version: str, toolchain_name: str,
                   tarbal_sha256: str):
  return '{}/{}/{}/{}'.format(upload_root, bazel_version, toolchain_name,
                              tarbal_sha256)


def get_output_tarball(output_dir: str) -> str:
  return '{}/rbe_default.tar'.format(output_dir)


def get_output_manifest(output_dir: str) -> str:
  return '{}/manifest.json'.format(output_dir)


def generate_configs(output_root: str, bazel_version: str, toolchain_name: str,
                     cpp_env_json: str):
  output_dir = get_output_dir(output_root, bazel_version, toolchain_name)
  output_tarball = get_output_tarball(output_dir)
  output_manifest = get_output_manifest(output_dir)

  if path.exists(output_tarball) and path.exists(output_manifest):
    return

  os.makedirs(output_dir, exist_ok=True)

  toolchain_container = 'gcr.io/bazel-public/{}:latest'.format(toolchain_name)
  exec_constrants = [
      '@bazel_tools//platforms:linux', '@bazel_tools//platforms:x86_64',
      '@bazel_tools//tools/cpp:gcc'
  ]
  subprocess.run(
      [
          'rbe_configs_gen',
          '--bazel_version={}'.format(bazel_version),
          '--toolchain_container={}'.format(toolchain_container),
          '--cpp_env_json={}'.format(cpp_env_json),
          '--exec_constrants={}'.format(','.join(exec_constrants)),
          '--output_tarball={}'.format(output_tarball),
          '--output_manifest={}'.format(output_manifest),
          '--exec_os=linux',
          '--target_os=linux',
      ],
      check=True,
  )


def generate_manifest(output_root: str, manifest: list[dict]):
  os.makedirs(output_root, exist_ok=True)

  with open('{}/manifest.json'.format(output_root), 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)


def upload_manifest(output_root: str, upload_root: str):
  subprocess.run(
      [
          'gsutil',
          'cp',
          '{}/manifest.json'.format(output_root),
          '{}/manifest.json'.format(upload_root),
      ],
      check=True,
  )


def upload_configs(output_root: str, upload_root: str, bazel_version: str,
                   toolchain_name: str, tarball_sha256: str):
  output_dir = get_output_dir(output_root, bazel_version, toolchain_name)
  upload_dir = get_upload_dir(upload_root, bazel_version, toolchain_name,
                              tarball_sha256)

  subprocess.run(
      [
          'gsutil',
          'cp',
          get_output_tarball(output_dir),
          get_output_tarball(upload_dir),
      ],
      check=True,
  )

  subprocess.run(
      [
          'gsutil',
          'cp',
          get_output_manifest(output_dir),
          get_output_manifest(upload_dir),
      ],
      check=True,
  )


bazel_versions = [
    '4.2.1',
    '4.2.0',
    '4.1.0',
    '4.0.0',
]

containers = [
    {
        'toolchain_name': 'ubuntu1604-bazel-java8',
        'cpp_env_json': 'cpp_env/ubuntu1604.json'
    },
    {
        'toolchain_name': 'ubuntu1604-java8',
        'cpp_env_json': 'cpp_env/ubuntu1604.json'
    },
    {
        'toolchain_name': 'ubuntu1804-bazel-java11',
        'cpp_env_json': 'cpp_env/ubuntu1804.json'
    },
    {
        'toolchain_name': 'ubuntu1804-java11',
        'cpp_env_json': 'cpp_env/ubuntu1804.json'
    },
    {
        'toolchain_name': 'ubuntu2004-bazel-java11',
        'cpp_env_json': 'cpp_env/ubuntu2004.json'
    },
    {
        'toolchain_name': 'ubuntu2004-java11',
        'cpp_env_json': 'cpp_env/ubuntu2004.json'
    },
]


def generate_configs_for_version(output_root: str, bazel_version: str, download_root: str) -> list[dict]:
  toolchains = []
  for container in containers:
    toolchain_name = container['toolchain_name']
    cpp_env_json = container['cpp_env_json']

    generate_configs(output_root, bazel_version, toolchain_name, cpp_env_json)

    tarball_manifest = load_json(
        get_output_manifest(
            get_output_dir(output_root, bazel_version, toolchain_name)))
    tarball_sha256 = tarball_manifest['configs_tarball_digest']
    assert tarball_sha256

    toolchains.append({
        'name': toolchain_name,
        'urls': [
            get_output_tarball(
                  get_upload_dir(download_root, bazel_version, toolchain_name, tarball_sha256))
        ],
        'sha256': tarball_sha256,
        'manifest': tarball_manifest,
    })


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--upload',
      default='',
      action=argparse.BooleanOptionalAction,
      help='upload generated configs to GCP')

  args = parser.parse_args()

  output_root = 'generated'
  upload_root = 'gs://bazel-ci/rbe-configs'
  download_root = 'https://storage.googleapis.com/bazel-ci/rbe-configs'

  manifest = []

  for bazel_version in bazel_versions:
    toolchains = generate_configs_for_version(output_root, bazel_version, download_root)
    if args.upload == 'all' or args.upload == bazel_version:
      for toolchain in toolchains:
        upload_configs(output_root, upload_root, bazel_version, toolchain['name'],
                       toolchain['sha256'])

    manifest.append({'bazel_version': bazel_version, 'toolchains': toolchains})

  generate_manifest(output_root, manifest)
  if args.upload == 'all' or args.upload == 'manifest':
    upload_manifest(output_root, upload_root)


if __name__ == '__main__':
  main()
