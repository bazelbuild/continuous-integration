// Copyright (C) 2017 The Bazel Authors.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import java.nio.channels.Channels

// Returns the latest Bazel version available on github
@NonCPS
def getLatestBazelVersion() {
  def url = new URL("https://github.com/bazelbuild/bazel/releases/latest")
  def conn = url.openConnection()
  conn.setInstanceFollowRedirects(false)
  String location = conn.getHeaderField("Location").trim()
  return location.replaceAll("^.*/", "")  // Last component of the location is the release tag
}

// Install bazel version X from the web
private def installBazel(script, version, flavour, platform) {
  def release_url = "https://releases.bazel.build/${version}/release"
  if (platform.startsWith("windows")) {
    // TODO(dmarting): this should be included in the flavour rather than special casing here
    def msvc = ""
    if (platform.startsWith("windows-msvc")) {
      msvc = "-msvc"
    }
    def url = "${release_url}/bazel${msvc}-${version}-windows${msvc}-x86_64.exe"
    def to = "c:\\bazel_ci\\installs\\${version}\\bazel.exe"
    script.bat "powershell -Command \"(New-Object Net.WebClient).DownloadFile('${url}', '${to}')\""
  } else {
    def destination ="${env.HOME}/.bazel/${version}${flavour}"
    // TODO(dmarting): this is kind of a hack, can we select -without-jdk in a better way?
    def jdk = flavour.isEmpty() ? "-without-jdk" : ""
    script.sh """#!/bin/bash -x
curl -L -o install.sh '${release_url}/bazel-${version}${flavour}${jdk}-installer-${platform}.sh'
chmod 0755 install.sh
./install.sh --base='${destination}' --bin='${destination}/binary'
"""
  }
}

@NonCPS
private def getPlatformFromNodeName(node) {
  def platforms = ["windows-msvc": "windows-msvc-x86_64",
                   "windows": "windows-x86_64",
                   "darwin": "darwin-x86_64",
                   "": "linux-x86_64"]
  return platforms.find { e -> node.startsWith(e.key) }.value
}

// A step to install a released version of Bazel
// parameters:
//   version: the version to install, default to latest
//   alias: alias of the version, if version is latest, this is set to "latest" too
//   flavour: flavours to install, default [""]
def call(params = [:]) {
  params["version"] = params.get("version", "latest")
  params["flavours"] = params.get("flavours", [""])
  params["alias"] = params.get("alias", params.version == "latest" ? "latest" : "")

  if (params.version == "latest") {
    params.version = getLatestBazelVersion()
  }

  machine(params.node) {
    // Determine the platform
    def platform = getPlatformFromNodeName(params.node)

    // install bazel
    for (flavour in params.flavours) {
      installBazel(this, params.version, flavour, platform)
    }

    // Symlinks
    if (!params.alias.isEmpty()) {
      for (flavour in params.flavours) {
        def from = "${params.version}${flavour}"
        def to = "${params.alias}${flavour}"
        if (platform.startsWith("windows")) {
          bat """
rmdir /q c:\\bazel_ci\\installs\\${to}
mklink /J c:\\bazel_ci\\installs\\${to} c:\\bazel_ci\\installs\\${from}
"""
        } else {
          sh "rm -f ~/.bazel/${to}; ln -s ~/.bazel/${from} ~/.bazel/${to}"
        }
      }
    }
  }
}
