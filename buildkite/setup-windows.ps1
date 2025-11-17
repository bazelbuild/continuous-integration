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

## Install curl
Write-Host "Installing curl..."
# FYI: choco installs curl.exe in C:\ProgramData\chocolatey\bin (which is on the PATH).
& choco install curl

## Install LLVM/Clang
Write-Host "Installing llvm..."
# FYI: choco installs clang in C:\Program Files\LLVM\bin (which is not on the PATH).
& choco install llvm
[Environment]::SetEnvironmentVariable("BAZEL_LLVM", "C:\Program Files\LLVM", "Machine")
$env:BAZEL_LLVM = [Environment]::GetEnvironmentVariable("BAZEL_LLVM", "Machine")

## Install MSYS2
Write-Host "Installing MSYS2..."
& choco install msys2
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";C:\tools\msys64\usr\bin;C:\tools\msys64\mingw64\bin"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH, "Machine")

[Environment]::SetEnvironmentVariable("BAZEL_SH", "C:\tools\msys64\usr\bin\bash.exe", "Machine")
$env:BAZEL_SH = [Environment]::GetEnvironmentVariable("BAZEL_SH", "Machine")
Set-Alias bash "c:\tools\msys64\usr\bin\bash.exe"

## Install MSYS2 packages required by Bazel.
Write-Host "Installing required MSYS2 packages..."
& bash -lc "pacman --noconfirm -Syuu"
& bash -lc "pacman --noconfirm --needed -S curl zip unzip gcc tar diffutils patch perl mingw-w64-x86_64-gcc ed"

## Install Git for Windows.
Write-Host "Installing Git for Windows..."
# FYI: choco adds "C:\Program Files\Git\cmd" to global PATH.
& choco install git --params "'/GitOnlyOnPath'"
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")
# Don't convert the line endings when cloning the repository because that could break some tests
& git config --system core.autocrlf false
# Turn on long path support on Windows
& git config --system core.longpaths true

# Function to install Azul Zulu JDK
function InstallAzulZuluJDK($filename, $rootPath) {
    $url = "https://cdn.azul.com/zulu/bin/${filename}"
    $zip = "c:\temp\${filename}"
    $extractedPath = "c:\temp\" + [IO.Path]::GetFileNameWithoutExtension($zip)
    $destination = "${rootPath}"

    (New-Object Net.WebClient).DownloadFile($url, $zip)
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, "c:\temp")
    Move-Item $extractedPath -Destination $destination
    Remove-Item $zip
}

## Install Azul Zulu JDK 11
Write-Host "Installing Azul Zulu JDK 11..."
InstallAzulZuluJDK "zulu11.52.13-ca-jdk11.0.13-win_x64.zip" "c:\openjdk11"

## Install Azul Zulu JDK 21
Write-Host "Installing Azul Zulu JDK 21..."
InstallAzulZuluJDK "zulu21.28.85-ca-jdk21.0.0-win_x64.zip" "c:\openjdk21"

## Set default JDK to Zulu 21
$jdk_root = "c:\openjdk21"
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";${jdk_root}\bin"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH, "Machine")
$env:JAVA_HOME = $jdk_root
[Environment]::SetEnvironmentVariable("JAVA_HOME", $env:JAVA_HOME, "Machine")

## Install Visual C++ 2017 Build Tools.
Write-Host "Installing Visual C++ 2017 Build Tools..."
& choco install visualstudio2017buildtools
& choco install visualstudio2017-workload-vctools --params "--add Microsoft.VisualStudio.Component.VC.Tools.ARM --add Microsoft.VisualStudio.Component.VC.Tools.ARM64"

## Install Visual C++ 2019 Build Tools.
Write-Host "Installing Visual C++ 2019 Build Tools..."
& choco install visualstudio2019buildtools
& choco install visualstudio2019-workload-vctools --params "--add Microsoft.VisualStudio.Component.VC.Tools.ARM --add Microsoft.VisualStudio.Component.VC.Tools.ARM64"

