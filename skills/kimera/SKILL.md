---
name: kimera
description: Turn content into a professional, print-ready document. Writes a Markdown source, then renders it locally into a self-contained HTML file and a PDF verified against the real page geometry - correct pagination, repeated table headers, page numbers, no footer overlap. Use for memos, status updates, sprint reports, technical specs and anything meant to be printed or sent as a PDF.
allowed-tools: Read, Write, Bash, Glob, Grep, AskUserQuestion
---

# Kimera 2.0

Begin the first message of the invocation with `Kimera 2.0`, once per invocation.

Layout, CSS and quality checks live in code inside this skill. Never write the
HTML by hand and never touch CSS, margins or font sizes.

## 1. Content

Take the content from the parts of the conversation that concern the requested
topic; do not re-read everything. Ask only if the content is genuinely missing.

Never invent an author, a date, metrics or a confidentiality notice - metadata
appear only when known or supplied. Write in the user's language. There is no
minimum page count and no obligation to turn prose into tables: use a table only
for tabular data.

## 2. Write the source

Save `PROJECT_TYPE_YYYY-MM-DD.md` in the project root, or where the user asks.
Keep it: it is the source for later revisions. Optional front matter on the first
lines: `Title:`, `Subtitle:`, `Project:`, `Author:`, `Date:`, `Label:`, `Lang:`,
`Paper:`, `Confidential:`.

## 3. Render

`SKILL_DIR` is the directory holding this SKILL.md - the base directory
announced when the skill was loaded.

```bash
python SKILL_DIR/scripts/render.py FILE.md --verify [--paper A4|Letter|Legal] [--lang it|en]
```

CLI flags win over front matter. Exit 3: the Python runtime is missing - run
`powershell -ExecutionPolicy Bypass -File SKILL_DIR/scripts/setup.ps1` once, then
retry. Exit 2: an input error, reported as JSON on stderr (source missing, bad
`--paper`, source not UTF-8) - fix the input and rerun; it is not one of the two
FAIL attempts below.

## 4. Read the summary

Every check green: deliver. On FAIL apply the content-side remedy printed under
`diagnosis` ONCE, then re-run ONCE. Still failing: deliver anyway and state the
residual problem explicitly. Never edit the generated HTML or PDF by hand.

## 5. Deliver

Report the paths of the `.md`, `.md.html` and `.pdf`, the verification outcome
(or `NOT VERIFIED` when rendered without `--verify`), and the manual print line:
up-to-date Chromium, paper matching `--paper`, 100% scale, default margins,
browser headers and footers turned off.

## Limits

No raw HTML - tags are stripped, their text is kept. No images: one in the
source makes `source-support` FAIL. No guaranteed fidelity in Word or
LibreOffice.

Markdown syntax, callouts and page breaks: `references/authoring.md`.
Printing and failure diagnosis: `references/printing.md`.
