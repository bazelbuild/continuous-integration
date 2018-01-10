# Creating a new Windows VM image for Bazel's CI

The key thing to keep in mind is that the Windows setup for Jenkins has nothing magic about it
that makes it a Jenkins slave VM. It's just a normal Windows setup with a few pre-installed tools
that you would install on a workstation anyway. The Jenkins-specific setup is then handled
completely automatic by the PowerShell script in `gce/jenkins-slave-windows-2016.ps1`.

## Necessary steps
- Create a new GCE VM with Windows Server 2016.
- Temporarily enable RDP access to the VM via:
  - `gcloud compute firewall-rules create $USER-rdp --allow=tcp:3389,udp:3389 --source-ranges=$(curl v4.ifconfig.co)/32`
- Set a new Windows password, note it somewhere and connect via RDP.

- Server Manager -> Configure this local server
  - Deactivate Windows Firewall.
  - Deactivate Windows Defender.
  - Deactivate IE Enhanced Security Configuration.
  - Set time zone to Europe/Berlin.

- Download and install Google Chrome. Pin to taskbar, unpin IE.

- Settings -> Update & security
  - For developers -> [x] Developer mode. Click all three "Apply" buttons below.
  - Windows Update -> Advanced options -> Check "Give me updates for other Microsoft products".
  - Windows Update -> Check updates, then install all updates.
    - Reboot if necessary.
    - Repeat until no more updates are found.

- Go to https://www.python.org/downloads/windows/
  - Download latest stable Python 3.x (64-Bit).
  - Start installation.
    - Check "Install launcher for all users".
    - Check "Add Python to PATH".
    - Customize installation, check all boxes.
    - Check "Install for all users".
    - Customize install location: C:\Python3
    - When setup is complete, click "Disable path length limit", then close setup.

- Go to http://www.msys2.org/
  - Download latest x86_64 msys2 setup.
  - Install to C:\msys64.
  - Launch msys2 shell from installer, run "pacman -Syuu", forcibly close terminal window when prompted.
  - Launch "MSYS2 MinGW 64-bit" shell, run "pacman -Syuu", install all updates.
  - Run "pacman -S git curl zip unzip gcc zlib-devel isl tar patch".

- Go to http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html
  - Download and install latest "Windows x64" JDK 8.

- Go to http://landinghub.visualstudio.com/visual-cpp-build-tools
  - Download "Visual C++ Build Tools 2015".
  - Start installation, choose "Custom", select all options, install.

- Go to https://nssm.cc/download
  - Download "nssm 2.24-101-g897c7ad (2017-04-26)" or later build.
  - Create new folder: "C:\Program Files\nssm".
  - Extract nssm.exe from the download ZIP file's "win64" folder into the just created folder.

- Start -> Search for "path" -> Choose "Edit the system environment variables"
  - Click "Environment Variables". Do the following actions in the lower "System variables" part of the UI.
  - Add "C:\Program Files\nssm" to the PATH variable.
  - Set BAZEL_VC to "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC"
  - Set BAZEL_SH to "C:\msys64\usr\bin\bash.exe"
  - Set JAVA_HOME to "C:\Program Files\Java\jdk1.8.0_152" (or the latest version installed)

- Start -> Type "GCESysprep", run it.
  - The system will shut down and prepare itself for being used as an image to create new VMs.
