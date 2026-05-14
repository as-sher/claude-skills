#!/usr/bin/env bash
# Install a skill from this repo directly into ~/.claude/skills/
# Usage: curl -fsSL https://raw.githubusercontent.com/as-sher/claude-skills/main/install.sh | bash -s usage-tracker
set -e

SKILL=${1:-usage-tracker}
DEST="$HOME/.claude/skills/$SKILL"
REPO="https://github.com/as-sher/claude-skills.git"

echo "Installing $SKILL → $DEST"

mkdir -p "$HOME/.claude/skills"

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

git clone --filter=blob:none --sparse --depth=1 --quiet "$REPO" "$tmpdir"
git -C "$tmpdir" sparse-checkout set "$SKILL"

rm -rf "$DEST"
cp -r "$tmpdir/$SKILL" "$DEST"

echo "✓ Done — type /usage-tracker in Claude Code to verify"
