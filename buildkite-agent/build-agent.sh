#!/bin/sh

set -eux

rm -rf bin
mkdir bin

GOOS=linux GOARCH=amd64 go build -i -o bin/buildkite-agent-linux-amd64 &
GOOS=darwin GOARCH=amd64 go build -i -o bin/buildkite-agent-darwin-amd64 &
GOOS=windows GOARCH=amd64 go build -i -o bin/buildkite-agent-windows-amd64.exe &
wait

