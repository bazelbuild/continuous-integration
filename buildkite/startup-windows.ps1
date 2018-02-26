## Stop on action error.
$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

# Initialize, partition and format the local SSD.
Write-Host "Initializing local SSD..."
if ((Get-Disk -Number 1).PartitionStyle -ne "RAW") {
  Clear-Disk -Number 1 -RemoveData -RemoveOEM
}
Initialize-Disk -Number 1
New-Partition -DiskNumber 1 -UseMaximumSize -DriveLetter D
Format-Volume -DriveLetter D -ShortFileNameSupport $true

# Remove write access to volumes for unprivileged users.
Write-Host "Setting NTFS permissions..."
Remove-NTFSAccess "C:\" -Account BUILTIN\Users -AccessRights Write
Remove-NTFSAccess "D:\" -Account BUILTIN\Users -AccessRights Write

# Create temporary folder (D:\temp).
Write-Host "Creating temporary folder on local SSD..."
New-Item "D:\temp" -ItemType "directory"
Add-NTFSAccess "D:\temp" -Account BUILTIN\Users -AccessRights Write

# Redirect MSYS2's tmp folder to D:\temp
Remove-Item -Recurse -Force C:\tools\msys64\tmp
New-Item -ItemType Junction -Path "C:\tools\msys64\tmp" -Value "D:\temp"

# Create Buildkite agent working directory (D:\build).
Write-Host "Creating build folder on local SSD..."
New-Item "D:\build" -ItemType "directory"
Add-NTFSAccess "D:\build" -Account BUILTIN\Users -AccessRights Write

# Setup the TEMP and TMP environment variables.
[Environment]::SetEnvironmentVariable("TEMP", "D:\temp", "Machine")
[Environment]::SetEnvironmentVariable("TMP", "D:\temp", "Machine")
$env:TEMP = [Environment]::GetEnvironmentVariable("TEMP", "Machine")
$env:TMP = [Environment]::GetEnvironmentVariable("TMP", "Machine")

## Download the Buildkite agent token.
Write-Host "Getting Buildkite Agent token from GCS..."
$buildkite_agent_token_url = "https://storage.googleapis.com/bazel-encrypted-secrets/buildkite-agent-token.enc"
$buildkite_agent_token_file = "d:\buildkite_agent_token.enc"
(New-Object Net.WebClient).DownloadFile($buildkite_agent_token_url, $buildkite_agent_token_file)

## Decrypt the Buildkite agent token.
Write-Host "Decrypting Buildkite Agent token using KMS..."
$buildkite_agent_token = & gcloud kms decrypt --location global --keyring buildkite --key buildkite-agent-token --ciphertext-file $buildkite_agent_token_file --plaintext-file -
Remove-Item $buildkite_agent_token_file

## Configure the Buildkite agent.
Write-Host "Configuring Buildkite Agent..."
$buildkite_agent_root = "c:\buildkite"
$buildkite_agent_config = @"
token="${buildkite_agent_token}"
name="%hostname"
tags="os=windows"
build-path="d:\build"
hooks-path="c:\buildkite\hooks"
plugins-path="c:\buildkite\plugins"
timestamp-lines=true

# Stop the agent (which will automatically be restarted) after each job.
disconnect-after-job=true
disconnect-after-job-timeout=86400
"@
[System.IO.File]::WriteAllLines("${buildkite_agent_root}\buildkite-agent.cfg", $buildkite_agent_config)

# Start the Buildkite agent service.
if ($(hostname) -match 'buildkite-') {
  Write-Host "Starting Buildkite Monitor..."
  & nssm start buildkite-monitor
}
