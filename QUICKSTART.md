# QUICKSTART — Setting Up Your OKF Wiki

This guide walks you through setting up your own Obsidian-backed llm-wiki in
under 5 minutes.

## Prerequisites

- **[Obsidian](https://obsidian.md)** — Download and install (free, Mac/Windows/Linux)
- **An LLM agent** — Claude Code, OpenAI Codex, GitHub Copilot Chat, Cursor, or
  any agent that reads `AGENT.md` as its instruction file
- **Git** (optional) — For version control and cloning the template

## Step 1: Get the repository

```bash
git clone <this-repo-url> my-wiki
cd my-wiki
```

Or download and extract the ZIP from GitHub.

## Step 2: Open the bundle in Obsidian

1. Launch Obsidian
2. Click **"Open folder as vault"**
3. Navigate to `my-wiki/bundles/main/` and select it
4. Obsidian will load the vault with all settings pre-configured

You should see the directory structure in the file explorer:

```
bundles/main/
├── index.md         # Empty index, ready to grow
├── log.md           # Operation log
├── raw/             # Where your source files go
├── sources/         # Source summaries (LLM writes these)
├── entities/        # Entity pages
├── concepts/        # Concept pages
└── synthesis/       # Synthesis pages
```

## Step 3: Verify templates are working

1. Create a new note: `Cmd/Ctrl+N`
2. Give it a title like `test-page`
3. Open the command palette: `Cmd/Ctrl+P`
4. Type **"Insert template"** and select it
5. Choose **`concept`** from the list

You should see OKF frontmatter pre-populated with `{{title}}` expanded to
`test-page`. Delete the test page when you're done.

If the templates don't appear:
1. Go to **Settings → Core plugins → Templates** — ensure it's enabled
2. Check **Settings → Templates → Template folder location** is set to `templates`

## Step 4: Point your LLM agent at AGENT.md

The agent reads `AGENT.md` from the repository root to understand:

- The directory structure and conventions
- How to ingest sources, answer queries, and lint the wiki
- What frontmatter is required
- What it should and shouldn't do

### Claude Code

Claude Code reads `CLAUDE.md` automatically, which imports `@AGENT.md`. Just
`cd` into the repository root and start Claude Code.

### Other agents

Most agents look for `AGENT.md` or `AGENTS.md` in the project root. OpenAI
Codex, Cursor, Windsurf, Aider, and GitHub Copilot all support this convention.

If your agent needs explicit instructions, paste the contents of `AGENT.md`
into your system prompt or project instructions.

## Step 5: Your first ingest

1. **Add a source** — Drop an article, paper, or note into `bundles/main/raw/`:
   - Use [Obsidian Web Clipper](https://obsidian.md/clipper) to convert web
     articles to markdown
   - Save PDFs as markdown (or just reference them)
   - Write your own notes on a book chapter, podcast, or paper

2. **Ask your agent to ingest it:**
   > "I've added `raw/articles/some-article.md`. Please ingest it."

   The agent will:
   - Read the source
   - Discuss key takeaways with you
   - Create a source summary in `sources/`
   - Update or create entity and concept pages
   - Cross-link everything
   - Update the index and log

3. **Browse the results in Obsidian** — Watch new pages appear in the file
   explorer, follow links between them, check the graph view to see connections
   forming.

## Step 6: Ask questions

Once you have a few sources ingested, ask your agent questions:

> "What does the wiki know about [topic]?"
> "Compare [concept A] and [concept B] based on what we've read."
> "What contradictions exist between our sources on [topic]?"

The agent reads `index.md` to find relevant pages, synthesizes an answer with
citations, and can file the answer back into the wiki if it's valuable.

## Step 7: Periodic linting

As the wiki grows, ask the agent to health-check it:

> "Lint the wiki."

The agent will find orphan pages, missing cross-references, stale claims, and
concepts that deserve their own page.

## Tips

### Enable image downloading in Obsidian

If you clip web articles with images:
1. **Settings → Files and Links → Attachment folder path** — set to `assets`
2. **Settings → Hotkeys** — search "Download attachments" and bind it (e.g.,
   `Ctrl+Shift+D`)
3. After clipping an article, hit the hotkey to download images locally

### Use graph view

Obsidian's graph view (`Cmd/Ctrl+G`) shows the shape of your wiki — what's
connected to what, which pages are hubs, which are orphans. It's the best way
to see your knowledge base grow over time.

### Add community plugins (optional)

These Obsidian community plugins enhance the llm-wiki experience:

- **[Dataview](https://github.com/blacksmithgu/obsidian-dataview)** — Query
  your wiki programmatically using frontmatter fields. Create dynamic lists of
  pages by type, tag, or timestamp.
- **[Templater](https://github.com/SilentVoid13/Templater)** — More powerful
  templates with scripting, file creation prompts, and dynamic dates. Replace
  the core Templates plugin if you need more control.
- **[Marp Slides](https://github.com/samuele-cozzi/obsidian-marp-slides)** —
  Generate slide decks from your wiki pages for presentations.

### Use git for version history

```bash
cd my-wiki
git init
git add -A
git commit -m "Initial wiki setup"
```

Commit after each ingest session. `git log` gives you a history of how your
knowledge base evolved. `git diff` shows exactly what changed.

### Create additional bundles

For separate knowledge domains, create additional bundles. Each bundle is a
self-contained Obsidian vault with its own directory structure, Obsidian
configuration, templates, and index/log files.

**Option A: Use the shell script**

```bash
./scripts/create-bundle.sh research
```

This creates `bundles/research/` with the complete bundle structure — directories,
Obsidian config, templates, and initial `index.md`/`log.md` files. Ready to open
in Obsidian immediately.

**Option B: Use the agent skill**

If your LLM agent supports skills, invoke:

```
/create-bundle research
```

The agent will scaffold the same complete structure that the shell script creates.

**Option C: Manual setup**

```bash
mkdir -p bundles/research/{.obsidian,templates,raw,sources,entities,concepts,synthesis}
for f in app.json appearance.json core-plugins.json community-plugins.json templates.json; do
  cp bundles/main/.obsidian/"$f" bundles/research/.obsidian/
done
cp bundles/main/templates/*.md bundles/research/templates/
# Then create index.md, log.md, and directory index files manually
```

Open `bundles/research/` as a separate Obsidian vault for your research domain.

## Troubleshooting

**Templates not working?**
Check Settings → Core plugins → Templates is enabled, and the template folder
is set to `templates`.

**Agent doesn't understand the structure?**
Verify `AGENT.md` is in the repository root. Some agents need it at the
directory where you run them. Share the contents directly if needed.

**Links not working in Obsidian?**
Make sure you opened `bundles/main/` as the vault (not the repo root).
Bundle-relative links like `/sources/foo.md` resolve from the vault root.

**Want to change the directory structure?**
Edit `SPEC.md` and `AGENT.md` to document your changes. The spec is a living
document — customize it to your domain.
