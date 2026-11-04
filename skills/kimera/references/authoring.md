# Authoring

Use Markdown, parsed by Python-Markdown and sanitised by nh3.

## Metadata

Optional known keys on the first lines, one value per line, then a blank line:

```text
Title: Stato della piattaforma
Subtitle: Sprint 24
Project: Atlante
Author: Squadra Piattaforma
Date: 2026-09-08
Label: Memo
Lang: it
Paper: A4
Confidential: Distribuzione interna.
```

Use only supplied or known values; add `Confidential` only when requested.
`Label` is the kicker above the title. CLI flags override metadata.
Unknown keys (`Nota: qualcosa`), duplicate keys and ordinary lines end metadata
parsing and remain in the body. A leading blank line makes even `Title:` literal
body text. Multiline metadata values are unsupported.

Title priority: `--title`, metadata, first H1, filename. The first H1 is removed
from the body only when used as the title or matching the explicit title.

## Syntax

- Headings H1-H6, paragraphs, bold, italic, `~~strike~~` (single `~` stays literal).
- Nested lists: four bullet styles; ordered lists preserve their starting number.
- Pipe tables: repeated headers; colon-based column alignment is honoured.
- Fenced and inline code: wrapping, without syntax highlighting.
- Blockquotes, footnotes collected at the end, definition lists and abbreviations.
- Links: absolute `http`, `https`, `mailto`, plus relative and protocol-relative
  links. Check relative destinations yourself.

Callouts use Python-Markdown syntax with a four-space indented body:

```text
!!! warning "Titolo"
    Corpo del callout.
```

Styled types: `note`, `info`, `tip`, `success`, `warning`, `danger`, `error`.
Other types use neutral styling; omitted titles default to the type name.

## Page breaks

A standalone `\pagebreak` or `\newpage` outside fenced code starts a page.
Leading/trailing breaks are removed; consecutive breaks collapse. In a list,
a break splits the list in two. Literal examples inside code are preserved.
Use sparingly: forced breaks can leave large empty areas.

## Limits

Images are unsupported and make `source-support` fail. Preserve required images
in the source and report the limitation; do not remove them to pass verification.

Raw HTML is unsupported as an authoring interface. The sanitiser removes tags
outside its allowlist, generally retaining text; `script` and `style` contents
are discarded. Event handlers, inline styles, ids and unsafe URL schemes are
stripped. Allowed tags and renderer class names can survive in raw HTML, so a
handwritten admonition or page-break class can still affect layout.

Long strings wrap in body text, code and table cells. Table headers retain normal
word breaking and can overflow. Reflow the table without dropping information;
shorten wording only when the user's content requirements permit it. Many wide
columns can remain cramped even when automated bounds checks pass.

Print layout targets Chromium; Word/LibreOffice fidelity is unsupported.
