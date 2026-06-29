# OKF Wiki — Specification

**Version 0.1 — Draft**

This document specifies a concrete instantiation of the [llm-wiki](llm-wiki.md)
pattern built on [OKF v0.1](google-okf-spec.md) (Open Knowledge Format). It
defines the directory structure, concept type taxonomy, operational workflows,
and Obsidian template conventions that make an OKF bundle function as an
LLM-maintained personal knowledge base.

This spec is to this repository what `google-okf-spec.md` is to OKF itself: the
authoritative description of what the system is and how it works. Agents read
`AGENT.md` for day-to-day instructions; they read this file to understand the
design rationale and formal rules.

**Ultimate goal:** A user can clone this repository, open a bundle in Obsidian,
point their LLM agent at `AGENT.md`, and immediately have a working llm-wiki —
ingesting sources, answering queries, and growing a compounding knowledge base
that follows the OKF standard.

---

## 1. Motivation

The llm-wiki pattern describes a powerful idea — an LLM that incrementally
builds and maintains a personal knowledge base — but it intentionally leaves
implementation details open. OKF provides the structural foundation (markdown
+ YAML frontmatter, cross-linking, index/log conventions) but doesn't prescribe
domain-specific type taxonomies or operational workflows.

This spec bridges the gap. It defines:

- **Where** files go (the directory structure for an llm-wiki).
- **What** types of pages exist (the concept taxonomy).
- **How** the LLM operates (the ingest, query, and lint workflows).
- **How** Obsidian templates accelerate page creation.

### Goals

1. **Immediate usability.** A user who clones this repository and opens a bundle
   in Obsidian should have a fully functional llm-wiki — no additional tooling
   or configuration required beyond what's provided.
2. Define a reusable directory layout for llm-wiki instances.
3. Standardize the frontmatter schema so agents and tools can operate reliably.
4. Specify operational workflows with enough precision that any OKF-aware agent
   can execute them.
5. Provide Obsidian templates that enforce the schema and reduce friction.

### Non-goals

- Prescribing the exact set of subdirectories — producers may add or remove
  categories as their domain requires.
- Defining a fixed tag vocabulary.
- Specifying raw source formats — raw sources are opaque to this spec.
- Replacing OKF — this spec extends OKF; it doesn't modify it.

---

## 2. Relationship to OKF

This spec is a **profile** of OKF v0.1. Every valid page in an OKF Wiki is a
valid OKF concept document. This spec adds:

| Layer | What it defines |
|-------|-----------------|
| **Directory conventions** | Where different concept types live within the bundle. |
| **Type taxonomy** | The recommended `type` values for llm-wiki pages. |
| **Extended frontmatter** | The `source` field for linking summaries to raw material. |
| **Operational workflows** | Step-by-step procedures for ingest, query, and lint. |
| **Obsidian templates** | Template files that pre-populate OKF frontmatter. |

Where this spec is silent, OKF v0.1 applies.

---

## 3. Terminology

Terms inherited from OKF v0.1 §2:

- **Knowledge Bundle** — The directory tree of markdown files. The unit of
  distribution. This vault is one bundle.
- **Concept** — A single unit of knowledge, represented as one `.md` file with
  YAML frontmatter.
- **Concept ID** — The file path with `.md` suffix removed.
- **Frontmatter** — YAML block delimited by `---` at the top of a file.
- **Body** — Everything after the frontmatter.
- **Link** — A standard markdown link from one concept to another.
- **Citation** — A link from a concept to an external source.

Terms specific to this spec:

- **Raw source** — An immutable document in `raw/` that the LLM reads but
  never modifies. Articles, papers, book notes, podcast transcripts, clipped
  web pages. Not an OKF concept.
- **Source summary** — An OKF concept (type: `source-summary`) that distills
  a raw source into structured knowledge, filed in `sources/`.
- **Entity** — A named thing with its own page: a person, organization, book,
  project, place, or event. Type: `entity`.
- **Synthesis** — A page that integrates multiple sources or concepts: a
  comparison, analysis, thesis, or overview. Type: `synthesis`.
- **Filed query** — A page created from a user's question when the answer is
  valuable enough to preserve. Type: `query`.

---

## 4. Bundle Structure

This repository can contain one or more OKF bundles. Each bundle is a
self-contained Obsidian vault stored in the `bundles/` directory at the
repository root.

### 4.0 Repository layout

