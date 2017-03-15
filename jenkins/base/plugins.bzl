# Copyright 2015 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Plugins for Jenkins
JENKINS_PLUGINS = {
    "conditional-buildstep": [
        "1.3.5",
        "bb505823eef199eef3b67bff5d7826d075329ce93c64784ae72d22fff88110d9",
    ],
    "javadoc": [
        "1.4",
        "2236e563d057a98b1bb2e56975756a008986289aa01a61c4655a31b62c760a22",
    ],
    "scm-api": [
        "2.1.0",
        "cbabbab916a631112157161b3e4858baf928b6a507963166193d923a5065c7d2",
    ],
    "ssh-credentials": [
        "1.13",
        "d4f979223cc543dfd9bf72a1177471bb08748d2c79e1115d7bb12198bbbf2010",
    ],
    "parameterized-trigger": [
        "2.33",
        "7fcba38e47b556ae9f34e5a8051ce935df7dd37ca12d871d18676292a27fb6bf",
    ],
    "copyartifact": [
        "1.38.1",
        "0171f402f064615a14b0adca348c2d49ee338cd49d54539793105a191d941501",
    ],
    "mailer": [
        "1.19",
        "24d99cc0f9ec2f1954604cacc8d7d1d4ffbfc9d4610d9fcc559e1ce83945e74d",
    ],
    "run-condition": [
        "1.0",
        "4e55ebf4bde1202784404d856f98f7de85470ed145cde06feb45f641891780fb",
    ],
    "script-security": [
        "1.27",
        "7f9def9f7347d0a0bf5ab8899ff2365b19d3b6a34a711adbc51a088f75eb587e",
    ],
    "matrix-project": [
        "1.8",
        "47fc1ffaa6516508b9415b23f2ef27ef8899e3511a7934fa1956a6a0f1e59bf0",
    ],
    "junit": [
        "1.20",
        "be0c9079c1ed7e3bc9d7157e30d0e8fdd733a83cba11ab184ddb48cea1a579c3",
    ],
    "credentials": [
        "2.1.13",
        "e793895fb727b59d83a9e395984243cfee9abdf4d56238fb6f2594948b0487e5",
        "pinned",
    ],
    "git-parameter": [
        "0.8.0",
        "c7251742e90110a0c6345a47373a20f8d97e0562bf543f04e6d2e7c9313e6ef1",
    ],
    "github-api": [
        "1.85",
        "e340c7d2719cd7569fd039c940df87154750a291918bcb982462575b775275b7",
    ],
    "git-client": [
        "2.3.0",
        "6a39048745815c6ed8e04fbbe26978d8457d77529b4448bf02cf357ae39d0af0",
    ],
    "github": [
        "1.26.1",
        "a2930570df3a30601c1d201eac2ae9a622a1b6dda03d740ee4a3bcfdfc4885c8",
    ],
    "maven-plugin": [
        "2.15.1",
        "61aeb7d787e312702b438c75ffd752394bbcaaf2b6d212a4fc169b3f28651c6e",
    ],
    "git": [
        "3.1.0",
        "7ee0473a61a39c250dfc1acab15462cc6a4f936c39a0456a0352df9c622f3fe4",
    ],
    "token-macro": [
        "2.0",
        "9e0909ec9a37d0de9311f507cc24634edf5f7f191dc7643d19ba835bdfaa1454",
    ],
    "nodelabelparameter": [
        "1.7.2",
        "0f556ae48573db6bae28b24eae561121ed9931e8b1bc31ac4e586bc8d3238edf",
    ],
    "jquery": [
        "1.11.2-0",
        "acf4940bd5a0d918d781b51a6f42f7a0cb9381ede8235582c629a5d347495029",
    ],
    "email-ext": [
        "2.57",
        "aee1e1a1d4e842a6e4827f97f71dfff307a3e97af0fc8f4c481415e8d11487be",
    ],
    "google-login": [
        "1.3",
        "4b1482347ddd0a2a54c1fdedfe46a519cc2ada60dfc774d2435f554287c52d25",
    ],
    "fail-the-build-plugin": [
        "1.0",
        "c97db02dc6fef269780b77d2001a9bfb49bcdc9ac2ee242cd10445709bb7d09e",
    ],
    "scoring-load-balancer": [
        "1.0.1",
        "a7229d2945e347afb472d3c45e83ea3c4409c8710c4168912601eb46684dd3a3",
    ],
    "greenballs": [
        "1.15",
        "6c3722fb9ce2a446f0266e1911d87ef50898a10f38890bb6963e7e1e1c4296fb",
    ],
    "plain-credentials": [
        "1.4",
        "4f1834f99ffd7f2a7db1972fe46ee42d06af819b27297193ac89eb33a14292d8",
    ],
    "ssh-agent": [
        "1.14",
        "08f67bcdbc7a1f1205376c508c1e5ed8b92f0834770352d2060252d6899102b7",
    ],
    "workflow-step-api": [
        "2.9",
        "c28cc0ecd0f707980c941b7b0c27cb55894b8caa5320e0bf7beebe10a0ae067b",
    ],
    "icon-shim": [
        "2.0.3",
        "8ab2f1617b68561a7f0254fb27578840aa9b7e158d0bd8c51628dbc64e8ab0ca",
    ],
    "ghprb": [
        "1.35.0",
        "e33212e46f9af4c02379ae6c8c37bf4df74f594da1597ec611921f5099c1e9d2",
    ],
    "build-flow-plugin": [
        "0.20",
        "7ce4746b7d59e543da340c98f3eaf0f559581d2fdd7f39d787152f45554a2966",
    ],
    "embeddable-build-status": [
        "1.9",
        "9d950ce4bfdcb67e1b1198ea2b54e18de95ec3214b1cf1135141b5b54a62edb2",
    ],
    "build-timeout": [
        "1.18",
        "6ea3eaa31d13314af1bcd7576fb07ee4a007c84ae56639eabc03e503de485dba",
    ],
    "build-monitor-plugin": [
        "1.11+build.201701152243",
        "4e8d5e0a00410f06e07a05cf1011563df7cd169e1961d3f334fc159a55b6a29b",
    ],
    "ace-editor": [
        "1.1",
        "abc97028893c8a71581a5f559ea48e8e1f1a65164faee96dabfed9e95e9abad2",
    ],
    "display-url-api": [
        "1.1.1",
        "d9c3266898caa82965bb08242da91cbc75bebe724744686d48ec676b511e5765",
    ],
    "jquery-detached": [
        "1.2.1",
        "a05273cd20c11557ffcb7dcb75150f21d35dc8be28355548b831c2960d7f11c0",
    ],
    "sauce-ondemand": [
        "1.161",
        "40f3ed7ce6eaf1ff3e1e3ecf2e6b8392bb3996abc708ba5db7eb7163d125cad1",
    ],
    "structs": [
        "1.6",
        "faad3252e325e9a672b3e2732711b4a673997ac3d35a501a43ccb47ae9536ca8",
    ],
    "workflow-api": [
        "2.12",
        "d83e61b9189ee0de6bb4c394cd07cd830e9cc7876205cd7d03d6b2a601cc0271",
    ],
    "workflow-basic-steps": [
        "2.4",
        "c57d5308a01df1990a7f491ddb6dfc7aab5b7b713ad9cfc458cbef76d27fdbab",
    ],
    "workflow-cps": [
        "2.29",
        "f511afb06bba24ee9a4521703e2c8a638a2f1525f7f2772bb13cf5daad43dbe7",
    ],
    "workflow-job": [
        "2.10",
        "fd5d5a68270fae99a4514eac6cc2b58ebc37673f5e535f778286a4d36d94405a",
    ],
    "workflow-scm-step": [
        "2.4",
        "69d58ceb58111663e82928c8db367ba8e857c29aaee9c4264aeb4100fc459e22",
    ],
    "workflow-support": [
        "2.13",
        "7e1d547757b8dedc824f3595701c88d06204e07565f99d488cb5a110421fb7e9",
    ],
    "ldap": [
        "1.14",
        "f424cbcb06e29879d58bf21bea365e4f9b055aae9e9ddd1b5f61dcb140128dcb",
    ],
    "matrix-auth": [
        "1.4",
        "366aa6c4c50b256cb38d5e5c30195d79d634b56cca24d3db190aa5bc01142408",
    ],
    "antisamy-markup-formatter": [
        "1.5",
        "8e8e3e917d76b0432ab3c32a000e824f4ef32011ba5e77dd8b6b476310df8f1a",
    ],
    "pam-auth": [
        "1.3",
        "1b1d32dca618f43f6c06786f3fde6cc0e0fa0c805cbb735fafd464cf2cfcf1e3",
    ],
    "ssh-slaves": [
        "1.13",
        "e860c90540bfa667cf215d90bfb1a607ba4fb0af7be039b3fdcfcd33cb71d777",
    ],
    "subversion": [
        "2.7.2",
        "ff56a46ccca9b89ab907f1da7ef5b0ea46106eba918678cd53101d2896a961ea",
    ],
    "windows-slaves": [
        "1.3.1",
        "4364f88286745a48962b86b53df3739a6978886e72ec83289a3cfc750f1adcc6",
    ],
    "translation": [
        "1.15",
        "11a0dd4aaa66d506d1bfc32d367e9c1f28b957296b5729ae9bf0947f5f1301ce",
    ],
    "bouncycastle-api": [
        "2.16.0",
        "8aed85e3d479da76406eedf609696e3b4393afb4ba8f060656b311388a1e5e20",
    ],
    "mapdb-api": [
        "1.0.9.0",
        "072c11a34cf21f87f9c44bf01b430c5ea77e8096d077e8533de654ef00f3f871",
    ],
}
