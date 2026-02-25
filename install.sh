#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  install.sh  —  FranzCode System Installer
#
#  Run this once to make `franz` available from anywhere.
#  Usage:  bash install.sh
# ─────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_TO="/usr/local/bin/franz"

echo ""
echo "  ╔═══════════════════════════════════╗"
echo "  ║   FranzCode Installer  v1.0       ║"
echo "  ╚═══════════════════════════════════╝"
echo ""

# ── Check Python ──────────────────────────────────────────────
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo "  ❌  Python 3 is required. Install from https://python.org"
    exit 1
fi

PY_VER=$($PY --version 2>&1)
echo "  ✔  Found: $PY_VER"

# ── Make the franz script executable ─────────────────────────
chmod +x "$SCRIPT_DIR/franz"
echo "  ✔  Made franz script executable."

# ── Option 1: Copy to /usr/local/bin (system-wide) ───────────
if [ -w /usr/local/bin ]; then
    cp "$SCRIPT_DIR/franz" "$INSTALL_TO"
    # Patch the script to use the absolute path to main.py
    sed -i.bak "s|SCRIPT_DIR=.*|SCRIPT_DIR=\"$SCRIPT_DIR\"|" "$INSTALL_TO" 2>/dev/null || true
    rm -f "${INSTALL_TO}.bak"
    echo "  ✔  Installed to $INSTALL_TO"
    echo ""
    echo "  ✅  All done! You can now use FranzCode from anywhere:"
    echo ""
    echo "      franz                → Interactive REPL"
    echo "      franz file.franz     → Run a program"
    echo "      franz --help         → Show all options"
    echo ""

elif sudo -n true 2>/dev/null; then
    # We can sudo without password prompt
    sudo cp "$SCRIPT_DIR/franz" "$INSTALL_TO"
    echo "  ✔  Installed to $INSTALL_TO (via sudo)"
    echo ""
    echo "  ✅  Done! Run:  franz"
    echo ""

else
    # Option 2: Add to ~/.local/bin instead (no sudo needed)
    LOCAL_BIN="$HOME/.local/bin"
    mkdir -p "$LOCAL_BIN"
    cp "$SCRIPT_DIR/franz" "$LOCAL_BIN/franz"

    echo "  ✔  Installed to $LOCAL_BIN/franz"
    echo ""
    echo "  ⚠️  Make sure $LOCAL_BIN is in your PATH."
    echo "     Add this to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo '      export PATH="$PATH:'"$LOCAL_BIN"'"'
    echo ""
    echo "     Then run:  source ~/.bashrc   (or restart your terminal)"
    echo ""
    echo "  ✅  After that, you can use:  franz"
    echo ""
fi

# ── Quick test ────────────────────────────────────────────────
echo "  Running quick sanity check..."
TMPFILE=$(mktemp /tmp/franztest.XXXXXX.franz)
echo 'SAY "FranzCode installed successfully!"' > "$TMPFILE"
$PY "$SCRIPT_DIR/main.py" "$TMPFILE"
rm -f "$TMPFILE"
