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

:: Batch script containing the main build phase for windows bazel_github_job-s
@echo on
set BAZEL_SH=c:\tools\msys64\usr\bin\bash.exe

set BAZEL=c:\bazel_ci\installs\%BAZEL_VERSION%\bazel.exe
set TMPDIR=c:\bazel_ci\temp

:: In src/main/native/build_windows_jni.sh, we use `sort --version-sort`
:: So we need to make sure find the msys sort instead of windows sort.
:: TODO(pcloudy): remove this after MSVC toolchain becomes default, because
:: at that time we can build dll by cc_binary for `bazel build src:bazel`.
set PATH=c:\tools\msys64\usr\bin;%PATH%

set ROOT=%cd%
set BAZELRC=%ROOT%\.bazelrc
rm -f %BAZELRC%
echo build {{ variables.BUILD_OPTS }} >> %BAZELRC%
echo test {{ variables.TEST_OPTS }} >> %BAZELRC%
echo test --test_tag_filters {{ variables.TEST_TAG_FILTERS }},-no_windows >> %BAZELRC%
echo test --define JAVA_VERSION=1.8 >> %BAZELRC%

%BAZEL% version

del .unstable

{{ variables.WINDOWS_CONFIGURE }}

if not "{{ variables.WINDOWS_BUILDS }}" == "" (
  call:bazel build {{ variables.WINDOWS_BUILDS }}
)

if not "{{ variables.WINDOWS_TESTS }}" == "" (
  call:bazel test {{ variables.WINDOWS_TESTS }}
)

exit %errorlevel%

:bazel
%BAZEL% --bazelrc=%BAZELRC% %*
set retCode=%errorlevel%
if %retCode%==3 (
  :: Write 1 in the .unstable file so the following step in Jenkins
  :: know that it is a test failure.
  echo 1 > %ROOT%\.unstable
) else (
  if not %retCode%==0 (
    :: Else simply fails the job by exiting with a non null return code
    exit /b %retCode%
  )
)
exit /b 0
