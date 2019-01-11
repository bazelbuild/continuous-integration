## Stop on action error.
$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

## Initialize, partition and format the local SSD.
Write-Host "Initializing local SSD..."
if ((Get-Disk -Number 1).PartitionStyle -ne "RAW") {
  Clear-Disk -Number 1 -RemoveData -RemoveOEM
}
Initialize-Disk -Number 1
New-Partition -DiskNumber 1 -UseMaximumSize -DriveLetter D
Format-Volume -DriveLetter D -ShortFileNameSupport $true

## Load PowerShell support for ZIP files.
Write-Host "Loading support for ZIP files..."
Add-Type -AssemblyName "System.IO.Compression.FileSystem"

## Create temporary folder (D:\temp).
Write-Host "Creating temporary folder on local SSD..."
New-Item "D:\temp" -ItemType "directory"

## Redirect MSYS2's tmp folder to D:\temp
Write-Host "Redirecting MSYS2's tmp folder to D:\temp..."
Remove-Item -Recurse -Force C:\tools\msys64\tmp
New-Item -ItemType Junction -Path "C:\tools\msys64\tmp" -Value "D:\temp"

## Create Buildkite agent working directory (D:\b).
Write-Host "Creating build folder on local SSD..."
Remove-Item "D:\b" -Recurse -Force -ErrorAction Ignore
New-Item "D:\b" -ItemType "directory"

## Setup the TEMP and TMP environment variables.
Write-Host "Setting environment variables..."
[Environment]::SetEnvironmentVariable("TEMP", "D:\temp", "Machine")
[Environment]::SetEnvironmentVariable("TMP", "D:\temp", "Machine")
$env:TEMP = [Environment]::GetEnvironmentVariable("TEMP", "Machine")
$env:TMP = [Environment]::GetEnvironmentVariable("TMP", "Machine")

## Write encrypted buildkite agent token into a file.
$encrypted_token = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("CiQA4iyQCY654VP8LoPAgFwjMDzRilLWQwNeqUIy6sz0A4gP4egSWwCyztU1sXJJGDLP0tL007Uvux9zYTpSQRFLRqyXOcOwXKz2Sk+1xe0KT8KjJN1njHBgRwGdCHczuZd8RKVCrtf1vkvR6mfC3xzS9cP2QOUhTSsnA4C/gvccXfE="))
$buildkite_agent_token_file = "d:\buildkite_agent_token.enc"
$encrypted_token | Out-File $buildkite_agent_token_file

## Decrypt the Buildkite agent token.
Write-Host "Decrypting Buildkite Agent token using KMS..."
$buildkite_agent_token = & gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-untrusted-agent-token --ciphertext-file $buildkite_agent_token_file --plaintext-file -
Remove-Item $buildkite_agent_token_file

## Configure the Buildkite agent.
Write-Host "Configuring Buildkite Agent..."
$buildkite_agent_root = "c:\buildkite"
$buildkite_agent_config = @"
token="${buildkite_agent_token}"
name="%hostname"
tags="kind=worker,os=windows,java=8"
build-path="d:\b"
hooks-path="c:\buildkite\hooks"
plugins-path="c:\buildkite\plugins"
git-clone-flags="-v --reference c:\buildkite\bazelbuild"
disconnect-after-job=true
disconnect-after-job-timeout=86400
"@
[System.IO.File]::WriteAllLines("${buildkite_agent_root}\buildkite-agent.cfg", $buildkite_agent_config)

## Start the Buildkite agent service.
try {
    Write-Host "Starting Buildkite agent..."
    & c:\buildkite\buildkite-agent.exe start
} finally {
    Write-Host "Buildkite agent has exited, shutting down."
    Stop-Computer -Force
}