## Install Visual C++ 2022 Build Tools.
Write-Host "Installing Visual C++ 2022 Build Tools..."
$tool_version="14.39.17.9."
& choco install visualstudio2022buildtools
# & choco install visualstudio2022-workload-vctools --params "--add Microsoft.VisualStudio.Component.VC.Tools.ARM --add Microsoft.VisualStudio.Component.VC.Tools.ARM64"
& choco install visualstudio2022-workload-vctools --params "--add Microsoft.VisualStudio.Component.VC.${tool_version}x86.x64 --add Microsoft.VisualStudio.Component.VC.${tool_version}ARM --add Microsoft.VisualStudio.Component.VC.${tool_version}ARM64"

## Prevent mysteirous failure caused by newer version of MSVC (14.40.33810). See https://github.com/bazelbuild/bazel/issues/22656
## Remove directories under C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC that don't match the specified version.
$versionPrefix = "14.39" # The installed version doesn't match the version in the component name, so we need to use a substring match.
$msvcPath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC"
$directories = Get-ChildItem -Path $msvcPath -Directory | Where-Object { $_.Name -notlike "$versionPrefix*" }
foreach ($directory in $directories) {
    $directoryPath = Join-Path -Path $msvcPath -ChildPath $directory.Name
    Write-Host "Deleting $directoryPath"
    Remove-Item -Path $directoryPath -Recurse -Force
}

[Environment]::SetEnvironmentVariable("BAZEL_VC", "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC", "Machine")
$env:BAZEL_VC = [Environment]::GetEnvironmentVariable("BAZEL_VC", "Machine")

## Install Python3
Write-Host "Installing Python 3..."
& choco install python312 --params "/InstallDir:C:\python3"
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine")
New-Item -ItemType SymbolicLink -Path "C:\python3\python3.exe" -Target "C:\python3\python.exe"

## Install a couple of Python modules required by TensorFlow.
Write-Host "Updating Python package management tools..."
& "C:\Python3\python.exe" -m pip install --upgrade pip setuptools wheel

