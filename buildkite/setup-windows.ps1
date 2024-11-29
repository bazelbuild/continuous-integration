## Stop on action error.
$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

## Use only the global PATH, not any user-specific bits.
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")

## Load PowerShell support for ZIP files.
Add-Type -AssemblyName "System.IO.Compression.FileSystem"

## Use TLS1.2 for HTTPS (fixes an issue where later steps can't connect to github.com)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

## If choco is already installed, this is the second time the VM starts up, run GCESysprep and then shutdown
if (Get-Command choco -ErrorAction SilentlyContinue) {
    $port = New-Object System.IO.Ports.SerialPort COM1,9600,None,8,one
    $port.Open()
    $port.WriteLine("[setup-windows.ps1]: choco is already installed, this is the second time the VM starts up, running GCESysprep and then shutdown...")
    $port.Close()
    GCESysprep
    exit 0
}

$port = New-Object System.IO.Ports.SerialPort COM1,9600,None,8,one
$port.Open()
$port.WriteLine("[setup-windows.ps1]: Starting to setup windows... This could take up to one hour, check C:/setup-stdout.log on the VM for progress.")
$port.Close()

## Create C:\temp
Write-Host "Creating temporary folder C:\temp..."
if (-Not (Test-Path "c:\temp")) {
    New-Item "c:\temp" -ItemType "directory"
}
[Environment]::SetEnvironmentVariable("TEMP", "C:\temp", "Machine")
[Environment]::SetEnvironmentVariable("TMP", "C:\temp", "Machine")
[Environment]::SetEnvironmentVariable("TEMP", "C:\temp", "User")
[Environment]::SetEnvironmentVariable("TMP", "C:\temp", "User")
$env:TEMP = [Environment]::GetEnvironmentVariable("TEMP", "Machine")
$env:TMP = [Environment]::GetEnvironmentVariable("TMP", "Machine")

## Disable Windows Firewall.
Write-Host "Disabling Windows Firewall..."
# Achtung: Set-NetFirewallProfile's parameter types are a bit special.
# "-Profile" doesn't want a String, and "-Enabled" doesn't want a Boolean, so
# don't quote the first one and don't use $false for the second one...
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False

## Disable Windows Defender.
Write-Host "Disabling Windows Defender..."
Set-MpPreference -DisableRealtimeMonitoring $true
Uninstall-WindowsFeature -Name "Windows-Defender"

## Set system timezone.
Write-Host "Setting timezone..."
Set-TimeZone "W. Europe Standard Time"

## Enable developer mode.
Write-Host "Enabling developer mode..."
& reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1"

## Enable long paths.
Write-Host "Enabling long paths..."
& reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem" /t REG_DWORD /f /v "LongPathsEnabled" /d "1"

## Enable Microsoft Updates.
Write-Host "Enabling PowerShell Gallery provider..."
Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force
Set-PSRepository -Name PSGallery -InstallationPolicy Trusted

## Install support for managing NTFS ACLs in PowerShell.
Write-Host "Installing NTFSSecurity module..."
Install-Module NTFSSecurity

## Install Chocolatey
Write-Host "Installing Chocolatey..."
# Chocolatey adds "C:\ProgramData\chocolatey\bin" to global PATH.
Invoke-Expression ((New-Object Net.WebClient).DownloadString("https://chocolatey.org/install.ps1"))
& choco feature enable -n allowGlobalConfirmation
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")

Write-Host "All done, rebooting..."

$port = New-Object System.IO.Ports.SerialPort COM1,9600,None,8,one
$port.Open()
$port.WriteLine("[setup-windows.ps1]: Setup windows done, rebooting...")
$port.Close()

Restart-Computer
