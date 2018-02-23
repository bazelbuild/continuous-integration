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

# add-apt-repository -y "ppa:deadsnakes/ppa"
# apt-get -qqy update > /dev/null
# apt-get -qqy install python3.6 python3.6-dev python3.6-venv > /dev/null
# python3.6 -m ensurepip
# rm -f /usr/local/bin/pip3
# apt-get -qqy install python3-pip
# pip3.6 install requests pyyaml
# pip3.6 install --pre github3.py

apt-get -qqy install zlib1g-dev libssl-dev

PYTHON_VERSION="3.6.4"

mkdir -p /usr/local/src
pushd /usr/local/src

curl -O "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz"
tar xvfJ "Python-${PYTHON_VERSION}.tar.xz"
rm -f "Python-${PYTHON_VERSION}.tar.xz"
cd "Python-${PYTHON_VERSION}"

# Enable the 'ssl' module.
cat >> Modules/Setup.dist <<'EOF'
_ssl _ssl.c \
       -DUSE_SSL -I/usr/include -I/usr/include/openssl \
       -L/usr/lib -lssl -lcrypto
EOF

echo "Compiling Python ${PYTHON_VERSION} ..."
./configure --enable-ipv6
make -s -j8 all > /dev/null
echo "Installing Python ${PYTHON_VERSION} ..."
make -s altinstall > /dev/null

pip3.6 install requests uritemplate pyyaml
pip3.6 install --pre github3.py

popd
rm -rf "/usr/local/src/Python-${PYTHON_VERSION}"
