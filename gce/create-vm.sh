#!/bin/bash
#
# Copyright 2015 Google Inc. All rights reserved.
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

# Create the various instances of GCE
set -eu

cd "$(dirname "${BASH_SOURCE[0]}")"

# The container engine VM containing the jenkins instance.
gcloud compute instances create jenkins --tags jenkins \
    --zone us-central1-a --machine-type n1-standard-4 \
    --image container-vm \
    --metadata-from-file google-container-manifest=jenkins.yml,startup-script=mount-volumes.sh \
    --boot-disk-type pd-ssd --boot-disk-size 40GB \
    --address ci --disk name=jenkins-volumes,device-name=volumes

# The ubuntu slave.
gcloud compute instances create ubuntu-14-04-slave \
    --zone us-central1-a --machine-type n1-standard-8 \
    --image ubuntu-14-04 \
    --metadata-from-file startup-script=ubuntu-14-04-slave.sh \
    --boot-disk-type pd-ssd --boot-disk-size 80GB

