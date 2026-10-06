---
name: llm-wiki
description: Maintain the project's LLM Wiki — a persistent, interlinked markdown knowledge base built from sources in raw/. Use when the user says "ingest", "add this to the wiki", "file this source", "ask the wiki", "what does the wiki say about", "lint the wiki", or "wiki health check".
---

# LLM Wiki

Based on Andrej Karpathy's LLM Wiki idea (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
Instead of re-researching sources every time, you build and keep up a wiki that grows with each source.
The user picks sources and asks questions; you do all the bookkeeping.

## Layout (paths relative to the project root)

- `raw/` — source documents (articles, transcripts, PDFs, notes, images). **Read only. Never edit or delete.**
- `wiki/` — markdown pages you write and maintain.
  - `wiki/index.md` — catalog of every page: `- [[page-name]] — one-line summary (category, updated YYYY-MM-DD)`, grouped by category.
  - `wiki/log.md` — append-only history. One heading per event: `## [YYYY-MM-DD] ingest | Title`, `## [YYYY-MM-DD] query | Question`, `## [YYYY-MM-DD] lint | Summary`.
  - `wiki/sources/` — one summary page per raw source.
  - `wiki/concepts/` — ideas, techniques, topics.
  - `wiki/entities/` — people, companies, tools, products.
  - `wiki/syntheses/` — comparisons, analyses and answers worth keeping.

## Page conventions

- File names: lowercase-kebab-case `.md`. Link with `[[page-name]]` (Obsidian style).
- Start each page with frontmatter: `title`, `type` (source | concept | entity | synthesis), `sources` (list of raw/ files), `updated` (date).
- Plain, jargon-free language. Bullet points over paragraphs.
- Every claim traces to a source: cite as `(source: [[source-page]])`.
- When sources disagree, keep both claims, note the conflict and which is newer. Never silently overwrite.
- End each page with a `## Related` list of links.

## Operations

### Ingest
1. Read the new file(s) in `raw/` (or the URL/text the user gives — save it to `raw/` first, with the URL at the top).
2. Write `wiki/sources/<name>.md`: summary, key points, notable quotes (short), open questions.
3. Update or create the concept and entity pages it touches (often 5–15 pages). Add cross-links both ways.
4. Update `wiki/index.md` and append to `wiki/log.md`.
5. Report back in bullets: pages created, pages updated, conflicts found.

### Query
1. Read `wiki/index.md` first, then only the relevant pages. Go to `raw/` only if the wiki is missing detail.
2. Answer with citations to wiki pages.
3. If the answer is a useful comparison or analysis, offer to save it in `wiki/syntheses/`. Log the query.

### Lint
Check for and report (fix only with the user's OK):
- contradictions between pages
- claims made stale by newer sources
- orphan pages (no inbound links) and broken `[[links]]`
- pages missing from `index.md`
- concepts mentioned often that deserve their own page
- raw files never ingested
Log the lint pass.

## Rules
- Never modify `raw/`.
- Never delete wiki pages without asking.
- Deliverables made *from* the wiki (reports, drafts) go to `output/`, not `wiki/`.
