## Stop on action error.
$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

## Use only the global PATH, not any user-specific bits.
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")

## Load PowerShell support for ZIP files.
Add-Type -AssemblyName "System.IO.Compression.FileSystem"

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

## Enable running unsigned PowerShell scripts.
# Write-Host "Setting PowerShell Execution Policy..."
# Set-ExecutionPolicy -ExecutionPolicy Undefined -Scope CurrentUser -Force
# Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine -Force
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force

## Enable Microsoft Updates.
Write-Host "Enabling PowerShell Gallery provider..."
Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force
Set-PSRepository -Name PSGallery -InstallationPolicy Trusted

## Enable Microsoft Updates.
# Write-Host "Installing all available Windows Updates (this can take ~30 minutes)..."
# Install-Module PSWindowsUpdate
# Get-Command -Module PSWindowsUpdate
# Get-WindowsUpdate -Install -AcceptAll -AutoReboot
# This fails with: https://gist.github.com/philwo/010bb5dffc62eccb391cd916c3bee2be
# Add-WUServiceManager -ServiceID 7971f918-a847-4430-9279-4a52d1efe18d
# Get-WindowsUpdate -Install -MicrosoftUpdate -AcceptAll -AutoReboot

## Install support for managing NTFS ACLs in PowerShell.
Write-Host "Installing NTFSSecurity module..."
Install-Module NTFSSecurity

## Install Chocolatey
Write-Host "Installing Chocolatey..."
# Chocolatey adds "C:\ProgramData\chocolatey\bin" to global PATH.
Invoke-Expression ((New-Object Net.WebClient).DownloadString("https://chocolatey.org/install.ps1"))
& choco feature enable -n allowGlobalConfirmation
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")

## Install curl
Write-Host "Installing curl..."
# FYI: choco installs curl.exe in C:\ProgramData\chocolatey\bin (which is on the PATH).
& choco install curl

## Install Git for Windows.
Write-Host "Installing Git for Windows..."
# FYI: choco adds "C:\Program Files\Git\cmd" to global PATH.
& choco install git --params="'/GitOnlyOnPath'"
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")

## Install MSYS2
Write-Host "Installing MSYS2..."
# FYI: We don't add MSYS2 to the PATH on purpose.
& choco install msys2 --params="'/NoPath /NoUpdate'"

[Environment]::SetEnvironmentVariable("BAZEL_SH", "C:\tools\msys64\usr\bin\bash.exe", "Machine")
$env:BAZEL_SH = [Environment]::GetEnvironmentVariable("BAZEL_SH", "Machine")
Set-Alias bash "c:\tools\msys64\usr\bin\bash.exe"

## This is a temporary hack that is necessary, because otherwise pacman asks whether it should
## remove 'catgets' and 'libcatgets', which '--noconfirm' unfortunately answers with 'no', which
## then causes the installation to fail.
Write-Host "Removing MSYS2 catgets and libcatgets packages..."
& bash -lc "pacman --noconfirm -R catgets libcatgets"

## Update MSYS2 once.
Write-Host "Updating MSYS2 packages (round 1)..."
& bash -lc "pacman --noconfirm -Syuu"

## Update again, in case the first round only upgraded core packages.
Write-Host "Updating MSYS2 packages (round 2)..."
& bash -lc "pacman --noconfirm -Syuu"

## Install MSYS2 packages required by Bazel.
Write-Host "Installing required MSYS2 packages..."
& bash -lc "pacman --noconfirm --needed -S curl zip unzip gcc tar diffutils patch perl"

## Install Azul Zulu.
Write-Host "Installing Zulu 8..."
$zulu_url = "https://cdn.azul.com/zulu/bin/zulu8.28.0.1-jdk8.0.163-win_x64.zip"
$zulu_zip = "c:\temp\zulu8.28.0.1-jdk8.0.163-win_x64.zip"
$zulu_extracted_path = "c:\temp\" + [IO.Path]::GetFileNameWithoutExtension($zulu_zip)
$zulu_root = "c:\openjdk"
(New-Object Net.WebClient).DownloadFile($zulu_url, $zulu_zip)
[System.IO.Compression.ZipFile]::ExtractToDirectory($zulu_zip, "c:\temp")
Move-Item $zulu_extracted_path -Destination $zulu_root
Remove-Item $zulu_zip
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";${zulu_root}\bin"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH, "Machine")
$env:JAVA_HOME = $zulu_root
[Environment]::SetEnvironmentVariable("JAVA_HOME", $env:JAVA_HOME, "Machine")

