#!/bin/bash

set -euxo pipefail

cd "$HOME"
curl -fL -o android-ndk.zip https://dl.google.com/android/repository/android-ndk-r15c-darwin-x86_64.zip
rm -rfv android-ndk-r15c
unzip android-ndk.zip > /dev/null
rm android-ndk.zip

curl -fLo android-ndk-r25b.dmg https://dl.google.com/android/repository/android-ndk-r25b-darwin.dmg
hdiutil attach android-ndk-r25b.dmg
rm -rfv android-ndk-r25b
cp -r /Volumes/Android\ NDK\ r25b/AndroidNDK8937393.app/Contents/NDK/ android-ndk-r25b
hdiutil detach /Volumes/Android\ NDK\ r25b/
sudo rm -fv android-ndk-r25b.dmg

rm -rf "$HOME/android-sdk-macosx"
mkdir -p "$HOME/android-sdk-macosx/cmdline-tools"
cd "$HOME/android-sdk-macosx/cmdline-tools"

curl -fL -o android-sdk.zip https://dl.google.com/android/repository/commandlinetools-mac-7302050_latest.zip
unzip android-sdk.zip > /dev/null
rm android-sdk.zip
mv cmdline-tools latest
yes | latest/bin/sdkmanager --licenses > /dev/null || true
latest/bin/sdkmanager --update
latest/bin/sdkmanager \
    "build-tools;28.0.2" \
    "build-tools;30.0.3" \
    "extras;android;m2repository" \
    "platform-tools" \
    "platforms;android-24" \
    "platforms;android-28" \
    "platforms;android-29" \
    "platforms;android-30" \
    "platforms;android-31"
