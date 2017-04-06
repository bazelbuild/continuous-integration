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
        "2.1.1",
        "cc93174abe2f28f8c3f0e572d718129dffe4e45685bcb82cf99c4ebce756dbe9",
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
        "1.20",
        "e78b7bb32957d11dcf58e57f2d7b60903bf31ace7858d19febb3b11a374a1187",
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
        "1.9",
        "a2c675486ad3c474478d92138fd30b50d74d94e7855e63b130ff88b61e728287",
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
        "2.4.1",
        "a1d608b739f221b4f7ca6810fba078eb2e06a6d82683820de337c829f7c8e763",
    ],
    "github": [
        "1.26.2",
        "25feed9d0d4e8120c4d7dd7921e3227fd9ef66f94614c0f74ee5e923e3b82759",
    ],
    "maven-plugin": [
        "2.15.1",
        "61aeb7d787e312702b438c75ffd752394bbcaaf2b6d212a4fc169b3f28651c6e",
    ],
    "git": [
        "3.2.0",
        "3784ff5bc38c93d8b55935507900c1f6b7205ab14195c21440c6a80a3307abdf",
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
        "2.57.1",
        "4d3cd61bcd040a8a36c39aea429dcbaf3b600122c9a319e083f3ab5f61b53cdd",
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
        "2.14",
        "49bf65953ad684e5d4f0f0750dce6f5efed9e67f5d0de26da405945bbd46f01d",
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
        "1.16",
        "6641040f192518cf4033d462cabddd2faa68afbcaebcf8e68c0e2b952c49fd36",
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
    "pipeline-stage-step": [
        "2.2",
        "08f077bc8cd98fbf6cb7383d8bcfe3db69796f89cedcfb6f13c8c9375b2a11c8",
    ],
    "pipeline-stage-view": [
        "2.6",
        "e4b82a523fe8151a117c150073c8a0cad65277651ed6565150b6b058111d4c98",
    ],
    "handlebars": [
        "1.1.1",
        "bc5cc7b3eca17ba6cec0a8def94f3aa78ad7a19387a19aa3a56f857a18966afa",
    ],
    "pipeline-rest-api": [
        "2.6",
        "4ecc8c111f86902a86860943390e1b98463437a33116df4feb888226daf42aaa",
    ],
    "momentjs": [
        "1.1.1",
        "ca3c2d264cff55f71e900dc7de1f13c0bfbffdb9b3419b854dce175bcb8a4848",
    ],
    "workflow-durable-task-step": [
        "2.10",
        "5a676c894d4deb5b9163d2f34cecfe187130710a6158f5721179b8a4cb5ae250",
    ],
    "durable-task": [
        "1.13",
        "e242f459b6662b84f3ab99f51cdbdb048d7a2bb1f1a27ffafb5f0c4bd6d5735c",
    ],
    "pipeline-graph-analysis": [
        "1.3",
        "bb3235a0b5a62cd7be3983bfd40a202c582757c9633d23858aaa38af88ee61ea",
    ],
    "pipeline-input-step": [
        "2.5",
        "ff62f1b3b48d2a660de55379f565be0948559fd722ff0345d0fb47bf81e537e3",
    ],
    "ansicolor": [
        "0.5.0",
        "4fd5b38959812712b62576ce98d0302f799bd950f5a6f777a8c0d862df336526",
    ],
    "workflow-cps-global-lib": [
        "2.7",
        "bfd2ed77b12dc15f50eed4d0a4cdd8126890697ba947048dc43f29b36cf8592e",
    ],
    "cloudbees-folder": [
        "6.0.3",
        "f8697c7e28a25501458115ed49f0146c7e40c4b0c342a0299593ac03f036ca6c",
    ],
    "git-server": [
        "1.7",
        "1a5dc733495681a6d1a6adce07e614e50f4e5d22580e6fafbd5ca260aa4367fc",
    ],
    "pipeline-build-step": [
        "2.5",
        "1df734b64a3297ec134f484546c3dbcec3e227e806502ee827d023c395b7e07a",
    ],
    # Blue ocean plugins (Jenkins new UI)
    "credentials-binding": [
        "1.11",
        "c86eb57fc390c2f82c17e53fe7fe4c9576fac6514af88906a117f6dfbf3c6256",
    ],
    "docker-workflow": [
        "1.10",
        "72669ece071e808edbd21d18f1021c8830ba7591d7b18e63af5b67148d35bc02",
    ],
    "pubsub-light": [
        "1.7",
        "d22edc047d476c15603126cf811a1566e237a7fe565eaca192a469795f50d5c5",
    ],
    "workflow-multibranch": [
        "2.14",
        "823986f18fc02508d9edae9c9876d0fa08e0b4f4b785707e224eab01bda9f018",
    ],
    "blueocean-web": [
        "1.0.0",
        "4c52d43c88f66a371c884f3e36c5b1c4507f19481f26bca7911e6d8ffe851103",
    ],
    "blueocean-autofavorite": [
        "0.6",
        "0a52677edb4d6bf3de5808f98c0159db11812854662fa35a041c78d23664e03d",
    ],
    "blueocean-dashboard": [
        "1.0.0",
        "31379171594214692c1fdf10462383bd10762da624fee71f045ed362ab49353c",
    ],
    "branch-api": [
        "2.0.8",
        "eb794fac3846f64840abf6bae0ed163c2c17a6a5fad13cbd4dd450744d79ee0d",
    ],
    "blueocean-commons": [
        "1.0.0",
        "ac4ac5a94b17efa752d2e39209c28ae337c7be7df15f1a2dc18921be4313f938",
    ],
    "pipeline-model-api": [
        "1.1.2",
        "05f9ddcc19123f62f4aef0f004a5d544c6341f149ea3b34e21b794c9a9327d39",
    ],
    "pipeline-model-definition": [
        "1.1.1",
        "46c1e15b14256a3c7f38e4327fd60c2a3e54182d21f0416e5687cfe5fbe5edec",
    ],
    "blueocean": [
        "1.0.0",
        "339e78362f8143f9fc76852ef2d9c2d97f8376ca06568d1dd49771709d97c63f",
    ],
    "variant": [
        "1.1",
        "971893fb05da213631b8ea977a32a5d4953f1cb7ab6fbdec9020d503550275ff",
    ],
    "blueocean-rest": [
        "1.0.0",
        "7432a080de3a63c40b0904ee71c2b3c8f58574438aee8a3f0a7fd996e5d721d4",
    ],
    "favorite": [
        "2.0.4",
        "d3c8fd1a13277316010b68f602181d78be32b89f2a8cbf4ab079d4a2f7832418",
    ],
    "blueocean-display-url": [
        "1.5.1",
        "85ebd9fccd1c13d532fd93087826bf992ff881fe325282b2d68db4a69f3ce29d",
    ],
    "blueocean-personalization": [
        "1.0.0",
        "b5df9d9c82d8a5fca1c93785fc8c705ae08daf77f6fc6c9d04a99e9e0bb872f7",
    ],
    "blueocean-pipeline-api-impl": [
        "1.0.0",
        "cf860a117c683c4d0da4d423498ba0a9f6ad957195bda0db4720896fd6c85c6d",
    ],
    "blueocean-jwt": [
        "1.0.0",
        "90e7d4899328ee4ae30f8dac0ce56f3e1945135e25f5135759601e3f1e64d236",
    ],
    "blueocean-events": [
        "1.0.0",
        "b4d880001fed2a0c2a183102670c1bdfa00fa292f5ae4c2837d1e57f556c8030",
    ],
    "github-branch-source": [
        "2.0.4",
        "828b1a04106cf5194be73d13edeb155a0a1f625ed0b42fead34af6be7b456bcd",
    ],
    "blueocean-i18n": [
        "1.0.0",
        "e423624adbf70fed06ccf15a1435a3c0c521064128e4bc5b77c6a55d3774386a",
    ],
    "blueocean-config": [
        "1.0.0",
        "f57058d91b8ab0909fcf2494cdb5bf0d6ac1c5737fecb4c5fd35c3a346f2a0d6",
    ],
    "blueocean-git-pipeline": [
        "1.0.0",
        "e2d177bf3f63bee248f76c0d243405ff37010213ba1ab462b2977295a94117de",
    ],
    "pipeline-stage-tags-metadata": [
        "1.1.2",
        "bea00844cbebdb0c7d12b074369c69b20b4eac36330a968b96676b9afae30282",
    ],
    "blueocean-pipeline-editor": [
        "0.2.0",
        "cd3d0a7aeee37aa8df6135dc575a4d0458dc63f206f61034f57a79a58be83c64",
    ],
    "sse-gateway": [
        "1.15",
        "56b19b7a48f646dc8269bae4aca41ec11f71756d618d302b1f8b9d688441850f",
    ],
    "blueocean-github-pipeline": [
        "1.0.0",
        "1e6490d3e06e6fcdbe11c30ed9464c17820cf1ec571576ecb7245820ee8f4cf9",
    ],
    "jackson2-api": [
        "2.7.3",
        "6dfa1ba3db32ae47630b239399c3fc8d9102ff0b523a5c33dd32bc88d9874837",
    ],
    "pipeline-model-extensions": [
        "1.1.1",
        "a4daea2176299ba5d36556e5a308ec46c1a6d240088272b36ef1185d5fec53fa",
    ],
    "metrics": [
        "3.1.2.9",
        "0828fe8dbd36d7f614ddc89cd2940f4004ee49cd9dca86c48cc1fd2f4495a542",
    ],
    "pipeline-model-declarative-agent": [
        "1.1.1",
        "d5540c3973bf5f568910f93b3a002c413148b9d3dd4211ce5faf4a2a1214d4ef",
    ],
    "blueocean-rest-impl": [
        "1.0.0",
        "2d230acad399eb9d750e7142eb9687c58d74393011e3c778b7511ebb8e217937",
    ],
    "docker-commons": [
        "1.6",
        "6aba36f54e88b7b5debfef7cf7e98c913a4b90da0713c80a8a6f5a90e9edff8b",
    ],
    "authentication-tokens": [
        "1.3",
        "f05736bc7da0df3bba5ceb4d893089706812ced3134adb2edc9ae341467f1ae3",
    ],
}