Write-Host "Installing Python packages..."
& "C:\Python3\Scripts\pip.exe" install --upgrade `
    autograd `
    numpy `
    portpicker `
    protobuf `
    pyreadline3 `
    six `
    requests `
    pyyaml `
    keras_applications `
    keras_preprocessing `
    pywin32

## Get the latest release version number of Bazelisk.
Write-Host "Grabbing latest Bazelisk version number from GitHub..."
$url = "https://github.com/bazelbuild/bazelisk/releases/latest"
$req = [system.Net.HttpWebRequest]::Create($url)
$res = $req.getresponse()
$res.Close()
$bazelisk_version = $res.ResponseUri.AbsolutePath.TrimStart("/bazelbuild/bazelisk/releases/tag/")

## Download the latest Bazelisk.
Write-Host "Downloading Bazelisk ${bazelisk_version}..."
$bazelisk_url = "https://github.com/bazelbuild/bazelisk/releases/download/${bazelisk_version}/bazelisk-windows-amd64.exe"
New-Item "c:\bazel" -ItemType "directory" -Force
(New-Object Net.WebClient).DownloadFile($bazelisk_url, "c:\bazel\bazel.exe")
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";c:\bazel"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH, "Machine")

## Download the Android NDK r15c and install into C:\android-ndk\r15c.
Write-Host "Installing Android NDK r15c..."
$android_ndk_url = "https://dl.google.com/android/repository/android-ndk-r15c-windows-x86_64.zip"
$android_ndk_zip = "c:\temp\android_ndk.zip"
$android_ndk_root = "c:\android_ndk"
New-Item $android_ndk_root -ItemType "directory" -Force
(New-Object Net.WebClient).DownloadFile($android_ndk_url, $android_ndk_zip)
[System.IO.Compression.ZipFile]::ExtractToDirectory($android_ndk_zip, $android_ndk_root)
Rename-Item "${android_ndk_root}\android-ndk-r15c" -NewName "r15c"
Remove-Item $android_ndk_zip

Write-Host "Installing Android NDK r25b..."
## Download the Android NDK r25b and install into C:\android-ndk\r25b.
$android_ndk_url = "https://dl.google.com/android/repository/android-ndk-r25b-windows.zip"
$android_ndk_zip = "c:\temp\android_ndk.zip"
$android_ndk_root = "c:\android_ndk"
New-Item $android_ndk_root -ItemType "directory" -Force
(New-Object Net.WebClient).DownloadFile($android_ndk_url, $android_ndk_zip)
[System.IO.Compression.ZipFile]::ExtractToDirectory($android_ndk_zip, $android_ndk_root)
Rename-Item "${android_ndk_root}\android-ndk-r25b" -NewName "r25b"
Remove-Item $android_ndk_zip

## Set the ANDROID_NDK_HOME environment variable to r15c.
[Environment]::SetEnvironmentVariable("ANDROID_NDK_HOME", "${android_ndk_root}\r15c", "Machine")
$env:ANDROID_NDK_HOME = [Environment]::GetEnvironmentVariable("ANDROID_NDK_HOME", "Machine")

## Download the Android SDK and install into C:\android_sdk.
$android_sdk_url = "https://dl.google.com/android/repository/commandlinetools-win-7302050_latest.zip"
$android_sdk_zip = "c:\temp\android_sdk.zip"
$android_sdk_root = "c:\android_sdk"
$android_sdk_tools_root = "c:\android_sdk\cmdline-tools"
New-Item $android_sdk_root -ItemType "directory" -Force
New-Item $android_sdk_tools_root -ItemType "directory" -Force
(New-Object Net.WebClient).DownloadFile($android_sdk_url, $android_sdk_zip)
[System.IO.Compression.ZipFile]::ExtractToDirectory($android_sdk_zip, $android_sdk_tools_root)
Rename-Item "${android_sdk_tools_root}\cmdline-tools" -NewName "latest"
[Environment]::SetEnvironmentVariable("ANDROID_HOME", $android_sdk_root, "Machine")
$env:ANDROID_HOME = [Environment]::GetEnvironmentVariable("ANDROID_HOME", "Machine")
Remove-Item $android_sdk_zip

## Accept the Android SDK license agreement.
New-Item "${android_sdk_root}\licenses" -ItemType "directory" -Force
Add-Content -Value "`nd56f5187479451eabf01fb78af6dfcb131a6481e" -Path "${android_sdk_root}\licenses\android-sdk-license" -Encoding ASCII
Add-Content -Value "`n24333f8a63b6825ea9c5514f83c2829b004d1fee" -Path "${android_sdk_root}\licenses\android-sdk-license" -Encoding ASCII
Add-Content -Value "`nd975f751698a77b662f1254ddbeed3901e976f5a" -Path "${android_sdk_root}\licenses\intel-android-extra-license" -Encoding ASCII

## Install all required Android SDK components.
& "${android_sdk_tools_root}\latest\bin\sdkmanager.bat" "platform-tools"
& "${android_sdk_tools_root}\latest\bin\sdkmanager.bat" "build-tools;28.0.2"
& "${android_sdk_tools_root}\latest\bin\sdkmanager.bat" "build-tools;30.0.3"
& "${android_sdk_tools_root}\latest\bin\sdkmanager.bat" "platforms;android-24"
& "${android_sdk_tools_root}\latest\bin\sdkmanager.bat" "platforms;android-28"
& "${android_sdk_tools_root}\latest\bin\sdkmanager.bat" "platforms;android-29"
& "${android_sdk_tools_root}\latest\bin\sdkmanager.bat" "platforms;android-30"
& "${android_sdk_tools_root}\latest\bin\sdkmanager.bat" "platforms;android-31"
& "${android_sdk_tools_root}\latest\bin\sdkmanager.bat" "platforms;android-32"
& "${android_sdk_tools_root}\latest\bin\sdkmanager.bat" "extras;android;m2repository"

## Download and unpack our Git snapshot.
Write-Host "Downloading Git snapshot..."
$bazelbuild_url = "https://storage.googleapis.com/bazel-git-mirror/bazelbuild-mirror.zip"
$bazelbuild_zip = "c:\temp\bazelbuild-mirror.zip"
$bazelbuild_root = "c:\buildkite"
(New-Object Net.WebClient).DownloadFile($bazelbuild_url, $bazelbuild_zip)
Write-Host "Unpacking Git snapshot..."
Expand-Archive -LiteralPath $bazelbuild_zip -DestinationPath $bazelbuild_root -Force
Remove-Item $bazelbuild_zip