```
okf-wiki/                          # Repository root
├── AGENT.md                       # Agent instruction file
├── CLAUDE.md                      # Claude Code import of AGENT.md
├── SPEC.md                        # This specification
├── README.md                      # Public introduction and license
├── QUICKSTART.md                  # Setup instructions
├── llm-wiki.md                    # Original llm-wiki idea document
├── google-okf-spec.md             # OKF v0.1 specification
└── bundles/                       # All OKF bundles
    ├── main/                      # Default bundle
    │   └── ... (see §4.1)
    └── <other-bundle>/            # Additional bundles (optional)
        └── ...
```

`AGENT.md`, `CLAUDE.md`, `SPEC.md`, `README.md`, and `QUICKSTART.md` are
repository-level documentation — they are NOT part of any OKF bundle.
`llm-wiki.md` and `google-okf-spec.md` are reference documents.

### 4.1 Bundle layout

Each bundle in `bundles/` is a self-contained OKF bundle AND an Obsidian vault:

```
bundles/<bundle-name>/
├── .obsidian/                   # Obsidian configuration (not OKF)
│   ├── app.json
│   ├── core-plugins.json
│   ├── templates.json
│   └── ...
├── templates/                   # Obsidian templates (not OKF concepts)
│   ├── concept.md
│   ├── source-summary.md
│   └── log-entry.md
├── index.md                     # Bundle root index (§8)
├── log.md                       # Chronological log (§9)
├── raw/                         # Immutable source documents (not OKF concepts)
│   └── ...
├── sources/                     # Source summaries (type: source-summary)
│   ├── index.md
│   └── <source-slug>.md
├── entities/                    # Entity pages (type: entity)
│   ├── index.md
│   └── <entity-slug>.md
├── concepts/                    # Concept pages (type: concept)
│   ├── index.md
│   └── <concept-slug>.md
└── synthesis/                   # Synthesis pages (type: synthesis)
    ├── index.md
    └── <synthesis-slug>.md
```

The `.obsidian/` and `templates/` directories live inside each bundle so the
bundle is a standalone Obsidian vault. Open `bundles/<bundle-name>/` as an
Obsidian vault to browse it.

New bundles can be scaffolded with the provided tooling:

- **Shell script:** `./scripts/create-bundle.sh <bundle-name>` — creates the
  full structure, copies Obsidian config and templates from `bundles/main/`.
- **Agent skill:** `/create-bundle <bundle-name>` — the LLM agent follows the
  procedure documented in `.claude/skills/create-bundle.md`.

### 4.2 Reserved filenames

Inherited from OKF v0.1 §3.1: `index.md` and `log.md` are reserved at every
level and MUST NOT be used for concept documents.

### 4.3 Directory semantics

| Directory | Concept type | Purpose |
|-----------|-------------|---------|
| `sources/` | `source-summary` | One page per ingested raw source. Captures key claims, data, quotes. |
| `entities/` | `entity` | Named things: people, orgs, books, projects, places, events. |
| `concepts/` | `concept` | Abstract ideas, theories, frameworks, methods, topics. |
| `synthesis/` | `synthesis` | Multi-source integration: comparisons, analyses, theses, overviews. |

Producers MAY add directories for additional types. The four above are the
recommended minimum.

### 4.4 The `raw/` directory

Files in `raw/` are **not OKF concepts**. They are immutable source material
that the LLM reads during ingest. They have no required structure or frontmatter.
The LLM MUST NOT modify files in `raw/`.

Common raw sources:
- Articles and papers (PDF converted to markdown, or web-clipped pages)
- Book notes and chapter summaries written by the human
- Podcast transcripts
- Data files (CSV, JSON) referenced by wiki pages
- Images and diagrams

### 4.5 Filed queries

Query-result pages (type: `query`) may be filed in the directory most
appropriate to their content — `concepts/` for conceptual answers,
`synthesis/` for multi-source analyses, or a `queries/` directory if the
producer prefers to keep them separate. The type field, not the directory,
determines how a page is classified.

---

## 5. Concept Documents

Every concept follows OKF v0.1 §4. It is a UTF-8 markdown file with YAML
frontmatter and a markdown body.

### 5.1 Frontmatter

```yaml
---
type: <type-name>                 # REQUIRED. One of the values in §5.2.
title: <Display Name>             # REQUIRED. Human-readable title.
description: <one-line summary>   # Recommended. Used in index listings.
tags: [<tag>, <tag>, …]           # Recommended. Cross-cutting categorization.
timestamp: <ISO 8601 datetime>    # Recommended. Last meaningful change.
source: <path-to-raw-file>        # REQUIRED for type: source-summary.
resource: <canonical-URI>         # Optional. URI of the thing described.
---
```