## Install the JDK.
# Write-Host "Installing JDK 8..."
# FYI: choco adds "C:\Program Files\Java\jdk<version>\bin" to global PATH.
# FYI: choco sets JAVA_HOME to "C:\Program Files\Java\jdk<version>\bin".
# & choco install jdk8
# $env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")
# $env:JAVA_HOME = [Environment]::GetEnvironmentVariable("JAVA_HOME", "Machine")
# Write-Host "JAVA_HOME was set to '${JAVA_HOME}'..."

## Install Visual C++ 2015 Build Tools (Update 3).
Write-Host "Installing Visual C++ 2015 Build Tools..."
(New-Object Net.WebClient).DownloadFile("http://go.microsoft.com/fwlink/?LinkId=691126", "c:\temp\visualcppbuildtools_full.exe")
Start-Process -Wait "c:\temp\visualcppbuildtools_full.exe" -ArgumentList "/Passive", "/NoRestart"
Remove-Item "c:\temp\visualcppbuildtools_full.exe"
[Environment]::SetEnvironmentVariable("BAZEL_VC", "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC", "Machine")
$env:BAZEL_VC = [Environment]::GetEnvironmentVariable("BAZEL_VC", "Machine")

## Install Visual C++ 2017 Build Tools.
# Write-Host "Installing Visual C++ 2017 Build Tools..."
# & choco install microsoft-build-tools
# & choco install visualstudio2017-workload-vctools
# [Environment]::SetEnvironmentVariable("BAZEL_VC", "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\VC", "Machine")
# $env:BAZEL_VC = [Environment]::GetEnvironmentVariable("BAZEL_VC", "Machine")

## Install Python3
Write-Host "Installing Python 3..."
# FYI: choco adds "C:\python3\Scripts\;C:\python3\" to PATH.
& choco install python3 --params="/InstallDir:C:\python3"
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")

## Install a couple of Python modules required by TensorFlow.
Write-Host "Updating Python packages..."
& "C:\Python3\Scripts\pip.exe" install --upgrade `
    autograd `
    numpy `
    portpicker `
    protobuf `
    pyreadline `
    six `
    wheel `
    requests `
    pyyaml
& "C:\Python3\Scripts\pip.exe" install --upgrade --pre `
    github3.py

## Get the latest release version number of Bazel.
Write-Host "Grabbing latest Bazel version number from GitHub..."
$url = "https://github.com/bazelbuild/bazel/releases/latest"
$req = [system.Net.HttpWebRequest]::Create($url)
$res = $req.getresponse()
$res.Close()
$bazel_version = $res.ResponseUri.AbsolutePath.TrimStart("/bazelbuild/bazel/releases/tag/")

## Download the latest Bazel.
Write-Host "Downloading Bazel ${bazel_version}..."
$bazel_url = "https://releases.bazel.build/${bazel_version}/release/bazel-${bazel_version}-without-jdk-windows-x86_64.exe"
New-Item "c:\bazel" -ItemType "directory" -Force
(New-Object Net.WebClient).DownloadFile($bazel_url, "c:\bazel\bazel.exe")
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";c:\bazel"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH, "Machine")

## Download the Android NDK and install into C:\android-ndk-r15c.
$android_ndk_url = "https://dl.google.com/android/repository/android-ndk-r15c-windows-x86_64.zip"
$android_ndk_zip = "c:\temp\android_ndk.zip"
$android_ndk_root = "c:\android_ndk"
New-Item $android_ndk_root -ItemType "directory" -Force
(New-Object Net.WebClient).DownloadFile($android_ndk_url, $android_ndk_zip)
[System.IO.Compression.ZipFile]::ExtractToDirectory($android_ndk_zip, $android_ndk_root)
Rename-Item "${android_ndk_root}\android-ndk-r15c" -NewName "r15c"
[Environment]::SetEnvironmentVariable("ANDROID_NDK_HOME", "${android_ndk_root}\r15c", "Machine")
$env:ANDROID_NDK_HOME = [Environment]::GetEnvironmentVariable("ANDROID_NDK_HOME", "Machine")
Remove-Item $android_ndk_zip

