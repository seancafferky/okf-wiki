# OKF Wiki — LLM-Managed Knowledge Base

An OKF-compliant Obsidian vault implementing the [llm-wiki](llm-wiki.md) pattern.
The LLM agent builds and maintains the wiki; the human curates sources and asks
questions. This file is the agent's instruction manual — read it before any
operation.

See [SPEC.md](SPEC.md) for the formal specification.

## Project Overview

- **Pattern:** llm-wiki — incremental, compounding knowledge base maintained by an LLM
- **Format:** [OKF v0.1](google-okf-spec.md) (Open Knowledge Format) — a directory of markdown files with YAML frontmatter
- **Editor:** Obsidian (the human's IDE for browsing the wiki)
- **Agent role:** Read raw sources, write and maintain all wiki pages, keep cross-references current
- **Human role:** Curate sources, direct analysis, ask questions, think about what it means
- **Goal:** Anyone can clone this repository and immediately have a working Obsidian-backed llm-wiki that follows OKF

## Directory Structure

```
okf-wiki/                          # Repository root
├── AGENT.md                       # This file — agent instructions
├── CLAUDE.md                      # Claude Code import of AGENT.md
├── SPEC.md                        # Formal specification for this implementation
├── README.md                      # Public introduction and license
├── QUICKSTART.md                  # Setup instructions
├── llm-wiki.md                    # Original llm-wiki idea document
├── google-okf-spec.md             # OKF v0.1 specification
└── bundles/                       # All OKF bundles live here
    ├── main/                      # Default bundle (self-contained Obsidian vault)
    │   ├── .obsidian/             # Obsidian configuration (DO NOT EDIT)
    │   ├── templates/             # Obsidian templates for new pages
    │   ├── index.md               # Bundle index — catalog of all wiki pages
    │   ├── log.md                 # Chronological log of all operations
    │   ├── raw/                   # Immutable source documents (read-only, not OKF)
    │   ├── sources/               # Source summaries (OKF concepts)
    │   ├── entities/              # Entity pages — people, orgs, books, projects
    │   ├── concepts/              # Concept pages — ideas, theories, frameworks
    │   └── synthesis/             # Synthesis pages — comparisons, analyses, theses
    └── <other_bundle>/            # Other bundle (self-contained Obsidian vault)
```

**Key insight:** The Obsidian vault root IS the bundle root (`bundles/main/`).
This means bundle-relative absolute links (`/sources/foo.md`) resolve correctly
in Obsidian because `/` is the bundle root. Each bundle in `bundles/` is its own
self-contained Obsidian vault — just open it in Obsidian as a vault.

The repository can contain multiple bundles (e.g., `bundles/research/`,
`bundles/personal/`). The agent works within one bundle at a time. Unless
instructed otherwise, the active bundle is `bundles/main/`.

## Conventions

### OKF Frontmatter (REQUIRED on every wiki page)

Every `.md` file the agent creates or edits (except `index.md` and `log.md`)
MUST have valid YAML frontmatter with at least `type` and `title`:

```yaml
---
type: source-summary | entity | concept | synthesis | query
title: <Display Name>
description: <One-sentence summary>
tags: [tag1, tag2]
timestamp: <ISO 8601 datetime>
source: <path to raw source file> # source-summary only
resource: <canonical URI> # If applicable
---
```

### Type values

| Type             | Use for                                                               |
| ---------------- | --------------------------------------------------------------------- |
| `source-summary` | A page summarizing one ingested raw source                            |
| `entity`         | A person, organization, book, project, place, or other named thing    |
| `concept`        | An idea, theory, framework, method, or abstract topic                 |
| `synthesis`      | A comparison, analysis, thesis, overview, or multi-source integration |
| `query`          | A page filed from a user question that produced a valuable answer     |

### Linking

- **Always** use bundle-relative absolute links: `[link text](/sources/some-article.md)`
- **Never** use relative links (`./other.md`) for cross-page references
- Link liberally — every mention of an entity or concept that has its own page should be linked
- Broken links are tolerated (they represent not-yet-written knowledge) — flag them during lint

### Naming

- File names: `kebab-case.md`, short, descriptive
- Directory names: lowercase plural nouns
- Page titles: Human-readable, Title Case (set in frontmatter `title`)

### Content style

- Favor structural markdown — headings, lists, tables, fenced code blocks
- Lead with the most important claim or summary
- Cite sources inline: `[1]` pointing to entries under `# Citations`
- Keep pages focused — one subject per page; split when a page covers too much

## Workflows

All paths below are relative to the active bundle root (e.g., `bundles/main/`).

### Create a bundle

When the user asks to create a new bundle (or invokes `/create-bundle <name>`):

1. **Validate** the bundle name — kebab-case, doesn't already exist under `bundles/`
2. **Create** the directory structure under `bundles/<name>/`:
   - `.obsidian/`, `templates/`, `raw/`, `sources/`, `entities/`, `concepts/`, `synthesis/`
3. **Copy** `.obsidian/` config files from `bundles/main/.obsidian/` (skip `workspace.json` — let Obsidian generate it fresh):
   - `app.json`, `appearance.json`, `core-plugins.json`, `community-plugins.json`, `templates.json`
4. **Copy** all `templates/*.md` files from `bundles/main/templates/`
5. **Create** `index.md` with empty sections for Sources, Entities, Concepts, Synthesis
6. **Create** `log.md` with an Initialization entry for today's date
7. **Create** minimal `index.md` files in `sources/`, `entities/`, `concepts/`, `synthesis/`
8. **Create** `raw/.gitkeep` so the directory is git-tracked
9. **Report** what was created and how to open it in Obsidian

See `.claude/skills/create-bundle.md` for the detailed procedure. A shell script
(`scripts/create-bundle.sh`) is also available for manual use outside the agent.

### Ingest a source

When the user provides a raw source file to process:

1. **Read** the raw source file from `raw/`
2. **Discuss** key takeaways with the user — what's important, what to emphasize
3. **Create** `sources/<source-name>.md` with:
   - `type: source-summary`
   - A structured summary of the source
   - Key claims, data points, quotes worth preserving
   - `source:` frontmatter field pointing to the raw file
4. **Update or create** entity pages in `entities/` for any named things discussed
5. **Update or create** concept pages in `concepts/` for ideas or frameworks introduced
6. **Cross-link** — add links between the new source page and affected entity/concept pages; add links from those pages back to the source
7. **Update** `index.md` — add the new page to the appropriate section with a one-line description
8. **Append** to `log.md` — record the ingest with date, source name, and pages touched

A single source might touch 10-15 wiki pages. The goal is integration, not just filing.

### Answer a query

When the user asks a question:

1. **Read** `index.md` to identify relevant pages
2. **Read** those pages and synthesize an answer
3. **Apply the filing bar** (below) — decide whether this becomes a new page at all
4. **Offer** to file the answer as a new page only if it clears the bar:
   - `type: query` for direct answers
   - `type: synthesis` for multi-source analyses or comparisons
5. If filed: update `index.md`, append to `log.md`, cross-link to related pages

#### The filing bar

File a `query` or `synthesis` page only when the answer does one of two things:

- **Joins two or more sources** — it connects, compares, or reconciles material
  that lives on separate pages, so the connection has nowhere else to live
- **Records a judgment no source contains** — a conclusion, ruling, or
  interpretation the wiki is making, not one it is reporting

If the answer does neither, it belongs in an existing page. **Improve that page
instead**: sharpen its claims, add the missing detail, tighten its links. An
answer restating one source is that source page's job; an answer explaining one
concept is that concept page's job.

This keeps the wiki compounding rather than accumulating. A wiki of near-duplicate
query pages is harder to use than the sources it was built from.

The bar covers `query` and `synthesis` only — `source-summary`, `entity`, and
`concept` pages are created freely during ingest. Formal statement: [SPEC.md
§4.6](SPEC.md).

### Lint the wiki

When the user asks to health-check the wiki:

1. **Scan** for contradictions — claims in different pages that can't both be true
2. **Find** orphan pages — pages with no inbound links from other wiki pages
3. **Identify** missing cross-references — an entity or concept mentioned in prose but not linked to its page
4. **Surface** redlinks — concepts mentioned that deserve their own page
5. **Check** stale timestamps — pages not updated recently despite newer relevant sources
6. **Report** findings to the user as a structured list
7. **Fix** what the user approves

### Update the index

After any operation that adds or changes pages, update `index.md`:

```markdown
# Sources

- [Article Title](/sources/article-slug.md) — One-line description of what it covers.

# Entities

- [Entity Name](/entities/entity-slug.md) — One-line description.

# Concepts

- [Concept Name](/concepts/concept-slug.md) — One-line description.

# Synthesis

- [Analysis Title](/synthesis/analysis-slug.md) — One-line description.
```

Use the `description` from each page's frontmatter as the one-line summary.

## Boundaries

### ✅ Always do

- Maintain valid OKF frontmatter on every wiki page
- Update `index.md` when adding or significantly modifying pages
- Append to `log.md` for every ingest, filed query, or lint pass
- Use absolute bundle-relative links (`/path/to/page.md`)
- Keep frontmatter `timestamp` current on every edit
- Read `index.md` first before searching for information
- Meet the filing bar before creating a `query` or `synthesis` page — otherwise improve the existing page
- Preserve existing frontmatter keys when editing pages (don't drop `tags`, `source`, etc.)

### ⚠️ Ask first

- Before deleting or significantly restructuring pages
- Before ingesting a source the user hasn't explicitly asked you to process
- Before changing the directory structure or type taxonomy
- Before modifying `AGENT.md`, `SPEC.md`, or `CLAUDE.md`

### 🚫 Never

- Modify files in `raw/` — these are immutable source documents
- Create wiki pages without OKF frontmatter (except `index.md` and `log.md`)
- Remove or alter the `type` field in existing pages
- Use relative links (`./`) for cross-page references
- Edit `.obsidian/` configuration files
