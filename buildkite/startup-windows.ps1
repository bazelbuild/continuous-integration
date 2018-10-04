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

## Remove write access to volumes for unprivileged users.
Write-Host "Setting NTFS permissions..."
Remove-NTFSAccess "C:\" -Account BUILTIN\Users -AccessRights Write
Remove-NTFSAccess "D:\" -Account BUILTIN\Users -AccessRights Write

## Ensure that home directory of buildkite user is deleted.
$buildkite_username = "b"
Write-Host "Deleting home directory of the buildkite user ${buildkite_username} user..."
Get-CimInstance Win32_UserProfile | Where LocalPath -EQ "C:\Users\${buildkite_username}" | Remove-CimInstance
if ( Test-Path "C:\Users\${buildkite_username}" ) {
  Throw "The home directory of the ${buildkite_username} user could not be deleted."
}

## Create temporary folder (D:\temp).
Write-Host "Creating temporary folder on local SSD..."
New-Item "D:\temp" -ItemType "directory"
Add-NTFSAccess "D:\temp" -Account BUILTIN\Users -AccessRights Write

## Redirect MSYS2's tmp folder to D:\temp
Write-Host "Redirecting MSYS2's tmp folder to D:\temp..."
Remove-Item -Recurse -Force C:\tools\msys64\tmp
New-Item -ItemType Junction -Path "C:\tools\msys64\tmp" -Value "D:\temp"

## Create Buildkite agent working directory (D:\build).
Write-Host "Creating build folder on local SSD..."
Remove-Item "D:\build" -Recurse -Force -ErrorAction Ignore
New-Item "D:\build" -ItemType "directory"
Add-NTFSAccess "D:\build" -Account BUILTIN\Users -AccessRights Write

## Setup the TEMP and TMP environment variables.
Write-Host "Setting environment variables..."
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

## Download and unpack our Git snapshot.
Write-Host "Downloading Git snapshot..."
$bazelbuild_url = "https://storage.googleapis.com/bazel-git-mirror/bazelbuild.zip"
$bazelbuild_zip = "c:\temp\bazelbuild.zip"
$bazelbuild_root = "c:\buildkite"
(New-Object Net.WebClient).DownloadFile($bazelbuild_url, $bazelbuild_zip)
Write-Host "Unpacking Git snapshot..."
Expand-Archive -LiteralPath $bazelbuild_zip -DestinationPath $bazelbuild_root -Force
Remove-Item $bazelbuild_zip

## Get the current image version.
Write-Host "Getting image version..."
$image_version = (Get-Content "c:\buildkite\image.version" -Raw).Trim()

## Configure the Buildkite agent.
Write-Host "Configuring Buildkite Agent..."
$buildkite_agent_root = "c:\buildkite"
$buildkite_agent_config = @"
token="${buildkite_agent_token}"
name="%hostname-%n"
tags="kind=worker,os=windows,java=8,image-version=${image_version}"
build-path="d:\build"
hooks-path="c:\buildkite\hooks"
plugins-path="c:\buildkite\plugins"
git-clone-flags="-v --reference c:\buildkite\bazelbuild"
disconnect-after-job=true
disconnect-after-job-timeout=86400
"@
[System.IO.File]::WriteAllLines("${buildkite_agent_root}\buildkite-agent.cfg", $buildkite_agent_config)

## Start the Buildkite agent service.
Write-Host "Starting Buildkite agent as user ${buildkite_username}..."
& nssm start "buildkite-agent"

Write-Host "Waiting for Buildkite agent to exit..."
While ((Get-Service "buildkite-agent").Status -eq "Running") { Start-Sleep -Seconds 1 }

Write-Host "Buildkite agent has exited, rebooting."
Restart-Computer -Force
