#!/bin/bash
# SmartHome — Launch backend and frontend in separate terminal tabs.
# macOS: requires iTerm2 or Terminal.app
# Linux: requires gnome-terminal or xfce4-terminal

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== SmartHome ==="

# Detect terminal emulator
if command -v osascript &>/dev/null && [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  osascript -e "tell app \"Terminal\"
    do script \"cd '$SCRIPT_DIR/python' && python3 start_services.py\"
  end tell"

  sleep 2

  osascript -e "tell app \"Terminal\"
    do script \"cd '$SCRIPT_DIR/web' && npm run dev:h5\"
  end tell"
elif command -v gnome-terminal &>/dev/null; then
  # Linux — GNOME
  gnome-terminal -- bash -c "cd '$SCRIPT_DIR/python' && python3 start_services.py; exec bash" &
  sleep 2
  gnome-terminal -- bash -c "cd '$SCRIPT_DIR/web' && npm run dev:h5; exec bash" &
elif command -v xfce4-terminal &>/dev/null; then
  # Linux — XFCE
  xfce4-terminal --command="bash -c 'cd \"$SCRIPT_DIR/python\" && python3 start_services.py; exec bash'" &
  sleep 2
  xfce4-terminal --command="bash -c 'cd \"$SCRIPT_DIR/web\" && npm run dev:h5; exec bash'" &
else
  echo "Could not detect a supported terminal emulator."
  echo "Run manually:"
  echo ""
  echo "  Terminal 1: cd $SCRIPT_DIR/python && python3 start_services.py"
  echo "  Terminal 2: cd $SCRIPT_DIR/web && npm run dev:h5"
  exit 1
fi

echo "Backend starting on http://localhost:8010"
echo "Frontend starting on http://localhost:5177"
