## Stop on action error.
$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

## Load PowerShell support for ZIP files.
Add-Type -AssemblyName "System.IO.Compression.FileSystem"

## Create C:\temp
Write-Host "Creating temporary folder C:\temp..."
if (-Not (Test-Path "c:\temp")) {
  New-Item "c:\temp" -ItemType "directory"
}
[Environment]::SetEnvironmentVariable("TEMP", "C:\temp", "Machine")
[Environment]::SetEnvironmentVariable("TMP", "C:\temp", "Machine")
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
# Write-Host "Installing all available Windows Updates (this can take ~30 minutes)..."
# Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force
# Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
# Install-Module PSWindowsUpdate
# Get-Command -Module PSWindowsUpdate
# Get-WindowsUpdate -Install -AcceptAll -AutoReboot
# This fails with: https://gist.github.com/philwo/010bb5dffc62eccb391cd916c3bee2be
# Add-WUServiceManager -ServiceID 7971f918-a847-4430-9279-4a52d1efe18d
# Get-WindowsUpdate -Install -MicrosoftUpdate -AcceptAll -AutoReboot

## Install Chocolatey
Write-Host "Installing Chocolatey..."
Invoke-Expression ((New-Object Net.WebClient).DownloadString("https://chocolatey.org/install.ps1"))
& choco feature enable -n allowGlobalConfirmation

## Install curl
Write-Host "Installing curl..."
& choco install curl

## Install Git for Windows.
Write-Host "Installing Git for Windows..."
& choco install git --params="'/GitOnlyOnPath'"

## Install MSYS2
Write-Host "Installing MSYS2..."
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
& bash -lc "pacman --noconfirm --needed -S curl zip unzip tar diffutils patch"

## Install the JDK.
Write-Host "Installing JDK 8..."
& choco install jdk8

## Set JAVA_HOME to the path of the installed JDK.
$java = Get-ChildItem "c:\Program Files\Java\jdk*" | Select-Object -Index 0 | foreach { $_.FullName }
Write-Host "Setting JAVA_HOME to ${java}..."
[Environment]::SetEnvironmentVariable("JAVA_HOME", $java, "Machine")
$env:JAVA_HOME = [Environment]::GetEnvironmentVariable("JAVA_HOME", "Machine")

## Install Visual C++ 2015 Build Tools (Update 3).
# Write-Host "Installing Visual C++ 2015 Build Tools..."
# (New-Object Net.WebClient).DownloadFile("http://go.microsoft.com/fwlink/?LinkId=691126", "c:\temp\visualcppbuildtools_full.exe")
# Start-Process -Wait "c:\temp\visualcppbuildtools_full.exe" -ArgumentList "/Passive", "/NoRestart"
# Remove-Item "c:\temp\visualcppbuildtools_full.exe"

## Install Visual C++ 2017 Build Tools.
Write-Host "Installing Visual C++ 2017 Build Tools..."
& choco install microsoft-build-tools
& choco install visualstudio2017-workload-vctools
[Environment]::SetEnvironmentVariable("BAZEL_VC", "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\VC", "Machine")
$env:BAZEL_VC = [Environment]::GetEnvironmentVariable("BAZEL_VC", "Machine")

## Install Python3
Write-Host "Installing Python 3..."
& choco install python3 --params="/InstallDir:C:\python3"

## Install a couple of Python modules required by TensorFlow.
Write-Host "Updating Python packages..."
& "C:\Python3\Scripts\pip.exe" install --upgrade `
    autograd `
    numpy `
    portpicker `
    protobuf `
    pyreadline `
    six `
    wheel

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
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";c:\bazel", "Machine")
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")

## Download the Android NDK and install into C:\android-ndk-r14b.
$android_ndk_url = "https://dl.google.com/android/repository/android-ndk-r14b-windows-x86_64.zip"
$android_ndk_zip = "c:\temp\android_ndk.zip"
$android_ndk_root = "c:\android_ndk"
New-Item $android_ndk_root -ItemType "directory" -Force
(New-Object Net.WebClient).DownloadFile($android_ndk_url, $android_ndk_zip)
[System.IO.Compression.ZipFile]::ExtractToDirectory($android_ndk_zip, $android_ndk_root)
Rename-Item "${android_ndk_root}\android-ndk-r14b" -NewName "r14b"
[Environment]::SetEnvironmentVariable("ANDROID_NDK_HOME", "${android_ndk_root}\r14b", "Machine")
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
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";${buildkite_agent_root}", "Machine")
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")

## Create a service for the Buildkite agent.
# Some hints: https://gist.github.com/fdstevex/52da0d7e5892fe2965eae105b8cf3883
#             https://github.com/buildkite/agent/issues/329
#             https://github.com/kohsuke/winsw
Write-Host "Creating Buildkite Agent service..."
$winsw_url = "https://github.com/kohsuke/winsw/releases/download/winsw-v2.1.2/WinSW.NET4.exe"
$winsw = "${buildkite_agent_root}\buildkite-service.exe"
(New-Object Net.WebClient).DownloadFile($winsw_url, $winsw)
$winsw_config=@"
<configuration>
  <id>buildkite-service</id>
  <name>Buildkite Agent</name>
  <description>The Buildkite CI agent.</description>
  <executable>%BASE%\buildkite-agent.exe</executable>
  <arguments>start</arguments>
  <startmode>Manual</startmode>
  <logmode>roll</logmode>
</configuration>
"@
[System.IO.File]::WriteAllLines("${buildkite_agent_root}\buildkite-service.xml", $winsw_config)
& $winsw install

Write-Host "All done, preparing system for imaging with GCESysprep..."
& GCESysprep
