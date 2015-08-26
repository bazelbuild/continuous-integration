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

# Delete all VM. This won't lose the Jenkins state as it goes into a
# persistent disk. Use this script after calling shutdown on Jenkins to
# avoid racing with ongoing Job.
gcloud compute instances delete --zone=us-central1-a jenkins
gcloud compute instances delete --zone=us-central1-a ubuntu-14-10-slave