## Download the Android SDK and install into C:\android_sdk.
$android_sdk_url = "https://dl.google.com/android/repository/sdk-tools-windows-3859397.zip"
$android_sdk_zip = "c:\temp\android_sdk.zip"
$android_sdk_root = "c:\android_sdk"
New-Item $android_sdk_root -ItemType "directory" -Force
(New-Object Net.WebClient).DownloadFile($android_sdk_url, $android_sdk_zip)
[System.IO.Compression.ZipFile]::ExtractToDirectory($android_sdk_zip, $android_sdk_root)
[Environment]::SetEnvironmentVariable("ANDROID_HOME", $android_sdk_root, "Machine")
$env:ANDROID_HOME = [Environment]::GetEnvironmentVariable("ANDROID_HOME", "Machine")
Remove-Item $android_sdk_zip

## Accept the Android SDK license agreement.
New-Item "${android_sdk_root}\licenses" -ItemType "directory" -Force
Add-Content -Value "`nd56f5187479451eabf01fb78af6dfcb131a6481e" -Path "${android_sdk_root}\licenses\android-sdk-license" -Encoding ASCII
Add-Content -Value "`nd975f751698a77b662f1254ddbeed3901e976f5a" -Path "${android_sdk_root}\licenses\intel-android-extra-license" -Encoding ASCII

## Update the Android SDK tools.
Rename-Item "${android_sdk_root}\tools" "${android_sdk_root}\tools.old"
& "${android_sdk_root}\tools.old\bin\sdkmanager" "tools"
Remove-Item "${android_sdk_root}\tools.old" -Force -Recurse

## Install all required Android SDK components.
& "${android_sdk_root}\tools\bin\sdkmanager.bat" "platform-tools"
& "${android_sdk_root}\tools\bin\sdkmanager.bat" "build-tools;27.0.3"
& "${android_sdk_root}\tools\bin\sdkmanager.bat" "platforms;android-24"
& "${android_sdk_root}\tools\bin\sdkmanager.bat" "platforms;android-25"
& "${android_sdk_root}\tools\bin\sdkmanager.bat" "platforms;android-26"
& "${android_sdk_root}\tools\bin\sdkmanager.bat" "platforms;android-27"
& "${android_sdk_root}\tools\bin\sdkmanager.bat" "extras;android;m2repository"

## Download and install the Buildkite agent.
Write-Host "Downloading Buildkite agent..."
$buildkite_agent_version = "3.0-beta.39"
$buildkite_agent_url = "https://github.com/buildkite/agent/releases/download/v${buildkite_agent_version}/buildkite-agent-windows-amd64-${buildkite_agent_version}.zip"
$buildkite_agent_zip = "c:\temp\buildkite-agent.zip"
$buildkite_agent_root = "c:\buildkite"
New-Item $buildkite_agent_root -ItemType "directory" -Force
(New-Object Net.WebClient).DownloadFile($buildkite_agent_url, $buildkite_agent_zip)
[System.IO.Compression.ZipFile]::ExtractToDirectory($buildkite_agent_zip, $buildkite_agent_root)
Remove-Item $buildkite_agent_zip
New-Item "${buildkite_agent_root}\hooks" -ItemType "directory" -Force
New-Item "${buildkite_agent_root}\plugins" -ItemType "directory" -Force
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";${buildkite_agent_root}"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH, "Machine")

## Remove empty folders (";;") from PATH.
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine").replace(";;", ";")
[Environment]::SetEnvironmentVariable("PATH", $env:PATH, "Machine")

## Create a service wrapper script for the Buildkite agent.
Write-Host "Creating Buildkite agent environment hook..."
$buildkite_environment_hook = @"
SET BUILDKITE_ARTIFACT_UPLOAD_DESTINATION=gs://bazel-buildkite-artifacts/%BUILDKITE_JOB_ID%
SET BUILDKITE_GS_ACL=publicRead
SET JAVA_HOME=${env:JAVA_HOME}
SET PATH=${env:PATH}
SET TEMP=D:\temp
SET TMP=D:\temp
"@
[System.IO.File]::WriteAllLines("${buildkite_agent_root}\hooks\environment.bat", $buildkite_environment_hook)

## Create an unprivileged user that we'll run the Buildkite agent as.
# The password used here is not relevant for security, as the server is behind a
# firewall blocking all incoming access and locally we run the CI jobs as that
# user anyway.
Write-Host "Creating Buildkite service user..."
$buildkite_username = "buildkite"
$buildkite_password = "Bu1ldk1t3"
$buildkite_secure_password = ConvertTo-SecureString $buildkite_password -AsPlainText -Force
New-LocalUser -Name $buildkite_username -Password $buildkite_secure_password -UserMayNotChangePassword

