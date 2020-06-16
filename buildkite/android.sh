#!/bin/bash

set -euxo pipefail

### Make sure that Cloud Filestore is mounted to /mnt first!

# Install Android NDK
cd /mnt
curl -Lo android-ndk.zip https://dl.google.com/android/repository/android-ndk-r15c-linux-x86_64.zip
unzip android-ndk.zip
rm android-ndk.zip
chown -R root:root /mnt/android-ndk-r15c

# Install Android SDK
mkdir -p /mnt/android-sdk-linux
cd /mnt/android-sdk-linux
curl -Lo android-sdk.zip https://dl.google.com/android/repository/sdk-tools-linux-4333796.zip
unzip android-sdk.zip
rm android-sdk.zip
yes | tools/bin/sdkmanager --licenses > /dev/null
tools/bin/sdkmanager --update
tools/bin/sdkmanager \
    "build-tools;28.0.2" \
    "build-tools;29.0.3" \
    "build-tools;30.0.0" \
    "emulator" \
    "extras;android;m2repository" \
    "platform-tools" \
    "platforms;android-24" \
    "platforms;android-28" \
    "system-images;android-19;default;x86" \
    "system-images;android-21;default;x86" \
    "system-images;android-22;default;x86" \
    "system-images;android-23;default;x86"
chown -R root:root /mnt/android-sdk-linux
