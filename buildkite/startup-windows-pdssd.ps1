## Stop on action error.
$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

## Use TLS1.2 for HTTPS (fixes an issue where later steps can't connect to github.com)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

## Load PowerShell support for ZIP files.
Write-Host "Loading support for ZIP files..."
Add-Type -AssemblyName "System.IO.Compression.FileSystem"

## Create Buildkite agent working directory (C:\b).
Write-Host "Creating build folder on PD-SSD..."
Remove-Item "C:\b" -Recurse -Force -ErrorAction Ignore
New-Item "C:\b" -ItemType "directory"

## Setup environment variables.
Write-Host "Setting environment variables..."
[Environment]::SetEnvironmentVariable("TEMP", "C:\temp", "Machine")
[Environment]::SetEnvironmentVariable("TMP", "C:\temp", "Machine")
$env:TEMP = [Environment]::GetEnvironmentVariable("TEMP", "Machine")
$env:TMP = [Environment]::GetEnvironmentVariable("TMP", "Machine")
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")

## Create an environment hook for the Buildkite agent.
$myhostname = [System.Net.Dns]::GetHostName()
if ($myhostname -like "*trusted*") {
  $artifact_bucket = "bazel-trusted-buildkite-artifacts"
} elseif ($myhostname -like "*testing*") {
  $artifact_bucket = "bazel-testing-buildkite-artifacts"
} else {
  $artifact_bucket = "bazel-untrusted-buildkite-artifacts"
}

Write-Host "Creating Buildkite agent environment hook..."
$buildkite_environment_hook = @"
SET BUILDKITE_ARTIFACT_UPLOAD_DESTINATION=gs://${artifact_bucket}/%BUILDKITE_JOB_ID%
SET ANDROID_HOME=${env:ANDROID_HOME}
SET ANDROID_NDK_HOME=${env:ANDROID_NDK_HOME}
SET JAVA_HOME=${env:JAVA_HOME}
SET PATH=${env:PATH}
SET TEMP=${env:TEMP}
SET TMP=${env:TEMP}
"@
[System.IO.File]::WriteAllLines("c:\buildkite\hooks\environment.bat", $buildkite_environment_hook)

Write-Host "Creating Buildkite agent pre-exit hook..."
$buildkite_preexit_hook = @"
wmic pagefile list /format:list
"@
[System.IO.File]::WriteAllLines("c:\buildkite\hooks\pre-exit.bat", $buildkite_preexit_hook)

## Enable support for symlinks.
Write-Host "Enabling SECreateSymbolicLinkPrivilege permission..."
$ntprincipal = New-Object System.Security.Principal.NTAccount "b"
$sid = $ntprincipal.Translate([System.Security.Principal.SecurityIdentifier])
$sidstr = $sid.Value.ToString()

$tmp = [System.IO.Path]::GetTempFileName()
& secedit.exe /export /cfg "$($tmp)"
$currentConfig = Get-Content -Path "$tmp"
$currentSetting = ""
foreach ($s in $currentConfig) {
    if ($s -like "SECreateSymbolicLinkPrivilege*") {
        $x = $s.split("=",[System.StringSplitOptions]::RemoveEmptyEntries)
        $currentSetting = $x[1].Trim()
    }
}

if ([string]::IsNullOrEmpty($currentSetting)) {
    $currentSetting = "*$($sidstr)"
} else {
    $currentSetting = "*$($sidstr),$($currentSetting)"
}
$outfile = @"
[Unicode]
Unicode=yes
[Version]
signature="`$CHICAGO`$"
Revision=1
[Privilege Rights]
SECreateSymbolicLinkPrivilege = $($currentSetting)
"@
$outfile | Set-Content -Path $tmp -Encoding Unicode -Force
& secedit.exe /configure /db "secedit.sdb" /cfg "$($tmp)" /areas USER_RIGHTS
Remove-Item -Path "$tmp"

