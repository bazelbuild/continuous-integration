New-Item c:\bazel_ci -type directory
Set-Location c:\bazel_ci
# First install Chocolatey...
Invoke-Expression ((New-Object Net.WebClient).DownloadString("https://chocolatey.org/install.ps1"))

# Then all the software we need:
#   - msys2 because Bazel currently depends on it
#   - JDK, because, well, Bazel is written in Java
#   - NSSM, because that's the easiest way to create services
& choco install msys2 -y
& choco install nssm -y
& choco install jdk8 -y

# Save the Jenkins slave.jar to a suitable location
Invoke-WebRequest http://jenkins/jnlpJars/slave.jar -OutFile slave.jar

# Install the necessary packages in msys2
$bash_installer=@"
pacman -S --noconfirm git
"@
Write-Output $bash_installer | Out-File -Encoding ascii install.sh
# -l is required so that PATH in bash is set properly
& c:\tools\msys64\usr\bin\bash -l /c/bazel_ci/install.sh

# Find the JDK. The path changes frequently, so hardcoding it is not enough.
$java=Get-ChildItem "c:\Program Files\Java\jdk*" | Select-Object -Index 0 | foreach { $_.FullName }

# Fetch the instance ID from GCE
$webclient=(New-Object Net.WebClient)
$webclient.Headers.Add("Metadata-Flavor", "Google")
$jenkins_node=$webclient.DownloadString("http://metadata/computeMetadata/v1/instance/attributes/jenkins_node")
Write-Output $jenkins_node | Out-File -Encoding ascii jenkins_node.txt

# Create the service that runs the Jenkins slave
& nssm install bazel_ci $java\bin\java -jar c:\bazel_ci\slave.jar -jnlpUrl http://jenkins/computer/${jenkins_node}/slave-agent.jnlp
& nssm set bazel_ci AppStdout c:\bazel_ci\stdout.log
& nssm set bazel_ci AppStderr c:\bazel_ci\stderr.log
& nssm start bazel_ci
