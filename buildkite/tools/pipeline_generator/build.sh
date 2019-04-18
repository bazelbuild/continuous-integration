#!/bin/bash

set -euxo pipefail

GOOS=linux GOARCH=amd64 go build -o releases/export-linux-amd64 export/main.go
GOOS=darwin GOARCH=amd64 go build -o releases/export-darwin-amd64 export/main.go
GOOS=windows GOARCH=amd64 go build -o releases/export-windows-amd64.exe export/main.go