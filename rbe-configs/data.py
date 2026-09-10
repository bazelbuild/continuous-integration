configs = [
  {
    "bazel_version": "9.1.0",
    "containers": [
      {
          'toolchain_name': 'ubuntu2404',
          'cpp_env_json': 'cpp_env/ubuntu2404.json'
      },
      {
          'toolchain_name': 'ubuntu2204',
          'cpp_env_json': 'cpp_env/ubuntu2204.json'
      }
    ]
  },
  {
    "bazel_version": "9.0.0",
    "containers": [
      {
          'toolchain_name': 'ubuntu2204',
          'cpp_env_json': 'cpp_env/ubuntu2204.json'
      }
    ]
  },
  {
    "bazel_version": "8.0.1",
    "containers": [
      {
          'toolchain_name': 'ubuntu2204',
          'cpp_env_json': 'cpp_env/ubuntu2204.json'
      }
    ]
  },
  {
    "bazel_version": "7.0.2",
    "containers": [
      {
          'toolchain_name': 'ubuntu2204',
          'cpp_env_json': 'cpp_env/ubuntu2204.json'
      }
    ]
  },
  {
    "bazel_version": "6.3.2",
    "containers": [
      {
          'toolchain_name': 'ubuntu2204-bazel-java17',
          'cpp_env_json': 'cpp_env/ubuntu2204.json'
      },
      {
          'toolchain_name': 'ubuntu2204-java17',
          'cpp_env_json': 'cpp_env/ubuntu2204.json'
      },
    ]
  },
]