**Required fields:**

- `type` — One of the values defined in §5.2. Consumers MUST tolerate unknown
  type values by treating them as generic concepts (per OKF v0.1 §4.1).
- `title` — Human-readable display name. Title Case.

**Required for specific types:**

- `source` — REQUIRED when `type: source-summary`. A path to the raw source
  file that this page summarizes (e.g., `raw/articles/some-article.md`).
  Agents use this to trace from summary back to original material.

**Recommended fields (in priority order):**

- `description` — A single sentence. Used by `index.md` generators and search.
- `tags` — A YAML list of short strings. No fixed vocabulary; producers define
  their own.
- `timestamp` — ISO 8601 datetime of last meaningful change (e.g.,
  `2026-06-29T14:30:00Z`). Updated on every substantive edit.
- `resource` — A canonical URI for the thing the concept describes (e.g., a
  Wikipedia URL for an entity, a DOI for a paper).

### 5.2 Type taxonomy

| Type | Directory | Purpose |
|------|-----------|---------|
| `source-summary` | `sources/` | A structured summary of one raw source. |
| `entity` | `entities/` | A named thing — person, org, book, project, place, event. |
| `concept` | `concepts/` | An abstract idea, theory, framework, method, or topic. |
| `synthesis` | `synthesis/` | Multi-source analysis, comparison, thesis, or overview. |
| `query` | Any | A valuable answer filed from a user question. |

Type values are not centrally registered. Producers MAY introduce new types
(e.g., `timeline`, `glossary`, `diagram`) as their domain requires. When a
page could fit multiple types, prefer the most specific one.

### 5.3 Body conventions

No body sections are required. The following section headings have conventional
meaning and SHOULD be used when applicable:

| Heading | Purpose |
|---------|---------|
| `# Overview` | A concise summary of what this page covers. |
| `# Key Claims` | Assertions extracted from sources, with citations. |
| `# Relationships` | How this concept connects to other concepts. |
| `# Citations` | External sources backing claims in the body. Numbered list. |
| `# References` | Links to related wiki pages for further reading. |

### 5.4 Example: a source summary

```markdown
---
type: source-summary
title: Attention Is All You Need
description: The seminal 2017 paper introducing the Transformer architecture.
source: raw/papers/attention-is-all-you-need.pdf.md
tags: [transformer, attention, deep-learning, paper]
timestamp: 2026-06-29T10:00:00Z
resource: https://arxiv.org/abs/1706.03762
---

# Overview

"Attention Is All You Need" (Vaswani et al., 2017) introduced the Transformer,
a neural network architecture that replaces recurrence with self-attention.
This paper is the foundation of modern LLMs.

# Key Claims

1. Self-attention layers can replace recurrent layers entirely for sequence
   transduction tasks. [1]
2. The Transformer achieves state-of-the-art BLEU scores on WMT 2014
   English-to-German and English-to-French translation while requiring
   significantly less training time than recurrent models. [1]
3. Multi-head attention allows the model to attend to information from
   different representation subspaces. [1]

# Relationships

- Introduces the [Transformer](/concepts/transformer.md) architecture.
- Builds on [Sequence-to-Sequence Learning](/concepts/seq2seq.md).
- Motivated the development of [BERT](/entities/bert.md) and
  [GPT](/entities/gpt.md).

# Citations

[1] Vaswani et al., "Attention Is All You Need", NeurIPS 2017.
```

### 5.5 Example: an entity page

```markdown
---
type: entity
title: Jane Jacobs
description: American-Canadian journalist and urbanist activist, author of The Death and Life of Great American Cities.
tags: [urbanism, author, activist, cities]
timestamp: 2026-06-29T10:00:00Z
resource: https://en.wikipedia.org/wiki/Jane_Jacobs
---

# Overview

Jane Jacobs (1916–2006) was an urbanist writer and activist whose work
fundamentally challenged modernist urban planning. Her book
[The Death and Life of Great American Cities](/sources/death-and-life.md)
(1961) introduced concepts like "eyes on the street" and the importance of
mixed-use neighborhoods.

# Key Ideas

- **Eyes on the street** — natural surveillance from street-level activity
  makes neighborhoods safer than top-down policing. See
  [natural surveillance](/concepts/natural-surveillance.md).
- **Mixed-use development** — neighborhoods thrive when they combine
  residential, commercial, and civic uses rather than segregating them.
- **Bottom-up planning** — cities are complex systems that cannot be
  understood or designed from a top-down perspective.

# Relationships

- Influenced [New Urbanism](/concepts/new-urbanism.md).
- Opposed [Robert Moses](/entities/robert-moses.md)'s top-down planning approach.
- Her ideas connect to [Complex Systems Theory](/concepts/complex-systems.md).

# References

- [The Death and Life of Great American Cities](/sources/death-and-life.md)
- [The Economy of Cities](/sources/economy-of-cities.md)
```

