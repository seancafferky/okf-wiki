# OKF Wiki

**An Obsidian-backed, LLM-maintained personal knowledge base that follows
Google's [Open Knowledge Format](google-okf-spec.md).**

Clone this repo, open a bundle in Obsidian, point your LLM agent at `AGENT.md`,
and start building a compounding knowledge base today.

---

## What is this?

Most people's experience with LLMs and documents looks like RAG: upload files,
the LLM retrieves chunks at query time, and generates an answer. There's no
accumulation. Nothing is built up.

OKF Wiki is different. Instead of retrieving from raw documents at query time,
your LLM agent **incrementally builds and maintains a persistent wiki** — a
structured, interlinked collection of markdown files that sits between you and
your sources. When you add a new source, the agent:

1. Reads it and extracts key information
2. Creates a structured summary page
3. Updates entity and concept pages across the wiki
4. Notes where new data contradicts old claims
5. Maintains cross-references so everything is connected
6. Keeps an index and log so you can find everything later

The knowledge is compiled once and then *kept current*, not re-derived on every
query. The wiki keeps getting richer with every source you add.

You never write the wiki yourself — the LLM does all the summarizing,
cross-referencing, filing, and bookkeeping. You curate sources, ask questions,
and think about what it all means.

Read [llm-wiki.md](llm-wiki.md) for the full vision.

## Why OKF?

[Open Knowledge Format](google-okf-spec.md) (OKF) is Google's open standard for
representing knowledge as a directory of markdown files with YAML frontmatter.
It's designed to be:

- **Readable** by humans without tooling (`cat` a file, you can read it)
- **Parseable** by agents without bespoke SDKs
- **Diffable** in version control (`git diff` works naturally)
- **Portable** across tools, organizations, and time

No schema registry, no central authority, no required tooling. If you can
`git clone` a repo, you can use OKF.

This repository is a reference implementation: an OKF-compliant Obsidian vault
purpose-built for the llm-wiki pattern. See [SPEC.md](SPEC.md) for the full
specification.

## Key Features

- **OKF-compliant** — Every page has structured YAML frontmatter with type,
  title, tags, and timestamps. Cross-links use bundle-relative paths.
- **Obsidian-native** — Each bundle is a self-contained Obsidian vault. Open it
  and you get graph view, backlinks, search, and all Obsidian features for free.
- **Agent-first design** — `AGENT.md` tells any LLM agent exactly how to
  operate: ingest sources, answer queries, lint the wiki, maintain the index.
- **Multi-bundle** — The `bundles/` directory can hold multiple independent
  knowledge bases, each with its own structure and Obsidian configuration.
- **Templates included** — Obsidian templates for source summaries, concept
  pages, and log entries so the agent (or you) can create pages with
  pre-populated OKF frontmatter.
- **Git-friendly** — It's just a directory of markdown files. Version history,
  branching, and collaboration come for free.

## Repository Structure

```
okf-wiki/
├── README.md                  # You are here
├── QUICKSTART.md              # Setup instructions
├── AGENT.md                   # LLM agent instruction manual
├── CLAUDE.md                  # Claude Code import
├── SPEC.md                    # Formal specification
├── llm-wiki.md                # Original llm-wiki pattern
├── google-okf-spec.md         # OKF v0.1 specification
└── bundles/
    └── main/                  # Default bundle (self-contained Obsidian vault)
        ├── .obsidian/         # Obsidian configuration
        ├── templates/         # Page templates
        ├── index.md           # Bundle index
        ├── log.md             # Operation log
        ├── raw/               # Immutable source documents
        ├── sources/           # Source summaries
        ├── entities/          # Entity pages
        ├── concepts/          # Concept pages
        └── synthesis/         # Synthesis & analysis pages
```

## Getting Started

See [QUICKSTART.md](QUICKSTART.md) for step-by-step setup instructions.

Quick version:

```bash
git clone <this-repo>
# Open bundles/main/ as an Obsidian vault
# Point your LLM agent at AGENT.md
# Drop a source in raw/ and say "ingest this"
```

## License

MIT License — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 OKF Wiki contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Acknowledgments

- [llm-wiki](llm-wiki.md) — The original pattern by the llm-wiki authors
- [OKF](google-okf-spec.md) (Open Knowledge Format) — Google's open standard for
  knowledge representation
- [Obsidian](https://obsidian.md) — The local-first markdown knowledge base
- [agents.md](https://agents.md) — The cross-tool standard for agent instructions
