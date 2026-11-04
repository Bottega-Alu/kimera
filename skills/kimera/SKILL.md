---
name: kimera
description: Render Markdown into self-contained HTML and a paginated PDF with automated layout checks. Use for printable text documents, memos, reports and specifications.
allowed-tools: Read, Write, Bash, Glob, Grep, AskUserQuestion
---

# Kimera

Use the bundled renderer; layout and CSS live in code.
For ordinary documents this file is sufficient. Execute scripts without reading
their implementation. Read references only for the specific need below.

## Source

Use relevant supplied content, in the user's language. Preserve supplied facts,
numbers and wording when fidelity is requested. Never invent metadata or remove
content to make a layout check pass. Use tables only for tabular information.
Save the Markdown source in the requested location (otherwise the project root).

Optional metadata on the first lines: `Title:`, `Subtitle:`, `Project:`, `Author:`,
`Date:`, `Label:`, `Lang:`, `Paper:`, `Confidential:`; then a blank line.
Only known keys are consumed. A leading blank line makes even known keys ordinary
body text. Read [authoring.md](references/authoring.md) for callouts, page breaks,
metadata examples or unsupported syntax. Images are unsupported; preserve the
source and report the limitation when an image is required.

## Render and check

`SKILL_DIR` is the directory containing this file. Quote paths containing spaces.

```bash
python "SKILL_DIR/scripts/render.py" "FILE.md" --verify
```

Optional: `--paper A4|Letter|Legal`, `--lang it|en`; flags override metadata.
Exit 3: run `scripts/setup.ps1` once, then retry. Exit 2: inspect the reported
input or internal error; do not keep retrying an unchanged failing command.

On a failed layout check, apply at most one content-preserving formatting fix
and rerun once. Never delete columns, shorten facts or replace required images
just to pass. If still failing, report the problem with the available artifacts.
Read [printing.md](references/printing.md) only for diagnosis or manual printing.

`VERIFIED` means the automated checks passed, not exact source fidelity or visual
approval. For a final PDF, inspect representative rendered pages when a preview
tool is available, including dense tables and page breaks. State when visual
review was not performed; do not start an open-ended polish loop.

## Deliver

Link the source, HTML and PDF actually produced, with the automated check outcome
and any unresolved limitation. Without `--verify`, only HTML is produced.
Include manual printing instructions only when the user needs to print the HTML.
