#!/usr/bin/env bash
# Brand New Day — installer.
#
# Idempotent. Safe to re-run. Never overwrites user-modified files (config.yml,
# profile.md, .env, dashboard.html, data/*.json). Re-running picks up new
# runtime/skill files from the repo without clobbering local edits.
#
# After this finishes, run `/brand-new-day init` in Claude Code to validate
# your config and exercise the JSearch API key.

set -euo pipefail

# --- locate the repo root (this script's directory) ---
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -d "$REPO_ROOT/runtime" || ! -d "$REPO_ROOT/skill" ]]; then
    echo "✗ install.sh must be run from the brand-new-day repo root."
    echo "  Expected $REPO_ROOT/runtime and $REPO_ROOT/skill."
    exit 1
fi

# --- BND_HOME prompt ---
DEFAULT_BND_HOME="$HOME/brand-new-day"
echo "Brand New Day — Installer"
echo "========================="
echo ""
read -r -p "Where should BND_HOME live? [$DEFAULT_BND_HOME]: " BND_HOME_INPUT
BND_HOME="${BND_HOME_INPUT:-$DEFAULT_BND_HOME}"
BND_HOME="${BND_HOME/#\~/$HOME}"  # expand leading ~
echo ""
echo "Installing to: $BND_HOME"
echo ""

# --- helpers ---
copy_if_missing() {
    # copy_if_missing <src> <dst>
    local src="$1" dst="$2"
    if [[ -e "$dst" ]]; then
        echo "  · $(basename "$dst") — skipped (already exists)"
    else
        cp "$src" "$dst"
        echo "  ✓ $(basename "$dst")"
    fi
}

write_starter_if_missing() {
    # write_starter_if_missing <path> <initial-content>
    local path="$1" content="$2"
    if [[ -e "$path" ]]; then
        echo "  · $(basename "$path") — skipped (already exists)"
    else
        printf '%s' "$content" > "$path"
        echo "  ✓ $(basename "$path")"
    fi
}

# --- 1. BND_HOME directory + data subdir ---
echo "[1/6] BND_HOME scaffolding"
mkdir -p "$BND_HOME/data"
echo "  ✓ $BND_HOME/data"

# --- 2. Copy runtime files ---
echo ""
echo "[2/6] Runtime files"
for f in bnd-scan.py bnd-hash.py bnd-render-dashboard.py fetch-page.js package.json; do
    copy_if_missing "$REPO_ROOT/runtime/$f" "$BND_HOME/$f"
done

# --- 3. Templates → user files (rename .example, only if target missing) ---
echo ""
echo "[3/6] User config templates"
copy_if_missing "$REPO_ROOT/runtime/config.yml.example"  "$BND_HOME/config.yml"
copy_if_missing "$REPO_ROOT/runtime/profile.md.example"  "$BND_HOME/profile.md"
copy_if_missing "$REPO_ROOT/runtime/dashboard-template.html" "$BND_HOME/dashboard.html"

# --- 4. Starter JSON data files (Option Y — install.sh creates these so first
#       scan works without /brand-new-day init being required) ---
echo ""
echo "[4/6] Starter data files"
write_starter_if_missing "$BND_HOME/data/listings.json"     "[]"
write_starter_if_missing "$BND_HOME/data/reviewed.json"     "{}"
write_starter_if_missing "$BND_HOME/data/scan-state.json"   "{}"
write_starter_if_missing "$BND_HOME/data/run-log.json"      "[]"
write_starter_if_missing "$BND_HOME/data/api-usage.json"    "{}"
write_starter_if_missing "$BND_HOME/data/credit-ledger.json" "{}"

# --- 5. Install the skill (overwrite OK — read-only artifacts) ---
echo ""
echo "[5/6] Claude Code skill"
SKILL_DEST="$HOME/.claude/skills/brand-new-day"
mkdir -p "$HOME/.claude/skills"
if [[ -e "$SKILL_DEST" ]]; then
    rm -rf "$SKILL_DEST"
fi
cp -r "$REPO_ROOT/skill" "$SKILL_DEST"
echo "  ✓ $SKILL_DEST"

# --- 6. .env + RapidAPI key prompt ---
echo ""
echo "[6/6] API key"
ENV_PATH="$BND_HOME/.env"
if [[ -e "$ENV_PATH" ]]; then
    echo "  · .env — skipped (already exists). Edit $ENV_PATH if you need to update RAPIDAPI_KEY."
else
    cp "$REPO_ROOT/.env.example" "$ENV_PATH"
    echo "  ✓ .env (from .env.example)"
    echo ""
    echo "  Brand New Day uses JSearch via RapidAPI. Sign up at:"
    echo "    https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch"
    echo ""
    read -r -p "  Paste RapidAPI key now (or hit Enter to skip and add later): " RAPIDAPI_KEY_INPUT
    if [[ -n "$RAPIDAPI_KEY_INPUT" ]]; then
        # replace the placeholder line in .env
        # use a portable in-place sed (works on macOS BSD sed without GNU -i)
        tmpfile=$(mktemp)
        sed "s|^RAPIDAPI_KEY=.*|RAPIDAPI_KEY=${RAPIDAPI_KEY_INPUT}|" "$ENV_PATH" > "$tmpfile"
        mv "$tmpfile" "$ENV_PATH"
        echo "  ✓ RAPIDAPI_KEY written to .env"
    else
        echo "  · skipped — edit $ENV_PATH later and set RAPIDAPI_KEY=<your-key>"
    fi
fi

echo ""
echo "============================================"
echo "Done."
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. export BND_HOME=\"$BND_HOME\""
echo "     (add this to your shell rc to persist across sessions)"
echo ""
echo "  2. Edit your profile:"
echo "     \$EDITOR $BND_HOME/profile.md"
echo ""
echo "  3. Optional: tune scoring + search keywords in config.yml:"
echo "     \$EDITOR $BND_HOME/config.yml"
echo ""
echo "  4. In Claude Code, run:"
echo "     /brand-new-day init    # validates config + tests API key"
echo "     /brand-new-day         # full scan"
echo ""