## Download and install the Buildkite agent.
Write-Host "Grabbing latest Buildkite Agent version number from GitHub..."
$url = "https://github.com/buildkite/agent/releases/latest"
$req = [system.Net.HttpWebRequest]::Create($url)
$res = $req.getresponse()
$res.Close()
$buildkite_agent_version = $res.ResponseUri.AbsolutePath.TrimStart("/buildkite/agent/releases/tag/v")

Write-Host "Downloading Buildkite agent..."
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

## Create an unprivileged user that we'll run the Buildkite agent as.
# The password used here is not relevant for security, as the server is behind a
# firewall blocking all incoming access and locally we run the CI jobs as that
# user anyway.
Write-Host "Creating Buildkite service user..."
$buildkite_username = "b"
$buildkite_password = "Bu1ldk1t3"
$buildkite_secure_password = ConvertTo-SecureString $buildkite_password -AsPlainText -Force
New-LocalUser -Name $buildkite_username -Password $buildkite_secure_password -UserMayNotChangePassword
Add-LocalGroupMember -Group "Administrators" -Member $buildkite_username
Add-NTFSAccess -Path "C:\buildkite" -Account "b" -AccessRights FullControl

## Allow the Buildkite agent to store SSH host keys in this folder.
Write-Host "Creating C:\buildkite\.ssh folder..."
New-Item "c:\buildkite\.ssh" -ItemType "directory"

Write-Host "Creating C:\buildkite\logs folder..."
New-Item "c:\buildkite\logs" -ItemType "directory"

## Create a service for the Buildkite agent.
& choco install nssm

Write-Host "Creating Buildkite Agent service..."
nssm install "buildkite-agent" `
    "c:\buildkite\buildkite-agent.exe" `
    "start"
nssm set "buildkite-agent" "AppDirectory" "c:\buildkite"
nssm set "buildkite-agent" "DisplayName" "Buildkite Agent"
nssm set "buildkite-agent" "Start" "SERVICE_DEMAND_START"
nssm set "buildkite-agent" "ObjectName" ".\${buildkite_username}" "$buildkite_password"
nssm set "buildkite-agent" "AppExit" "Default" "Exit"
nssm set "buildkite-agent" "AppStdout" "COM1"
nssm set "buildkite-agent" "AppStderr" "COM1"

## Setup pagefile.sys, because otherwise we might run out of memory.
## The JVM uses 25% of the physical RAM as its default heap size and doesn't return free memory
## to the operating system. Windows doesn't overcommit memory, so we might get "unlucky" during
## some CI runs and run out of available heap space. Setting up a pagefile.sys is a hack to give
## Windows some breathing room, while we figure out how to use a more reasonable default heap size
## in Bazel.
$pagefile = Get-WmiObject -Query "SELECT * FROM Win32_PageFileSetting";
$pagefile.InitialSize = 4 * 1024;
$pagefile.MaximumSize = 64 * 1024;
$pagefile.Put();

### Install security updates
# 1. Install the module (if not already present in the base image)
if (-not (Get-Module -ListAvailable -Name PSWindowsUpdate)) {
    Write-Output "Installing PSWindowsUpdate module..."
    Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope CurrentUser
    Install-Module -Name PSWindowsUpdate -Force -Scope CurrentUser -SkipPublisherCheck
}

# 2. Import the module
Import-Module PSWindowsUpdate

# 3. Install only 'Security Updates'
# -AcceptAll: Auto-accepts EULAs
# -IgnoreReboot: Prevents the VM from rebooting mid-script
# -MicrosoftUpdate: Checks against MS servers (useful if WSUS isn't configured)
Write-Output "Checking for and installing Security Updates..."
$Results = Install-WindowsUpdate -MicrosoftUpdate -Category "Security Updates" -AcceptAll -IgnoreReboot -Verbose

# 4. Check if a reboot is actually required (so you can handle it)
if ($Results.RebootRequired -contains $true) {
    Write-Warning "A reboot is required to complete security updates."
}

Write-Host "All done, rebooting..."

$port = New-Object System.IO.Ports.SerialPort COM1,9600,None,8,one
$port.Open()
$port.WriteLine("[setup-windows.ps1]: Setup windows done, rebooting...")
$port.Close()

Restart-Computer

