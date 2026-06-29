#!/usr/bin/env bash
#
# create-bundle.sh — Scaffold a new OKF bundle under bundles/
#
# Usage:
#   ./scripts/create-bundle.sh <bundle-name>
#
# Creates a complete self-contained Obsidian vault with:
#   - Directory structure (raw/, sources/, entities/, concepts/, synthesis/)
#   - Obsidian configuration (copied from bundles/main/.obsidian/)
#   - Templates (copied from bundles/main/templates/)
#   - Initial index.md and log.md files
#
# Example:
#   ./scripts/create-bundle.sh research
#
# Requirements: bash 3.2+, standard Unix tools (mkdir, cp, cat)

set -euo pipefail

# ── Help ──────────────────────────────────────────────────────────────────────

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  cat <<'EOF'
Usage: create-bundle.sh <bundle-name>

Scaffold a new OKF bundle (self-contained Obsidian vault) under bundles/.

The new bundle includes:
  - Full directory structure (raw, sources, entities, concepts, synthesis)
  - Obsidian configuration (copied from bundles/main/.obsidian/)
  - Templates (copied from bundles/main/templates/)
  - Initial index.md and log.md
  - Empty raw/.gitkeep for git tracking

Arguments:
  <bundle-name>  A kebab-case name for the new bundle (e.g., research, my-notes)

Example:
  ./scripts/create-bundle.sh research
EOF
  exit 0
fi

# ── Argument validation ──────────────────────────────────────────────────────

if [ $# -eq 0 ]; then
  echo "Error: Bundle name required." >&2
  echo "Usage: ./scripts/create-bundle.sh <bundle-name>" >&2
  echo "Try --help for more information." >&2
  exit 1
fi

BUNDLE_NAME="$1"

# Validate kebab-case: lowercase letters, digits, hyphens only
if ! [[ "$BUNDLE_NAME" =~ ^[a-z][a-z0-9-]*$ ]]; then
  echo "Error: Bundle name must be kebab-case (lowercase letters, digits, hyphens, start with a letter)." >&2
  echo "Got: '$BUNDLE_NAME'" >&2
  exit 1
fi

# ── Determine paths ───────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MAIN_BUNDLE="$REPO_ROOT/bundles/main"
NEW_BUNDLE="$REPO_ROOT/bundles/$BUNDLE_NAME"

# ── Pre-flight checks ─────────────────────────────────────────────────────────

if [ ! -d "$MAIN_BUNDLE" ]; then
  echo "Error: Source bundle 'bundles/main/' not found at $MAIN_BUNDLE" >&2
  echo "Make sure you're running this script from the okf-wiki repository." >&2
  exit 1
fi

if [ -d "$NEW_BUNDLE" ]; then
  echo "Error: Bundle 'bundles/$BUNDLE_NAME/' already exists at $NEW_BUNDLE" >&2
  echo "Choose a different name or remove the existing bundle first." >&2
  exit 1
fi

# ── Create directory structure ────────────────────────────────────────────────

echo "Creating bundle: bundles/$BUNDLE_NAME/"
echo ""

echo "  → Creating directories..."
mkdir -p "$NEW_BUNDLE"/{.obsidian,templates,raw,sources,entities,concepts,synthesis}

# ── Copy Obsidian configuration ───────────────────────────────────────────────

echo "  → Copying Obsidian configuration..."
for f in app.json appearance.json core-plugins.json community-plugins.json templates.json; do
  if [ -f "$MAIN_BUNDLE/.obsidian/$f" ]; then
    cp "$MAIN_BUNDLE/.obsidian/$f" "$NEW_BUNDLE/.obsidian/$f"
    echo "    ✓ .obsidian/$f"
  else
    echo "    ⚠ .obsidian/$f not found in main bundle, skipping"
  fi
done

# NOTE: workspace.json is intentionally NOT copied — each vault should generate
# its own workspace to avoid stale file paths from the source vault.

# ── Copy templates ────────────────────────────────────────────────────────────

echo "  → Copying templates..."
template_count=0
for f in "$MAIN_BUNDLE"/templates/*.md; do
  if [ -f "$f" ]; then
    cp "$f" "$NEW_BUNDLE/templates/"
    echo "    ✓ templates/$(basename "$f")"
    ((template_count++)) || true
  fi
done
if [ "$template_count" -eq 0 ]; then
  echo "    ⚠ No template files found in main bundle"
fi

# ── Create root index.md ──────────────────────────────────────────────────────

echo "  → Creating index.md..."
cat > "$NEW_BUNDLE/index.md" <<'EOF'
---
okf_wiki_version: "0.1"
---

# OKF Wiki Index

## Sources

*No sources ingested yet.*

## Entities

*No entity pages yet.*

## Concepts

*No concept pages yet.*

## Synthesis

*No synthesis pages yet.*
EOF
echo "    ✓ index.md"

# ── Create root log.md ────────────────────────────────────────────────────────

echo "  → Creating log.md..."
TODAY="$(date +%Y-%m-%d)"
cat > "$NEW_BUNDLE/log.md" <<LOGEOF
# Wiki Log

## $TODAY

* **Initialization**: Created bundle \`bundles/$BUNDLE_NAME/\` with directory structure, Obsidian configuration, and templates. Established the foundation for llm-wiki operations following OKF v0.1.
LOGEOF
echo "    ✓ log.md"

# ── Create directory index files ──────────────────────────────────────────────

echo "  → Creating directory index files..."
for dir in sources entities concepts synthesis; do
  dir_title="$(echo "$dir" | sed 's/.*/\u&/')"  # Capitalize first letter
  cat > "$NEW_BUNDLE/$dir/index.md" <<INDEXEOF
# $dir_title Index

*No ${dir%-} pages yet.*
INDEXEOF
  echo "    ✓ $dir/index.md"
done

# Fix the "s" removal for entities/concepts/synthesis (they end in s, we want them displayed naturally)
# Rewrite with proper titles
echo "# Sources Index

*No source summaries yet.*" > "$NEW_BUNDLE/sources/index.md"

echo "# Entities Index

*No entity pages yet.*" > "$NEW_BUNDLE/entities/index.md"

echo "# Concepts Index

*No concept pages yet.*" > "$NEW_BUNDLE/concepts/index.md"

echo "# Synthesis Index

*No synthesis pages yet.*" > "$NEW_BUNDLE/synthesis/index.md"

# ── Create raw/.gitkeep ───────────────────────────────────────────────────────

echo "  → Creating raw/.gitkeep..."
touch "$NEW_BUNDLE/raw/.gitkeep"
echo "    ✓ raw/.gitkeep"

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Bundle 'bundles/$BUNDLE_NAME/' created successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Structure:"
echo "    bundles/$BUNDLE_NAME/"
echo "    ├── .obsidian/        Obsidian configuration"
echo "    ├── templates/        Page templates"
echo "    ├── index.md          Bundle index"
echo "    ├── log.md            Operation log"
echo "    ├── raw/              Immutable source documents"
echo "    ├── sources/          Source summaries"
echo "    ├── entities/         Entity pages"
echo "    ├── concepts/         Concept pages"
echo "    └── synthesis/        Synthesis pages"
echo ""
echo "  To open in Obsidian:"
echo "    Open folder as vault → select 'bundles/$BUNDLE_NAME/'"
echo ""
echo "  To use with an LLM agent:"
echo "    Tell the agent: 'Switch to bundle $BUNDLE_NAME'"
echo ""
