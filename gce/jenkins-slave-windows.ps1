# This script is executed on every boot. Even though we lack even basic error
# reporting and handling, at least make sure that it is not executed twice.
if (Test-Path "c:\bazel_ci\install_completed.txt") {
  Exit
}

# Stop on action error.
# TODO(dmarting): for executable, we need to check for $LastExitCode each time.
$ErrorActionPreference = "Stop"

if (-Not (Test-Path c:\bazel_ci)) {
  New-Item c:\bazel_ci -type directory
}
Set-Location c:\bazel_ci

# Install Chocolatey
Invoke-Expression ((New-Object Net.WebClient).DownloadString("https://chocolatey.org/install.ps1"))

# Initialize msys
$msysRoot='c:\tools\msys64\'

# Finally initialize and upgrade MSYS2 according to https://msys2.github.io
Write-Host "Initializing MSYS2..."
$msysShell = Join-Path $msysRoot msys2_shell.bat
Start-Process -Wait $msysShell -ArgumentList '-c', exit

$command = 'pacman --noconfirm --needed -Sy bash pacman pacman-mirrors msys2-runtime'
Write-Host "Updating system packages with '$command'..."
Start-Process -Wait $msysShell -ArgumentList '-c', "'$command'"

$command = 'pacman --noconfirm -Su'
Write-Host "Upgrading full system with '$command'..."
Start-Process -Wait $msysShell -ArgumentList '-c', "'$command'"

# Download and install Python
New-Item c:\temp -type directory
(New-Object Net.WebClient).DownloadFile("https://www.python.org/ftp/python/2.7.11/python-2.7.11.amd64.msi",
                                        "c:\temp\python-2.7.11.amd64.msi")
& msiexec /qn TARGETDIR=c:\python_27_amd64\files\ /i c:\temp\python-2.7.11.amd64.msi

[Environment]::SetEnvironmentVariable("Path", $env:Path + ";c:\python_27_amd64\files",
                                      [System.EnvironmentVariableTarget]::Machine)

# Download and install Anaconda3, because python3 is required by TensorFlow on Windows
$anaconda3_tmp_folder = "c:\temp\anaconda3"
New-Item $anaconda3_tmp_folder -type directory -force
$anaconda3_installer = $anaconda3_tmp_folder + "\Anaconda3-4.2.0-Windows-x86_64.exe"
(New-Object Net.WebClient).DownloadFile("https://repo.continuum.io/archive/Anaconda3-4.2.0-Windows-x86_64.exe", $anaconda3_installer)
Start-Process -Wait $anaconda3_installer -ArgumentList "/AddToPath=0? /InstallationType=AllUsers /S /D='C:\Program Files\Anaconda3'"

# Install pyreadline (Windows-compatible Python GNU readline library) and portpicker.
# Required by TensorFlow Python tests (tfdbg).
& "C:\Program Files\Anaconda3\Scripts\pip.exe" install pyreadline portpicker

# Install autograd (needed by TensorFlow)
& "C:\Program Files\Anaconda3\Scripts\pip.exe" install autograd

# Install protobuf (needed by TensorFlow)
& "C:\Program Files\Anaconda3\Scripts\pip.exe" install protobuf

# Install all the Windows software we need:
#   - JDK, because, Bazel is written in Java
#   - NSSM, because that's the easiest way to create services
#   - Chrome, because the default IE setup is way too crippled by security measures
& choco install nssm -y --allow-empty-checksums
& choco install jdk8 -y --allow-empty-checksums
& choco install googlechrome -y --allow-empty-checksums

# Fetch the instance ID from GCE
$webclient=(New-Object Net.WebClient)
$webclient.Headers.Add("Metadata-Flavor", "Google")
$jenkins_node=$webclient.DownloadString("http://metadata/computeMetadata/v1/instance/attributes/jenkins_node")

# Save the Jenkins slave.jar to a suitable location.
Invoke-WebRequest https://ci.bazel.build/jnlpJars/slave.jar -OutFile slave.jar

# Install the necessary packages in msys2
$bash_installer=@'
pacman -Syyu --noconfirm
pacman -S --noconfirm git curl gcc zip unzip zlib-devel isl tar patch
'@
Write-Output $bash_installer | Out-File -Encoding ascii install.sh
# -l is required so that PATH in bash is set properly
& c:\tools\msys64\usr\bin\bash -l /c/bazel_ci/install.sh

# Find the JDK. The path changes frequently, so hardcoding it is not enough.
$java=Get-ChildItem "c:\Program Files\Java\jdk*" | Select-Object -Index 0 | foreach { $_.FullName }

# Get the latest release version number of Bazel
$url = "https://github.com/bazelbuild/bazel/releases/latest"
$req=[system.Net.HttpWebRequest]::Create($url);
$res = $req.getresponse();
$res.Close();
$bazel_version=$res.ResponseUri.AbsolutePath.TrimStart("/bazelbuild/bazel/releases/tag/")

# Download the latest bazel

$folder="c:\bazel_ci\installs\${BAZEL_VERSION}"
$url="https://releases.bazel.build/${BAZEL_VERSION}/release/bazel-${BAZEL_VERSION}-windows-x86_64.exe"
New-Item $folder -type directory -force
(New-Object Net.WebClient).DownloadFile("${url}", "${folder}\bazel.exe")

# Create a junction to the latest release
# The CI machines have Powershell 4 installed, so we cannot use New-Item to
# create a junction, so shell out to mklink.
cmd.exe /C mklink /j C:\bazel_ci\installs\latest $folder

# Also use the latest release for bootstrapping
cmd.exe /C mklink /j C:\bazel_ci\installs\bootstrap $folder

# Create the service that runs the Jenkins slave
# We can't execute Java directly because then it mysteriously fails with
# "Sockets error: 10106: create", so we redirect through Powershell
# The path change is needed because Jenkins cannot execute a different git
# binary on different nodes, so we need to simply use "git"
$jnlpUrl = "https://ci.bazel.build/computer/${jenkins_node}/slave-agent.jnlp"
$agent_script=@"
`$env:path="c:\tools\msys64\usr\bin;`$env:path"
cd c:\bazel_ci
# A path name with c:\ in the JNLP URL makes Java hang. I don't know why.
# Jenkins tries to reconnect to the wrong port if the server is restarted.
# -noReconnect makes the agent die, and it is then subsequently restarted by
# Windows because it is a service, and then all is well.
& "${java}\bin\java" -jar c:\bazel_ci\slave.jar -jnlpUrl $jnlpUrl -noReconnect
"@
Write-Output $agent_script | Out-File -Encoding ascii agent_script.ps1

& nssm install bazel_ci powershell c:\bazel_ci\agent_script.ps1
& nssm set bazel_ci AppStdout c:\bazel_ci\stdout.log
& nssm set bazel_ci AppStderr c:\bazel_ci\stderr.log
& nssm start bazel_ci

Write-Output "DONE" | Out-File -Encoding ascii "c:\bazel_ci\install_completed.txt"
