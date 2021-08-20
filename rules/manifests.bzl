manifests = [
    {
        "bazel_version": "4.2.0",
        "toolchains": [
            {
                "name": "ubuntu1604-bazel-java8",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.2.0/ubuntu1604-bazel-java8/c0acac594f0e97fa85298d153b4bca5bd920065bf15d44cdfa25751364539b9c/rbe_default.tar",
                ],
                "sha256": "c0acac594f0e97fa85298d153b4bca5bd920065bf15d44cdfa25751364539b9c",
                "manifest": {
                    "bazel_version": "4.2.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1604-bazel-java8:latest",
                    "image_digest": "b6d867c9d57b3d7555485c8bbb105a24225b584c920c3cb7235c7f470bff39c6",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "c0acac594f0e97fa85298d153b4bca5bd920065bf15d44cdfa25751364539b9c",
                },
            },
            {
                "name": "ubuntu1604-java8",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.2.0/ubuntu1604-java8/4938e4acc3d044f65bbbb044bdf3de3f4e9ffd0f15f1053103ba263fe8d9eb1e/rbe_default.tar",
                ],
                "sha256": "4938e4acc3d044f65bbbb044bdf3de3f4e9ffd0f15f1053103ba263fe8d9eb1e",
                "manifest": {
                    "bazel_version": "4.2.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1604-java8:latest",
                    "image_digest": "d0fb0b8554eaf0e6d043222fdb18fd4ae313f8b13512ed025c0a264cc5036d09",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "4938e4acc3d044f65bbbb044bdf3de3f4e9ffd0f15f1053103ba263fe8d9eb1e",
                },
            },
            {
                "name": "ubuntu1804-bazel-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.2.0/ubuntu1804-bazel-java11/1b4fa45f5ed0e5ba0a52df9df540c7dc16e3fc5b32b7e92f8a6a990a56e2e457/rbe_default.tar",
                ],
                "sha256": "1b4fa45f5ed0e5ba0a52df9df540c7dc16e3fc5b32b7e92f8a6a990a56e2e457",
                "manifest": {
                    "bazel_version": "4.2.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1804-bazel-java11:latest",
                    "image_digest": "dcbd915da732d44da3fd840672277965833e6f277690f31c87fb3c7037adb42a",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "1b4fa45f5ed0e5ba0a52df9df540c7dc16e3fc5b32b7e92f8a6a990a56e2e457",
                },
            },
            {
                "name": "ubuntu1804-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.2.0/ubuntu1804-java11/cfaf279b5d04ccca4a6f0117f4739d19a33fcbd1a08bef11c31dba7321f31884/rbe_default.tar",
                ],
                "sha256": "cfaf279b5d04ccca4a6f0117f4739d19a33fcbd1a08bef11c31dba7321f31884",
                "manifest": {
                    "bazel_version": "4.2.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1804-java11:latest",
                    "image_digest": "bba52f148c0eb5f34e2a74ffdad53adfe842008814db3202189288970eca7ccf",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "cfaf279b5d04ccca4a6f0117f4739d19a33fcbd1a08bef11c31dba7321f31884",
                },
            },
            {
                "name": "ubuntu2004-bazel-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.2.0/ubuntu2004-bazel-java11/559dc00e65f7f53f78c1b21725c82a056f54a72255c8f65915441556f91be90c/rbe_default.tar",
                ],
                "sha256": "559dc00e65f7f53f78c1b21725c82a056f54a72255c8f65915441556f91be90c",
                "manifest": {
                    "bazel_version": "4.2.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu2004-bazel-java11:latest",
                    "image_digest": "bde5a6680736d167198ddb7f703e325454f45bdc93480572d7e5aded7905f110",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "559dc00e65f7f53f78c1b21725c82a056f54a72255c8f65915441556f91be90c",
                },
            },
            {
                "name": "ubuntu2004-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.2.0/ubuntu2004-java11/7ac9a2c7b5bc78a240a66d68f11ef6347ec7be52dd5b2ee020b0642b1a20b095/rbe_default.tar",
                ],
                "sha256": "7ac9a2c7b5bc78a240a66d68f11ef6347ec7be52dd5b2ee020b0642b1a20b095",
                "manifest": {
                    "bazel_version": "4.2.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu2004-java11:latest",
                    "image_digest": "d6aa610036544f299998cae445bbb385b0f35bc9fa7d20e5cfdb1dcdb3ee5f60",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "7ac9a2c7b5bc78a240a66d68f11ef6347ec7be52dd5b2ee020b0642b1a20b095",
                },
            },
        ],
    },
    {
        "bazel_version": "4.1.0",
        "toolchains": [
            {
                "name": "ubuntu1604-bazel-java8",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.1.0/ubuntu1604-bazel-java8/c0acac594f0e97fa85298d153b4bca5bd920065bf15d44cdfa25751364539b9c/rbe_default.tar",
                ],
                "sha256": "c0acac594f0e97fa85298d153b4bca5bd920065bf15d44cdfa25751364539b9c",
                "manifest": {
                    "bazel_version": "4.1.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1604-bazel-java8:latest",
                    "image_digest": "b6d867c9d57b3d7555485c8bbb105a24225b584c920c3cb7235c7f470bff39c6",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "c0acac594f0e97fa85298d153b4bca5bd920065bf15d44cdfa25751364539b9c",
                },
            },
            {
                "name": "ubuntu1604-java8",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.1.0/ubuntu1604-java8/4938e4acc3d044f65bbbb044bdf3de3f4e9ffd0f15f1053103ba263fe8d9eb1e/rbe_default.tar",
                ],
                "sha256": "4938e4acc3d044f65bbbb044bdf3de3f4e9ffd0f15f1053103ba263fe8d9eb1e",
                "manifest": {
                    "bazel_version": "4.1.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1604-java8:latest",
                    "image_digest": "d0fb0b8554eaf0e6d043222fdb18fd4ae313f8b13512ed025c0a264cc5036d09",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "4938e4acc3d044f65bbbb044bdf3de3f4e9ffd0f15f1053103ba263fe8d9eb1e",
                },
            },
            {
                "name": "ubuntu1804-bazel-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.1.0/ubuntu1804-bazel-java11/1b4fa45f5ed0e5ba0a52df9df540c7dc16e3fc5b32b7e92f8a6a990a56e2e457/rbe_default.tar",
                ],
                "sha256": "1b4fa45f5ed0e5ba0a52df9df540c7dc16e3fc5b32b7e92f8a6a990a56e2e457",
                "manifest": {
                    "bazel_version": "4.1.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1804-bazel-java11:latest",
                    "image_digest": "dcbd915da732d44da3fd840672277965833e6f277690f31c87fb3c7037adb42a",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "1b4fa45f5ed0e5ba0a52df9df540c7dc16e3fc5b32b7e92f8a6a990a56e2e457",
                },
            },
            {
                "name": "ubuntu1804-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.1.0/ubuntu1804-java11/cfaf279b5d04ccca4a6f0117f4739d19a33fcbd1a08bef11c31dba7321f31884/rbe_default.tar",
                ],
                "sha256": "cfaf279b5d04ccca4a6f0117f4739d19a33fcbd1a08bef11c31dba7321f31884",
                "manifest": {
                    "bazel_version": "4.1.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1804-java11:latest",
                    "image_digest": "bba52f148c0eb5f34e2a74ffdad53adfe842008814db3202189288970eca7ccf",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "cfaf279b5d04ccca4a6f0117f4739d19a33fcbd1a08bef11c31dba7321f31884",
                },
            },
            {
                "name": "ubuntu2004-bazel-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.1.0/ubuntu2004-bazel-java11/559dc00e65f7f53f78c1b21725c82a056f54a72255c8f65915441556f91be90c/rbe_default.tar",
                ],
                "sha256": "559dc00e65f7f53f78c1b21725c82a056f54a72255c8f65915441556f91be90c",
                "manifest": {
                    "bazel_version": "4.1.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu2004-bazel-java11:latest",
                    "image_digest": "bde5a6680736d167198ddb7f703e325454f45bdc93480572d7e5aded7905f110",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "559dc00e65f7f53f78c1b21725c82a056f54a72255c8f65915441556f91be90c",
                },
            },
            {
                "name": "ubuntu2004-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.1.0/ubuntu2004-java11/7ac9a2c7b5bc78a240a66d68f11ef6347ec7be52dd5b2ee020b0642b1a20b095/rbe_default.tar",
                ],
                "sha256": "7ac9a2c7b5bc78a240a66d68f11ef6347ec7be52dd5b2ee020b0642b1a20b095",
                "manifest": {
                    "bazel_version": "4.1.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu2004-java11:latest",
                    "image_digest": "d6aa610036544f299998cae445bbb385b0f35bc9fa7d20e5cfdb1dcdb3ee5f60",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "7ac9a2c7b5bc78a240a66d68f11ef6347ec7be52dd5b2ee020b0642b1a20b095",
                },
            },
        ],
    },
    {
        "bazel_version": "4.0.0",
        "toolchains": [
            {
                "name": "ubuntu1604-bazel-java8",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.0.0/ubuntu1604-bazel-java8/c0acac594f0e97fa85298d153b4bca5bd920065bf15d44cdfa25751364539b9c/rbe_default.tar",
                ],
                "sha256": "c0acac594f0e97fa85298d153b4bca5bd920065bf15d44cdfa25751364539b9c",
                "manifest": {
                    "bazel_version": "4.0.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1604-bazel-java8:latest",
                    "image_digest": "b6d867c9d57b3d7555485c8bbb105a24225b584c920c3cb7235c7f470bff39c6",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "c0acac594f0e97fa85298d153b4bca5bd920065bf15d44cdfa25751364539b9c",
                },
            },
            {
                "name": "ubuntu1604-java8",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.0.0/ubuntu1604-java8/4938e4acc3d044f65bbbb044bdf3de3f4e9ffd0f15f1053103ba263fe8d9eb1e/rbe_default.tar",
                ],
                "sha256": "4938e4acc3d044f65bbbb044bdf3de3f4e9ffd0f15f1053103ba263fe8d9eb1e",
                "manifest": {
                    "bazel_version": "4.0.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1604-java8:latest",
                    "image_digest": "d0fb0b8554eaf0e6d043222fdb18fd4ae313f8b13512ed025c0a264cc5036d09",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "4938e4acc3d044f65bbbb044bdf3de3f4e9ffd0f15f1053103ba263fe8d9eb1e",
                },
            },
            {
                "name": "ubuntu1804-bazel-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.0.0/ubuntu1804-bazel-java11/1b4fa45f5ed0e5ba0a52df9df540c7dc16e3fc5b32b7e92f8a6a990a56e2e457/rbe_default.tar",
                ],
                "sha256": "1b4fa45f5ed0e5ba0a52df9df540c7dc16e3fc5b32b7e92f8a6a990a56e2e457",
                "manifest": {
                    "bazel_version": "4.0.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1804-bazel-java11:latest",
                    "image_digest": "dcbd915da732d44da3fd840672277965833e6f277690f31c87fb3c7037adb42a",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "1b4fa45f5ed0e5ba0a52df9df540c7dc16e3fc5b32b7e92f8a6a990a56e2e457",
                },
            },
            {
                "name": "ubuntu1804-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.0.0/ubuntu1804-java11/cfaf279b5d04ccca4a6f0117f4739d19a33fcbd1a08bef11c31dba7321f31884/rbe_default.tar",
                ],
                "sha256": "cfaf279b5d04ccca4a6f0117f4739d19a33fcbd1a08bef11c31dba7321f31884",
                "manifest": {
                    "bazel_version": "4.0.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu1804-java11:latest",
                    "image_digest": "bba52f148c0eb5f34e2a74ffdad53adfe842008814db3202189288970eca7ccf",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "cfaf279b5d04ccca4a6f0117f4739d19a33fcbd1a08bef11c31dba7321f31884",
                },
            },
            {
                "name": "ubuntu2004-bazel-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.0.0/ubuntu2004-bazel-java11/559dc00e65f7f53f78c1b21725c82a056f54a72255c8f65915441556f91be90c/rbe_default.tar",
                ],
                "sha256": "559dc00e65f7f53f78c1b21725c82a056f54a72255c8f65915441556f91be90c",
                "manifest": {
                    "bazel_version": "4.0.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu2004-bazel-java11:latest",
                    "image_digest": "bde5a6680736d167198ddb7f703e325454f45bdc93480572d7e5aded7905f110",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "559dc00e65f7f53f78c1b21725c82a056f54a72255c8f65915441556f91be90c",
                },
            },
            {
                "name": "ubuntu2004-java11",
                "urls": [
                    "https://storage.googleapis.com/bazel-ci/rbe-configs/4.0.0/ubuntu2004-java11/7ac9a2c7b5bc78a240a66d68f11ef6347ec7be52dd5b2ee020b0642b1a20b095/rbe_default.tar",
                ],
                "sha256": "7ac9a2c7b5bc78a240a66d68f11ef6347ec7be52dd5b2ee020b0642b1a20b095",
                "manifest": {
                    "bazel_version": "4.0.0",
                    "toolchain_container": "gcr.io/bazel-public/ubuntu2004-java11:latest",
                    "image_digest": "d6aa610036544f299998cae445bbb385b0f35bc9fa7d20e5cfdb1dcdb3ee5f60",
                    "exec_os": "Linux",
                    "configs_tarball_digest": "7ac9a2c7b5bc78a240a66d68f11ef6347ec7be52dd5b2ee020b0642b1a20b095",
                },
            },
        ],
    },
]