### 5.6 Example: a concept page

```markdown
---
type: concept
title: Induced Demand
description: The phenomenon where increasing supply of a good (like road capacity) increases its consumption, often negating the expected benefit.
tags: [economics, transportation, urban-planning, paradox]
timestamp: 2026-06-29T10:00:00Z
---

# Overview

Induced demand is the economic phenomenon where increasing the supply of a
good makes people consume more of it. In transportation, building more highway
lanes tends to increase traffic rather than reduce congestion, because the
additional capacity induces more people to drive.

# Key Claims

1. Adding road capacity in congested urban areas leads to proportional
   increases in vehicle-miles traveled within 5 years. [1]
2. The effect is strongest when the new capacity reduces travel time below
   the equilibrium that people tolerate. [1]
3. The reverse effect — "reduced demand" or "traffic evaporation" — occurs
   when road capacity is removed: some trips simply disappear. [2]

# Relationships

- A specific case of [Jevons Paradox](/concepts/jevons-paradox.md).
- Central to debates about [highway expansion](/concepts/highway-expansion.md).
- Supports arguments for [congestion pricing](/concepts/congestion-pricing.md).

# Citations

[1] Duranton & Turner, "The Fundamental Law of Road Congestion", AER 2011.
[2] Cairns et al., "Disappearing Traffic", Municipal Engineer 2002.
```

---

## 6. Cross-linking

Per OKF v0.1 §5, concepts link to other concepts using standard markdown links.

### 6.1 Link form

**Absolute bundle-relative links are REQUIRED** for all cross-references:

```markdown
See the [Transformer](/concepts/transformer.md) for details.
```

This form is stable when pages are moved within their directory and is
unambiguous regardless of the linking page's location.

### 6.2 Link density

Agents SHOULD link liberally. Every mention of an entity or concept that has
its own page should be linked on first mention within a section. Dense linking
is what makes the graph view useful and what lets humans navigate the wiki by
following connections.

### 6.3 Raw source references

Links from wiki pages to raw source files use the same absolute form:

```markdown
See the [original paper](/raw/papers/attention-is-all-you-need.pdf.md).
```

---

## 7. Index Files

Per OKF v0.1 §6, every directory MAY contain an `index.md`. Within an OKF Wiki,
every concept directory (`sources/`, `entities/`, `concepts/`, `synthesis/`)
MUST contain an `index.md` that enumerates the directory's contents.

### 7.1 Root index

The root `index.md` serves as the entry point for the entire wiki. It organizes
all pages by type:

```markdown
# OKF Wiki Index

## Sources

* [Article Title](/sources/article-slug.md) — One-line description.
* ...

## Entities

* [Entity Name](/entities/entity-slug.md) — One-line description.
* ...

## Concepts

* [Concept Name](/concepts/concept-slug.md) — One-line description.
* ...

## Synthesis

* [Analysis Title](/synthesis/analysis-slug.md) — One-line description.
* ...
```

Each entry MUST include the description from the linked page's frontmatter.
The agent updates this file on every ingest, filed query, or page creation.

### 7.2 Directory indexes

Directory-level `index.md` files follow the OKF v0.1 §6 format. They are
optional but recommended for directories with more than ~10 files.

---

## 8. Log Files

Per OKF v0.1 §7, a `log.md` at the bundle root records the chronological
history of operations. Agents MUST append to this file for every ingest, filed
query, and lint pass.

### 8.1 Format

```markdown
# Wiki Log

## 2026-06-29

* **Ingest**: Processed [Attention Is All You Need](/sources/attention-is-all-you-need.md).
  Created [Transformer](/concepts/transformer.md), updated
  [Deep Learning](/concepts/deep-learning.md).
* **Query**: "How does self-attention differ from recurrence?" — filed as
  [Self-Attention vs Recurrence](/synthesis/self-attention-vs-recurrence.md).
* **Lint**: Health check. Found 2 orphan pages, 1 contradiction flagged.

## 2026-06-28

* **Ingest**: Processed [The Death and Life of Great American Cities](/sources/death-and-life.md).
  Created [Jane Jacobs](/entities/jane-jacobs.md),
  [Eyes on the Street](/concepts/eyes-on-the-street.md),
  [Mixed-Use Development](/concepts/mixed-use-development.md).
```

