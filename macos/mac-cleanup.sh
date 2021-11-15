# Example how to setup a clean-up step for the Buildkite Agent on macOS

# Create a "buildkite" user first with a clean home directory.
#
# The agent will run as this "buildkite" user and will be monitored by a launchd
# service that runs a "buildkite-wrapper" script, which will launch the actual
# agent and clean-up after each job. (launchd will restart the service automatically
# after it exits.)

cat > /Library/LaunchDaemons/de.geheimspeicher.buildkite-agent.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>de.geheimspeicher.buildkite-agent</string>
  <key>WorkingDirectory</key>
  <string>/usr/local/bin</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/buildkite-wrapper</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ProcessType</key>
  <string>Interactive</string>
  <key>ThrottleInterval</key>
  <integer>10</integer>
  <key>StandardOutPath</key>
  <string>/usr/local/var/log/buildkite-agent.log</string>
  <key>StandardErrorPath</key>
  <string>/usr/local/var/log/buildkite-agent.log</string>
</dict>
</plist>
EOF

chown root:wheel /Library/LaunchDaemons/de.geheimspeicher.buildkite-agent.plist
chmod 0644 /Library/LaunchDaemons/de.geheimspeicher.buildkite-agent.plist

cat > /usr/local/bin/buildkite-wrapper <<'EOF'
#!/bin/bash

set -x

OS_VERSION=$(sw_vers -productVersion)
MACHINE_TYPE=$(system_profiler SPHardwareDataType | grep 'Model Name' | cut -d':' -f2 | tr -d ' ' | tr '[:upper:]' '[:lower:]')
BUILDKITE_AGENT_TAGS="queue=macos,kind=worker,os=macos,os-version=${OS_VERSION},machine-type=${MACHINE_TYPE}"

# Kill all processes that might still be running from the last build.
killall -9 -u buildkite

# Remove temporary files.
find /private/tmp -user buildkite -delete

# Delete all Bazel output bases (but leave the cache and install bases).
find /private/var/tmp/_bazel_buildkite -mindepth 1 -maxdepth 1 ! -name 'cache' ! -name 'install' -exec rm -rf {} +

# Delete Bazel install bases older than 7 days.
find /private/var/tmp/_bazel_buildkite/install -mindepth 1 -maxdepth 1 -mtime +7 -exec rm -rf {} +

# Delete the user's cache and temporary files.
find /var/folders -user buildkite -delete

# Completely remove all temporary files, output bases, repo cache, install bases, ...
# find /private/var/tmp -user buildkite -delete

# Completely reset the user's home directory to a known state.
/usr/local/bin/rsync -aAX --delete --ignore-errors /Users/buildkite-fresh/ /Users/buildkite/

sudo -H -u buildkite env \
    PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
    BUILDKITE_AGENT_DISCONNECT_AFTER_JOB="true" \
    BUILDKITE_AGENT_EXPERIMENT="git-mirrors" \
    BUILDKITE_AGENT_NAME="%hostname" \
    BUILDKITE_AGENT_TAGS="${BUILDKITE_AGENT_TAGS}" \
    BUILDKITE_BUILD_PATH="/Users/buildkite/builds" \
    BUILDKITE_CONFIG_PATH="/usr/local/etc/buildkite-agent/buildkite-agent.cfg" \
    BUILDKITE_GIT_MIRRORS_PATH="/usr/local/var/bazelbuild" \
    BUILDKITE_GIT_CLONE_MIRROR_FLAGS="-v --bare" \
    /usr/local/bin/buildkite-agent start

# Just to make really sure that nothing stays running after a job, run 'killall' now.
killall -9 -u buildkite
EOF

chown ci:staff /usr/local/bin/buildkite-wrapper
chmod 0755 /usr/local/bin/buildkite-wrapper

launchctl load /Library/LaunchDaemons/de.geheimspeicher.buildkite-agent.plist
