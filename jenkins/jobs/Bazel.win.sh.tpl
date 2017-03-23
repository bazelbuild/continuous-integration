# Copyright 2016 The Bazel Authors. All rights reserved.
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

# Shell script to set-up the environment on Windows to call the bootstrap
# inside MSYS.

set -eux

# We have to strip the environment or the windows env will override the 
# Bazel latest to bootstrap bazel
echo 'export BOOTSTRAP_BAZEL="/c/bazel_ci/installs/latest/bazel.exe"' >env.sh

# Pass PLATFORM_NAME to Windows bootstrap script for building a MSVC Bazel
echo "export PLATFORM_NAME=\"${PLATFORM_NAME}\"" >>env.sh

# Various set-up for the slave
echo 'export TMPDIR="${TMPDIR:-/c/bazel_ci/temp}"' >>env.sh
echo 'mkdir -p "${TMPDIR}"' >>env.sh
echo 'export PATH="$PATH:/c/python_27_amd64/files"' >>env.sh

# Get java home
echo "export JAVA_HOME='$(dirname "$(dirname "$(which java)")")'" >>env.sh

# Jenkins is capable of executing shell scripts directly, even on Windows,
# but it uses a shell binary bundled with it and not the msys one. We don't
# want to use two different shells, so a batch file is used instead to call
# the msys shell.
/c/tools/msys64/usr/bin/bash -l -c "cd $PWD; source env.sh; exec ./scripts/ci/windows/compile_windows.sh"
