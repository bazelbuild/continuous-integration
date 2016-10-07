@echo on

mkdir c:\bazel_ci\installs

copy "bazel-installer\JAVA_VERSION=1.8,PLATFORM_NAME=windows-x86_64\output\ci\bazel*.exe" c:\bazel_ci\installs\bazel-jdk8.exe
