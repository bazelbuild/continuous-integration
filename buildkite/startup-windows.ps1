## Stop on action error.
$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

Write-Host "Initializing local SSD..."
if ((Get-Disk -Number 1).PartitionStyle -ne "RAW") {
  Clear-Disk -Number 1 -RemoveData -RemoveOEM
}
Initialize-Disk -Number 1
New-Partition -DiskNumber 1 -UseMaximumSize -DriveLetter D
Format-Volume -DriveLetter D

Write-Host "Creating temporary folder on local SSD..."
New-Item "D:\temp" -ItemType "directory"
New-Item "D:\build" -ItemType "directory"
[Environment]::SetEnvironmentVariable("TEMP", "D:\temp", "Machine")
[Environment]::SetEnvironmentVariable("TMP", "D:\temp", "Machine")
$env:TEMP = [Environment]::GetEnvironmentVariable("TEMP", "Machine")
$env:TMP = [Environment]::GetEnvironmentVariable("TMP", "Machine")

Write-Host "Getting Buildkite Agent token from GCS..."
$buildkite_agent_token_url = "https://storage.googleapis.com/bazel-encrypted-secrets/buildkite-agent-token.enc"
$buildkite_agent_token_file = "d:\buildkite_agent_token.enc"
(New-Object Net.WebClient).DownloadFile($buildkite_agent_token_url, $buildkite_agent_token_file)

Write-Host "Decrypting Buildkite Agent token using KMS..."
$buildkite_agent_token = & gcloud kms decrypt --location global --keyring buildkite --key buildkite-agent-token --ciphertext-file $buildkite_agent_token_file --plaintext-file -
Remove-Item $buildkite_agent_token_file

## Configure the Buildkite agent.
Write-Host "Configuring Buildkite Agent..."
$buildkite_agent_root = "c:\buildkite"
$buildkite_agent_config=@"
token="${buildkite_agent_token}"
name="%hostname"
tags="os=windows"
build-path="d:\build"
hooks-path="c:\buildkite\hooks"
plugins-path="c:\buildkite\plugins"
"@
[System.IO.File]::WriteAllLines("${buildkite_agent_root}\buildkite-agent.cfg", $buildkite_agent_config)

& net start buildkite-service
