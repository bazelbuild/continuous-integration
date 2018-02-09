# Stop on action error.
$ErrorActionPreference = "Stop"

# Install Chocolatey
Invoke-Expression ((New-Object Net.WebClient).DownloadString("https://chocolatey.org/install.ps1"))

if (-Not (Test-Path c:\bazel_ci)) {
  New-Item c:\bazel_ci -type directory
}
Set-Location c:\bazel_ci

# TODO(philwo) remove if it turns out we don't need Chocolatey.
# Upgrade Chocolatey.
# Write-Host "Updating Chocolatey..."
# & "C:\ProgramData\chocolatey\choco.exe" upgrade chocolatey
# & "C:\ProgramData\chocolatey\choco.exe" upgrade all

# Update MSYS2 once.
Write-Host "Updating MSYS2 packages (round 1)..."
Start-Process -Wait "c:\msys64\msys2_shell.cmd" -ArgumentList "-c", "pacman --noconfirm -Syuu"

# Update again, in case the first round only upgraded core packages.
Write-Host "Updating MSYS2 packages (round 2)..."
Start-Process -Wait "c:\msys64\msys2_shell.cmd" -ArgumentList "-c", "pacman --noconfirm -Syuu"

# Install a couple of Python modules required by TensorFlow.
Write-Host "Updating Python packages..."
& "C:\Python3\Scripts\pip.exe" install --upgrade `
    autograd `
    numpy `
    portpicker `
    protobuf `
    pyreadline `
    six `
    wheel

# Fetch the instance ID from GCE.
Write-Host "Fetching instance ID from GCE..."
$webclient = (New-Object Net.WebClient)
$webclient.Headers.Add("Metadata-Flavor", "Google")
$jenkins_node = $webclient.DownloadString("http://metadata/computeMetadata/v1/instance/attributes/jenkins_node")

# Get the latest release version number of Bazel.
Write-Host "Grabbing latest Bazel version number from GitHub..."
$url = "https://github.com/bazelbuild/bazel/releases/latest"
$req = [system.Net.HttpWebRequest]::Create($url);
$res = $req.getresponse();
$res.Close();
$bazel_version = $res.ResponseUri.AbsolutePath.TrimStart("/bazelbuild/bazel/releases/tag/")

# Download the latest bazel.
$folder = "c:\bazel_ci\installs\${bazel_version}"
if (-Not (Test-Path "${folder}\bazel.exe")) {
  Write-Host "Downloading Bazel ${bazel_version}..."
  $url = "https://releases.bazel.build/${bazel_version}/release/bazel-${bazel_version}-without-jdk-windows-x86_64.exe"
  New-Item $folder -type directory -force
  (New-Object Net.WebClient).DownloadFile("${url}", "${folder}\bazel.exe")
} else {
  Write-Host "Bazel ${bazel_version} was already downloaded, skipping..."
}

# Create a junction to the latest release.
Write-Host "Creating helper junctions..."
$latest_folder = "C:\bazel_ci\installs\latest"
if (Test-Path $latest_folder) {
  Remove-Item -Force -Recurse $latest_folder
}
New-Item -ItemType Junction $latest_folder -Value $folder

$bootstrap_folder = "C:\bazel_ci\installs\bootstrap"
if (Test-Path $bootstrap_folder) {
  Remove-Item -Force -Recurse $bootstrap_folder
}
New-Item -ItemType Junction $bootstrap_folder -Value $folder

# Find the JDK. The path changes frequently, so hardcoding it is not enough.
$java = Get-ChildItem "c:\Program Files\Java\jdk*" | Select-Object -Index 0 | foreach { $_.FullName }
Write-Host "Found latest JDK at ${java}..."

# Save the Jenkins slave.jar to a suitable location.
Write-Host "Downloading https://ci.bazel.build/jnlpJars/slave.jar..."
Invoke-WebRequest https://ci.bazel.build/jnlpJars/slave.jar -OutFile slave.jar

# Create the service that runs the Jenkins slave
# We can't execute Java directly because then it mysteriously fails with
# "Sockets error: 10106: create", so we redirect through Powershell
# The path change is needed because Jenkins cannot execute a different git
# binary on different nodes, so we need to simply use "git"
Write-Host "Creating Jenkins slave startup script..."
$jnlpUrl = "https://ci.bazel.build/computer/${jenkins_node}/slave-agent.jnlp"
$agent_script = @"
`$env:path="c:\tools\msys64\usr\bin;`$env:path"
cd c:\bazel_ci
# A path name with c:\ in the JNLP URL makes Java hang. I don't know why.
# Jenkins tries to reconnect to the wrong port if the server is restarted.
# -noReconnect makes the agent die, and it is then subsequently restarted by
# Windows because it is a service, and then all is well.
& "${java}\bin\java" -jar c:\bazel_ci\slave.jar -jnlpUrl ${jnlpUrl} -noReconnect
"@
Write-Output $agent_script | Out-File -Encoding ascii agent_script.ps1

Write-Host "Creating Jenkins slave service..."
& nssm install bazel_ci powershell c:\bazel_ci\agent_script.ps1
& nssm set bazel_ci AppStdout c:\bazel_ci\stdout.log
& nssm set bazel_ci AppStderr c:\bazel_ci\stderr.log
& nssm start bazel_ci
