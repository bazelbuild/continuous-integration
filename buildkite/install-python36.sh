#!/bin/bash
#
# Copyright 2017 The Bazel Authors. All rights reserved.
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

apt-get -qqy install zlib1g-dev libssl-dev

PYTHON_VERSION="3.6.5"

mkdir -p /usr/local/src
pushd /usr/local/src

curl -O "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz"
tar xfJ "Python-${PYTHON_VERSION}.tar.xz"
rm -f "Python-${PYTHON_VERSION}.tar.xz"
cd "Python-${PYTHON_VERSION}"

# Enable the 'ssl' module.
cat >> Modules/Setup.dist <<'EOF'
_ssl _ssl.c \
       -DUSE_SSL -I/usr/include -I/usr/include/openssl \
       -L/usr/lib -lssl -lcrypto
EOF

echo "Compiling Python ${PYTHON_VERSION} ..."
./configure --quiet --enable-ipv6
make -s -j8 all > /dev/null
echo "Installing Python ${PYTHON_VERSION} ..."
make -s altinstall > /dev/null

pip3.6 install requests uritemplate pyyaml github3.py

popd
rm -rf "/usr/local/src/Python-${PYTHON_VERSION}"
