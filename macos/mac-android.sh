#!/bin/bash

set -euxo pipefail

export JAVA_HOME="$(/usr/libexec/java_home -v 1.8)"

# cd "$HOME"
# curl -fsSL -o android-ndk.zip https://dl.google.com/android/repository/android-ndk-r15c-darwin-x86_64.zip
# unzip android-ndk.zip > /dev/null
# rm android-ndk.zip

rm -rf "$HOME/android-sdk"
mkdir -p "$HOME/android-sdk"
cd "$HOME/android-sdk"
curl -fsSL -o android-sdk.zip https://dl.google.com/android/repository/sdk-tools-darwin-4333796.zip
unzip android-sdk.zip > /dev/null
rm android-sdk.zip
yes | tools/bin/sdkmanager --licenses > /dev/null || true
tools/bin/sdkmanager --update
tools/bin/sdkmanager \
    "build-tools;28.0.2" \
    "build-tools;30.0.3" \
    "extras;android;m2repository" \
    "platform-tools" \
    "platforms;android-24" \
    "platforms;android-28"