## Write encrypted buildkite agent token into a file.
$myhostname = [System.Net.Dns]::GetHostName()
if ($myhostname -like "*trusted*") {
  $buildkite_agent_token_url = "https://storage.googleapis.com/bazel-trusted-encrypted-secrets/buildkite-trusted-agent-token.enc"
  $project = "bazel-public"
  $key = "buildkite-trusted-agent-token"
} elseif ($myhostname -like "*testing*") {
  $buildkite_agent_token_url = "https://storage.googleapis.com/bazel-testing-encrypted-secrets/buildkite-testing-agent-token.enc"
  $project = "bazel-untrusted"
  $key = "buildkite-testing-agent-token"
} else {
  $buildkite_agent_token_url = "https://storage.googleapis.com/bazel-untrusted-encrypted-secrets/buildkite-untrusted-agent-token.enc"
  $project = "bazel-untrusted"
  $key = "buildkite-untrusted-agent-token"
}
$buildkite_agent_token_file = "c:\buildkite\buildkite_agent_token.enc"

Write-Host "Getting Buildkite Agent token from GCS..."

# Try at most 30 times to download file, if not succeeding, shutdown the VM.
$maxAttempts = 30
$attemptCount = 0

while ($attemptCount -lt $maxAttempts) {
  try {
    (New-Object Net.WebClient).DownloadFile($buildkite_agent_token_url, $buildkite_agent_token_file)
    Write-Host "Token downloaded successfully."
    break
  } catch {
    $msg = $_.Exception.Message
    Write-Host "Failed to download token: $msg"

    $attemptCount++
    Write-Host "Attempt $attemptCount of $maxAttempts"

    Start-Sleep -Seconds 10
  }
}

# Check if maximum attempts were reached and shut down if necessary
if ($attemptCount -eq $maxAttempts) {
  Write-Host "Maximum attempts reached. Shutting down the machine..."
  Stop-Computer
}

# Fix ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1129)
# Apply changes from https://github.com/bazelbuild/rules_foreign_cc/pull/1171
cd $env:USERPROFILE;
Invoke-WebRequest https://curl.haxx.se/ca/cacert.pem -OutFile $env:USERPROFILE\cacert.pem;
$plaintext_pw = 'PASSWORD';
$secure_pw = ConvertTo-SecureString $plaintext_pw -AsPlainText -Force;
& openssl.exe pkcs12 -export -nokeys -out certs.pfx -in cacert.pem -passout pass:$plaintext_pw;
Import-PfxCertificate -Password $secure_pw  -CertStoreLocation Cert:\LocalMachine\Root -FilePath certs.pfx;

## Decrypt the Buildkite agent token.
Write-Host "Decrypting Buildkite Agent token using KMS..."
$buildkite_agent_token = & gcloud kms decrypt --project $project --location global --keyring buildkite --key $key --ciphertext-file $buildkite_agent_token_file --plaintext-file -
Remove-Item $buildkite_agent_token_file

## Configure the Buildkite agent.
Write-Host "Configuring Buildkite Agent..."
$buildkite_agent_root = "c:\buildkite"
$buildkite_agent_config = @"
token="${buildkite_agent_token}"
name="%hostname"
tags="queue=windows,kind=worker,os=windows"
experiment="git-mirrors"
build-path="c:\b"
hooks-path="c:\buildkite\hooks"
plugins-path="c:\buildkite\plugins"
git-mirrors-path="c:\buildkite\bazelbuild"
git-clone-mirror-flags="-v --bare"
disconnect-after-job=true
health-check-addr=0.0.0.0:8080
"@
[System.IO.File]::WriteAllLines("${buildkite_agent_root}\buildkite-agent.cfg", $buildkite_agent_config)

## Start the Buildkite agent service.
try {
  Write-Host "Starting Buildkite agent..."
  Start-Service -Name "buildkite-agent"

  Write-Host "Waiting for Buildkite agent to start..."
  (Get-Service -Name "buildkite-agent").WaitForStatus([ServiceProcess.ServiceControllerStatus]::Running)
  Write-Host "Waiting for Buildkite agent to exit..."
  (Get-Service -Name "buildkite-agent").WaitForStatus([ServiceProcess.ServiceControllerStatus]::Stopped)
  Write-Host "Buildkite agent has exited."
} finally {
  Write-Host "Waiting for at least one minute of uptime..."
  ## Wait until the machine has been running for at least one minute, in order to
  ## prevent exponential backoff from happening when it terminates too early.
  $up = (Get-CimInstance -ClassName win32_operatingsystem).LastBootUpTime
  $uptime = ((Get-Date) - $up).TotalSeconds
  $timetosleep = 60 - $uptime
  if ($timetosleep -gt 0) {
    Start-Sleep -Seconds $timetosleep
  }

  Write-Host "Shutting down..."
  Stop-Computer
}