### 8.2 Entry format

Each entry begins with a bold action word:

| Prefix | Use for |
|--------|---------|
| `**Ingest**` | Processing a new raw source. |
| `**Query**` | Filing a user question and its answer. |
| `**Lint**` | Running a wiki health check. |
| `**Update**` | Significant revision to an existing page. |
| `**Creation**` | Creating a page independently of an ingest or query. |
| `**Deprecation**` | Marking a page as superseded or no longer current. |

Date headings MUST use ISO 8601 `YYYY-MM-DD` form. Entries within a day are
ordered newest first.

---

## 9. Operations

### 9.1 Ingest

**Trigger:** The user provides a raw source and asks the agent to process it.

**Input:** A file in `raw/` (or a URL to clip into `raw/`).

**Procedure:**

1. **Read** the raw source.
2. **Discuss** key takeaways with the user. Ask what to emphasize.
3. **Create** `sources/<source-slug>.md` — a source summary page with
   `type: source-summary`. Include:
   - An overview of what the source is.
   - Key claims, data points, or quotes the user cares about.
   - A `# Relationships` section linking to affected entities and concepts.
   - A `# Citations` section with the primary source reference.
4. **Update entities** — for each named thing discussed in the source, either
   create a new entity page or update the existing one with new information.
   Note where new data contradicts old claims.
5. **Update concepts** — for each idea or framework discussed, either create a
   new concept page or update the existing one.
6. **Cross-link** — add links between the new source page and all affected
   entity/concept pages. Add backlinks from those pages to the source.
7. **Update index** — add the new page (and any created entity/concept pages)
   to `index.md`.
8. **Append log** — record the ingest in `log.md`, listing all pages touched.

### 9.2 Query

**Trigger:** The user asks a question about the knowledge in the wiki.

**Input:** A natural language question.

**Procedure:**

1. **Read** `index.md` to identify relevant pages.
2. **Read** those pages.
3. **Synthesize** an answer with citations to source pages.
4. **Offer** to file the answer as a new page. If the user agrees:
   - Create a page with `type: synthesis` (for multi-source answers) or
     `type: query` (for focused answers).
   - Include the question and the synthesized answer.
   - Cross-link to all pages cited in the answer.
   - Update `index.md` and `log.md`.

### 9.3 Lint

**Trigger:** The user asks the agent to health-check the wiki.

**Procedure:**

1. **Contradictions** — read pairs of pages on the same topic. Flag claims
   that cannot both be true. Present to the user with page references.
