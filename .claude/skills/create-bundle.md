---
name: create-bundle
description: Create a new OKF bundle under bundles/ with the complete directory structure, Obsidian configuration, templates, and initial index/log files.
argument-hint: <bundle-name>
---

# Create Bundle

Create a new self-contained OKF bundle (Obsidian vault) under `bundles/`.

## Usage

The user invokes `/create-bundle <bundle-name>` where `<bundle-name>` is a
kebab-case name for the new bundle (e.g., `research`, `personal-notes`,
`project-alpha`).

## Procedure

### 1. Validate

- Ensure `<bundle-name>` is provided and uses kebab-case (lowercase letters, digits, hyphens).
- Ensure `bundles/<bundle-name>/` does not already exist. If it does, warn the user and ask whether to skip or pick a different name.

### 2. Create directory structure

Under `bundles/<bundle-name>/`, create:

```
bundles/<bundle-name>/
├── .obsidian/
├── templates/
├── raw/
├── sources/
├── entities/
├── concepts/
└── synthesis/
```

```bash
mkdir -p bundles/<bundle-name>/{.obsidian,templates,raw,sources,entities,concepts,synthesis}
```

### 3. Copy Obsidian configuration

Copy all files from `bundles/main/.obsidian/` to the new bundle's `.obsidian/` directory. The Obsidian config files are:

- `app.json` — Editor settings (always update links, spellcheck, etc.)
- `appearance.json` — Theme and font settings
- `core-plugins.json` — Enabled core plugins (templates, graph, backlinks, etc.)
- `community-plugins.json` — Community plugin list (empty array initially)
- `templates.json` — Template folder configuration
- `workspace.json` — Default workspace layout (file explorer, search, backlinks, etc.)

Do NOT copy `.obsidian/workspace.json` — each vault should start with a fresh workspace so Obsidian generates it on first open and file paths from the old vault don't appear in "last open files."

```bash
for f in app.json appearance.json core-plugins.json community-plugins.json templates.json; do
  cp bundles/main/.obsidian/"$f" bundles/<bundle-name>/.obsidian/
done
```

### 4. Copy templates

Copy all template files from `bundles/main/templates/`:

```bash
cp bundles/main/templates/*.md bundles/<bundle-name>/templates/
```

This includes:
- `concept.md` — For entity, concept, and synthesis pages
- `source-summary.md` — For source summary pages
- `log-entry.md` — For log entries

### 5. Create root index.md

Create `bundles/<bundle-name>/index.md`:

```markdown
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
```

### 6. Create root log.md

Create `bundles/<bundle-name>/log.md`:

```markdown
# Wiki Log

## YYYY-MM-DD

* **Initialization**: Created bundle `bundles/<bundle-name>/` with directory structure, Obsidian configuration, and templates. Established the foundation for llm-wiki operations following OKF v0.1.
```

Replace `YYYY-MM-DD` with today's date in ISO 8601 format (e.g., `2026-06-30`).

### 7. Create directory index files

Create minimal `index.md` files in each concept directory:

**`sources/index.md`:**
```markdown
# Sources Index

*No source summaries yet.*
```

**`entities/index.md`:**
```markdown
# Entities Index

*No entity pages yet.*
```

**`concepts/index.md`:**
```markdown
# Concepts Index

*No concept pages yet.*
```

**`synthesis/index.md`:**
```markdown
# Synthesis Index

*No synthesis pages yet.*
```

### 8. Create raw/.gitkeep

Create an empty `bundles/<bundle-name>/raw/.gitkeep` to ensure the `raw/` directory is tracked by git even when empty.

### 9. Report

Tell the user what was created and how to use it:

- The bundle path: `bundles/<bundle-name>/`
- How to open it in Obsidian: Open folder as vault → select `bundles/<bundle-name>/`
- How the agent will use it: The agent reads `AGENT.md` from the repo root and operates on the active bundle
- How to switch the active bundle: Tell the agent "Switch to bundle `<bundle-name>`"
