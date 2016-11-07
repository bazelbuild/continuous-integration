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

:: Batch to avoid failing bazel_github_job because of the absence of log files

if EXIST "{{ variables.WORKSPACE }}/bazel-testlogs" (
  rmdir /q "{{ variables.WORKSPACE }}/bazel-testlogs"
  md "{{ variables.WORKSPACE }}/bazel-testlogs"
)

set LOGFILE="{{ variables.WORKSPACE }}/bazel-testlogs/dummy.xml"
echo ^<?xml version="1.0" encoding="UTF-8"?^> > %LOGFILE%
echo ^<testsuites^> >> %LOGFILE%
echo ^<testsuite name="dummy" tests="0" failures="0" errors="0"/^> >> %LOGFILE%
echo ^</testsuites^> >> %LOGFILE%