## Create the Buildkite Monitor script.
Write-Host "Creating Buildkite Monitor script..."
$buildkite_monitor_script = @"
`$ErrorActionPreference = "Stop"
`$ConfirmPreference = "None"
`$buildkite_username = "${buildkite_username}"

Write-Host "Terminating all processes belonging to the `${buildkite_username} user..."
& taskkill /FI "username eq `${buildkite_username}" /T /F
Start-Sleep -Seconds 1

Write-Host "Recreating fresh temporary directory D:\temp..."
Remove-Item -Recurse -Force "D:\temp"
New-Item -Type Directory "D:\temp"
Add-NTFSAccess -Path "D:\temp" -Account BUILTIN\Users -AccessRights Write

Write-Host "Deleting home directory of the `${buildkite_username} user..."
Get-CimInstance Win32_UserProfile | Where LocalPath -EQ "C:\Users\`${buildkite_username}" | Remove-CimInstance
if ( Test-Path "C:\Users\`${buildkite_username}" ) {
  Throw "The home directory of the `${buildkite_username} user could not be deleted."
}

Write-Host "Starting Buildkite agent as user `${buildkite_username}..."
& nssm start "buildkite-agent"

Write-Host "Waiting for Buildkite agent to exit..."
While ((Get-Service "buildkite-agent").Status -eq "Running") { Start-Sleep -Seconds 1 }

Write-Host "Buildkite agent has exited."
"@
[System.IO.File]::WriteAllLines("${buildkite_agent_root}\buildkite-monitor.ps1", $buildkite_monitor_script)

## Allow the Buildkite agent to store SSH host keys in this folder.
Write-Host "Creating C:\buildkite\.ssh folder..."
New-Item "c:\buildkite\.ssh" -ItemType "directory"
Add-NTFSAccess -Path "c:\buildkite\.ssh" -Account BUILTIN\Users -AccessRights Write

Write-Host "Creating C:\buildkite\logs folder..."
New-Item "c:\buildkite\logs" -ItemType "directory"
Add-NTFSAccess -Path "c:\buildkite\logs" -Account BUILTIN\Users -AccessRights Write

## Create a service for the Buildkite agent.
& choco install nssm

Write-Host "Creating Buildkite Monitor service..."
nssm install "buildkite-monitor" `
    "c:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" `
    "c:\buildkite\buildkite-monitor.ps1"
nssm set "buildkite-monitor" "AppDirectory" "c:\buildkite"
nssm set "buildkite-monitor" "DisplayName" "Buildkite Monitor"
nssm set "buildkite-monitor" "Start" "SERVICE_DEMAND_START"
nssm set "buildkite-monitor" "AppExit" "Default" "Restart"
nssm set "buildkite-monitor" "AppRestartDelay" "3000"
nssm set "buildkite-monitor" "AppStdout" "c:\buildkite\logs\buildkite-monitor.log"
nssm set "buildkite-monitor" "AppStderr" "c:\buildkite\logs\buildkite-monitor.log"
nssm set "buildkite-monitor" "AppRotateFiles" "1"
nssm set "buildkite-monitor" "AppRotateSeconds" 86400
nssm set "buildkite-monitor" "AppRotateBytes" 1048576

Write-Host "Creating Buildkite Agent service..."
nssm install "buildkite-agent" `
    "c:\buildkite\buildkite-agent.exe" `
    "start"
nssm set "buildkite-agent" "AppDirectory" "c:\buildkite"
nssm set "buildkite-agent" "DisplayName" "Buildkite Agent"
nssm set "buildkite-agent" "Start" "SERVICE_DEMAND_START"
nssm set "buildkite-agent" "ObjectName" ".\${buildkite_username}" "$buildkite_password"
nssm set "buildkite-agent" "AppExit" "Default" "Exit"
nssm set "buildkite-agent" "AppStdout" "c:\buildkite\logs\buildkite-agent.log"
nssm set "buildkite-agent" "AppStderr" "c:\buildkite\logs\buildkite-agent.log"
nssm set "buildkite-agent" "AppRotateFiles" "1"
nssm set "buildkite-agent" "AppRotateSeconds" 86400
nssm set "buildkite-agent" "AppRotateBytes" 1048576

Write-Host "All done, adding GCESysprep to RunOnce and rebooting..."
Set-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce" -Name "GCESysprep" -Value "c:\Program Files\Google\Compute Engine\sysprep\gcesysprep.bat"
Restart-Computer
