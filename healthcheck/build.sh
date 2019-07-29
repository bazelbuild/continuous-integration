#!/bin/sh

set -eux

rm -rf bin
mkdir bin

GOOS=linux GOARCH=amd64 go build -o bin/healthcheck-linux-amd64
GOOS=darwin GOARCH=amd64 go build -o bin/healthcheck-darwin-amd64
GOOS=windows GOARCH=amd64 go build -o bin/healthcheck-windows-amd64.exe
