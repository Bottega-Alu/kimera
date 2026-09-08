# Authoring a Kimera document

The source is plain Markdown, parsed by Python-Markdown and then run through an
nh3 allowlist. Anything outside the allowlist is dropped while its text is kept,
so nothing silently disappears from the page - but a construct that is not
supported will simply not be styled.

## Front matter

Optional. It must sit on the very first lines, one `Key: value` per line,
followed by a blank line. CLI flags always win.

```
Title: Stato della piattaforma Atlante
Subtitle: Memo di stato, sprint 24
Project: Atlante
Author: Squadra Piattaforma
Date: 2026-09-08
Label: Memo di stato
Lang: it
Paper: A4
Confidential: Distribuzione interna.
```

`Label` is the small uppercase kicker above the title. `Confidential` prints one
line at the end of the document - only ever use it when the user asked for it.
Nothing is mandatory and nothing is invented: a missing field simply does not
appear.

The title is resolved as `--title`, then front matter, then the first `# H1` of
the document, then the file name. When the title comes from the first `# H1`
(or matches it) that heading is removed from the body so it is not printed twice.

Because front matter is detected on the first lines, a document that genuinely
starts with a line like `Nota: qualcosa` will have it swallowed as metadata.
Insert a blank line or a heading first.

## Supported syntax

| Construct | Notes |
|---|---|
| `#` to `######` | `#` inside the body renders as a section title, not the document title |
| paragraphs, `**bold**`, `*italic*`, `~~strikethrough~~` | |
| `- ` / `1. ` lists, nested | sane list parsing, mixed nesting works |
| tables (GFM pipe syntax) | header repeats on every page; `:---:` / `---:` alignment honoured |
| fenced code ``` ``` ``` | no syntax highlighting, wraps instead of overflowing |
| inline `` `code` `` | |
| `> ` blockquote | |
| links `[text](https://...)` and `<https://...>` | only `http`, `https` and `mailto` survive |
| footnotes `[^1]` | collected at the end of the document |
| definition lists (`Term` / `:   definition`) | |
| abbreviations (`*[API]: Application ...`) | |

## Callouts

Python-Markdown admonition syntax. The body must be indented by four spaces.

```
!!! warning "Titolo del callout"
    Corpo del callout, su una o piu righe.
```

Styled types: `note`, `info`, `tip`, `success`, `warning`, `danger`, `error`.
Any other type still renders, in the neutral grey style. Omit the quoted title
and the type name is used as the title.

## Page breaks

A line containing only `\pagebreak` (or `\newpage`), outside code fences, starts
a new page. A trailing one is ignored so it cannot produce a blank last page.

Use it sparingly: a forced break in the middle of a document usually leaves a
large empty area on the previous page. Let the print engine paginate.

## Not supported

- **Raw HTML.** Tags are removed and the text between them is kept — except for
  `script` and `style`, whose contents are discarded entirely. `javascript:`
  links, event handlers, ids and inline styles are stripped. Write Markdown; the
  `content-preserved` check will flag anything that was actually lost.
- **Images.** There is no `img` support in this version; describe or link instead.
- **Custom classes, ids, inline styles.** Only the classes the renderer itself
  produces survive the sanitiser.
- **Syntax highlighting** in code blocks.
- **Word / LibreOffice fidelity.** The `.md.html` opens in those applications
  because it is HTML, but the print layout is only guaranteed in Chromium.

## Things that break the page, and what to do

Long unbroken strings (URLs, hashes, base64) wrap anywhere, including inside
table cells and code blocks, so they do not overflow. What can still overflow is
a **table header** that is one very long word: headers keep normal word breaking
on purpose, so that a column is never squeezed to a single character. Shorten the
header.

A table with many columns of long text will get cramped. Fewer columns, or move
the long text out of the table.
