#!/bin/bash

set -eux

sudo launchctl unload /Library/LaunchDaemons/jenkins.plist

cd /Users/ci
rm -rf /var/tmp/_bazel_ci workspace android-ndk-* android-sdk-* node jenkins.slave.*.log slave.jar
curl https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/mac/mac-android.sh | bash
curl https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/mac/mac-nodejs.sh | bash
curl -o slave.jar http://master.ci.bazel.io/jnlpJars/slave.jar

sudo launchctl load /Library/LaunchDaemons/jenkins.plist