2. **Orphans** — for each page, check whether any other page links to it.
   (Index entries don't count.) Flag pages with zero inbound links.
3. **Missing links** — for each page, scan the body for mentions of entities
   or concepts that have wiki pages but aren't linked. Flag them.
4. **Redlinks** — identify concepts mentioned across multiple pages that
   deserve their own page but don't have one yet. Suggest creating them.
5. **Staleness** — flag pages whose `timestamp` is older than the most recent
   source that discusses the same topic.
6. **Report** findings as a structured list grouped by category.
7. **Fix** — for each finding the user approves, apply the fix and update
   `timestamp`, `index.md`, and `log.md`.

---

## 10. Obsidian Templates

The vault includes Obsidian templates that pre-populate OKF frontmatter. These
are stored in `templates/` and configured via `.obsidian/templates.json`.

### 10.1 Template: concept.md

For creating entity, concept, and synthesis pages.

```markdown
---
type: 
title: "{{title}}"
description: 
tags: []
timestamp: {{date:YYYY-MM-DD}}T{{time:HH:mm}}:00Z
---

# Overview


# Relationships


# References

*
```

**Usage:** In Obsidian, open the command palette → "Insert template" → select
`concept`. The `{{title}}` variable expands to the active note's filename.
After insertion, fill in `type`, `description`, and `tags`.

### 10.2 Template: source-summary.md

For creating source summary pages.

```markdown
---
type: source-summary
title: "{{title}}"
description: 
source: raw/
tags: []
timestamp: {{date:YYYY-MM-DD}}T{{time:HH:mm}}:00Z
resource: 
---

# Overview


# Key Claims

1.  [1]

# Relationships


# Citations

[1] 
```

### 10.3 Template: log-entry.md

For appending a log entry. Not a full page — insert at the top of the current
day's section in `log.md`.

```markdown
* **Ingest**: Processed [Title](/sources/slug.md). Created [Entity](/entities/entity.md), updated [Concept](/concepts/concept.md).
```

---

## 11. Conformance

A bundle is conformant with OKF Wiki v0.1 if:

1. It is conformant with OKF v0.1 (per `google-okf-spec.md` §9):
   - Every non-reserved `.md` file outside `raw/` has parseable YAML frontmatter.
   - Every frontmatter block contains a non-empty `type` field.
   - `index.md` and `log.md` follow their respective structures.
2. Every `type: source-summary` page includes a non-empty `source` field.
3. A root `index.md` exists and enumerates the wiki's contents.
4. A root `log.md` exists and records operations chronologically.
5. All cross-links between wiki pages use absolute bundle-relative paths.

The `raw/` directory and its contents are explicitly excluded from OKF
conformance. Files in `raw/` are source material, not knowledge concepts.

---

## 12. Versioning

This document specifies OKF Wiki version **0.1**. It targets OKF v0.1.

- **Minor** bumps: new optional frontmatter fields, new recommended type
  values, new conventional section headings.
- **Major** bumps: breaking changes to required fields, directory structure,
  or type taxonomy.

Bundles MAY declare the OKF Wiki version by including
`okf_wiki_version: "0.1"` in the root `index.md` frontmatter.

---

## Appendix A — Minimal bundle example

Repository layout:

```
okf-wiki/
├── AGENT.md
├── CLAUDE.md
├── SPEC.md
├── README.md
├── QUICKSTART.md
├── llm-wiki.md
├── google-okf-spec.md
└── bundles/
    └── main/
        ├── .obsidian/
        │   └── ...
        ├── templates/
        │   ├── concept.md
        │   ├── source-summary.md
        │   └── log-entry.md
        ├── index.md
        ├── log.md
        ├── raw/
        │   └── articles/
        │       └── attention-is-all-you-need.pdf.md
        ├── sources/
        │   ├── index.md
        │   └── attention-is-all-you-need.md
        ├── entities/
        │   ├── index.md
        │   └── geoffrey-hinton.md
        ├── concepts/
        │   ├── index.md
        │   ├── transformer.md
        │   └── self-attention.md
        └── synthesis/
            ├── index.md
            └── transformers-vs-rnns.md
```

Root `index.md`:

```markdown
---
okf_wiki_version: "0.1"
---

# OKF Wiki Index

## Sources

* [Attention Is All You Need](/sources/attention-is-all-you-need.md) — The seminal 2017 paper introducing the Transformer architecture.

## Entities

* [Geoffrey Hinton](/entities/geoffrey-hinton.md) — British-Canadian computer scientist, pioneer of deep learning.

## Concepts

* [Transformer](/concepts/transformer.md) — Neural network architecture based on self-attention.
* [Self-Attention](/concepts/self-attention.md) — Mechanism for relating different positions in a sequence.

## Synthesis

* [Transformers vs RNNs](/synthesis/transformers-vs-rnns.md) — Comparison of the two sequence modeling paradigms.
```

Root `log.md`:

```markdown
# Wiki Log

## 2026-06-29

* **Ingest**: Processed [Attention Is All You Need](/sources/attention-is-all-you-need.md). Created [Transformer](/concepts/transformer.md), [Self-Attention](/concepts/self-attention.md), updated [Geoffrey Hinton](/entities/geoffrey-hinton.md).
* **Initialization**: Created foundational directory structure and templates.
```

---

## Appendix B — Extending the spec

This spec is designed to be customized. Common extensions:

- **Adding a directory:** Create `glossary/` for term definitions, add
  `glossary` to the type taxonomy, update the root index template.
- **Adding a type:** Define a new `type` value (e.g., `timeline`, `recipe`,
  `workout`), document its frontmatter requirements, create a template.
- **Changing the template engine:** Replace Obsidian core templates with
  Templater for dynamic template logic. Update `templates/` files accordingly.
- **Adding tooling:** Integrate `qmd` for search, Dataview for dynamic queries,
  Marp for presentations. Document tool-specific frontmatter fields.

Extensions SHOULD be documented in `SPEC.md` so agents in future sessions
understand the modified conventions.
