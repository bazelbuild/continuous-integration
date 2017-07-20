:: Copyright 2016 The Bazel Authors. All rights reserved.
::
:: Licensed under the Apache License, Version 2.0 (the "License");
:: you may not use this file except in compliance with the License.
:: You may obtain a copy of the License at
::
::    http://www.apache.org/licenses/LICENSE-2.0
::
:: Unless required by applicable law or agreed to in writing, software
:: distributed under the License is distributed on an "AS IS" BASIS,
:: WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
:: See the License for the specific language governing permissions and
:: limitations under the License.

:: Batch script to install bazel on the windows host
@echo on

:: Get the latest bazel version number
echo $url = "https://github.com/bazelbuild/bazel/releases/latest" > get_latest_bazel_version.ps1
echo $req=[system.Net.HttpWebRequest]::Create($url); >> get_latest_bazel_version.ps1
echo $res = $req.getresponse(); >> get_latest_bazel_version.ps1
echo $res.Close(); >> get_latest_bazel_version.ps1
echo $res.ResponseUri.AbsolutePath.TrimStart("/bazelbuild/bazel/releases/tag/") >> get_latest_bazel_version.ps1
for /F %%i in ('powershell -file get_latest_bazel_version.ps1') do set BAZEL_VERSION=%%i
del get_latest_bazel_version.ps1

echo BAZEL_VERSION=(%BAZEL_VERSION%)
if "%BAZEL_VERSION%" == "" (
  echo ERROR: Could not parse BAZEL_VERSION from https://github.com/bazelbuild/bazel/releases/latest
  exit 1
)

:: Download the latest bazel release
set folder=c:\bazel_ci\installs\%BAZEL_VERSION%


:: Download MSVC version Bazel.
:: TODO(pcloudy): Use the following URL after default Bazel release is MSVC version
:: set url='https://releases.bazel.build/%BAZEL_VERSION%/release/bazel-%BAZEL_VERSION%-windows-x86_64.exe'
set url='https://releases.bazel.build/%BAZEL_VERSION%/release/bazel-msvc-%BAZEL_VERSION%-windows-msvc-x86_64.exe'

if not exist %folder%\bazel.exe (
  md %folder%
  powershell -Command "(New-Object Net.WebClient).DownloadFile(%url%, '%folder%\bazel.exe')"
)

:: Create a junction to the latest release
rmdir /q c:\bazel_ci\installs\latest
mklink /J c:\bazel_ci\installs\latest %folder%

:: Also update bootstrap Bazel to the latest release
rmdir /q c:\bazel_ci\installs\bootstrap
mklink /J c:\bazel_ci\installs\bootstrap %folder%

:: Install Bazel built at HEAD
md c:\bazel_ci\installs\HEAD
echo F | xcopy /y "bazel-installer\PLATFORM_NAME=windows-x86_64\output\ci\bazel*.exe" c:\bazel_ci\installs\HEAD\bazel.exe

if not exist c:\bazel_ci\installs\HEAD\bazel.exe (
  exit 1
)
