#!/usr/bin/env bash
# Installs the soil agent as a launchd agent that starts at login and
# restarts if it crashes. Run from anywhere:
#   bash install/macos/install.sh
# Remove with:
#   launchctl bootout gui/$(id -u)/com.soiltest.agent && rm ~/Library/LaunchAgents/com.soiltest.agent.plist
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONFIG="$REPO_ROOT/config.toml"
LABEL="com.soiltest.agent"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [[ ! -f "$CONFIG" ]]; then
  cp "$REPO_ROOT/config.example.toml" "$CONFIG"
  echo "Created $CONFIG. Edit the paths in it, then run this script again."
  exit 1
fi

PYTHON="$(command -v python3)"
"$PYTHON" -m pip install --user -r "$REPO_ROOT/requirements.txt"

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>-m</string>
    <string>soil_agent</string>
    <string>--config</string>
    <string>$CONFIG</string>
  </array>
  <key>WorkingDirectory</key><string>$REPO_ROOT</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/soil_agent.out.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/soil_agent.err.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed and running. If the inbox is in Desktop/Documents/Downloads, macOS will ask"
echo "to allow python3 access the first time. Approve it, or grant Full Disk Access to python3."
