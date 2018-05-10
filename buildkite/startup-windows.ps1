## Stop on action error.
$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

## Load PowerShell support for ZIP files.
Add-Type -AssemblyName "System.IO.Compression.FileSystem"

## Remove write access to volumes for unprivileged users.
Write-Host "Setting NTFS permissions..."
Remove-NTFSAccess "C:\" -Account BUILTIN\Users -AccessRights Write
Add-NTFSAccess "C:\temp" -Account BUILTIN\Users -AccessRights Write

## Redirect MSYS2's tmp folder to C:\temp
Remove-Item -Recurse -Force C:\tools\msys64\tmp
New-Item -ItemType Junction -Path "C:\tools\msys64\tmp" -Value "C:\temp"

## Create Buildkite agent working directory (C:\build).
Write-Host "Creating build folder..."
Remove-Item "C:\build" -Recurse -ErrorAction Ignore
New-Item "C:\build" -ItemType "directory"
Add-NTFSAccess "C:\build" -Account BUILTIN\Users -AccessRights Write

## Setup the TEMP and TMP environment variables.
[Environment]::SetEnvironmentVariable("TEMP", "C:\temp", "Machine")
[Environment]::SetEnvironmentVariable("TMP", "C:\temp", "Machine")
$env:TEMP = [Environment]::GetEnvironmentVariable("TEMP", "Machine")
$env:TMP = [Environment]::GetEnvironmentVariable("TMP", "Machine")

## Download the Buildkite agent token.
Write-Host "Getting Buildkite Agent token from GCS..."
$buildkite_agent_token_url = "https://storage.googleapis.com/bazel-encrypted-secrets/buildkite-agent-token.enc"
$buildkite_agent_token_file = "C:\buildkite_agent_token.enc"
(New-Object Net.WebClient).DownloadFile($buildkite_agent_token_url, $buildkite_agent_token_file)

## Decrypt the Buildkite agent token.
Write-Host "Decrypting Buildkite Agent token using KMS..."
$buildkite_agent_token = & gcloud kms decrypt --location global --keyring buildkite --key buildkite-agent-token --ciphertext-file $buildkite_agent_token_file --plaintext-file -
Remove-Item $buildkite_agent_token_file

## Download and unpack our Git snapshot.
$bazelbuild_url = "https://storage.googleapis.com/bazel-git-mirror/bazelbuild.zip"
$bazelbuild_zip = "c:\temp\bazelbuild.zip"
$bazelbuild_root = "c:\buildkite"
(New-Object Net.WebClient).DownloadFile($bazelbuild_url, $bazelbuild_zip)
[System.IO.Compression.ZipFile]::ExtractToDirectory($bazelbuild_zip, $bazelbuild_root)
Remove-Item $bazelbuild_zip

## Get the current image version.
$image_version = (Get-Content "c:\buildkite\image.version" -Raw).Trim()

## Configure the Buildkite agent.
Write-Host "Configuring Buildkite Agent..."
$buildkite_agent_root = "c:\buildkite"
$buildkite_agent_config = @"
token="${buildkite_agent_token}"
name="%hostname-%n"
tags="kind=worker,os=windows,java=8,image-version=${image_version}"
build-path="c:\build"
hooks-path="c:\buildkite\hooks"
plugins-path="c:\buildkite\plugins"
git-clone-flags="-v --reference c:\buildkite\bazelbuild"
disconnect-after-job=true
disconnect-after-job-timeout=86400
"@
[System.IO.File]::WriteAllLines("${buildkite_agent_root}\buildkite-agent.cfg", $buildkite_agent_config)

## Start the Buildkite agent service.
if ($(hostname) -match 'buildkite-') {
  Write-Host "Starting Buildkite Monitor..."
  & nssm start buildkite-monitor
}
