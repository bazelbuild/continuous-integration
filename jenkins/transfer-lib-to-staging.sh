#!/bin/bash
# Copyright (C) 2017 The Bazel Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# A simple wrapper around transfer-lib to execute it on the staging server
# just run it and it should transfer the lib to jenkins staging.

: "${JENKINS_SERVER:=jenkins-staging}"
: "${JENKINS_ZONE:=europe-west1-d}"
: "${IMAGE_NAME:=gcr.io/bazel-public/jenkins-master-staging}"

cd "$(dirname "$0")"
gcloud compute copy-files "--zone=${JENKINS_ZONE}" lib/{src,vars} transfer-lib.sh "${JENKINS_SERVER}":
gcloud compute ssh "--zone=${JENKINS_ZONE}" "${JENKINS_SERVER}" \
  --command "sudo bash -c 'IMAGE_NAME=${IMAGE_NAME} ./transfer-lib.sh'"
