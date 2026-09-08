# Printing, verification and diagnosis

## What `--verify` does

`render.py FILE.md --verify` writes the HTML, drives Chromium through Playwright
(`emulate_media(print)`, `page.pdf(prefer_css_page_size=True, print_background=True,
display_header_footer=False)`), saves the PDF next to the HTML, and then measures
the PDF itself with PyMuPDF. Pagination is entirely the print engine's job: the
renderer never estimates a page height.

Without `--verify` only the HTML is produced and the summary says
`NOT VERIFIED`. Say so when delivering.

Exit codes: `0` fine, `1` a check failed, `2` internal error, `3` runtime missing.

## The seven checks

| Check | What it proves |
|---|---|
| `paper-size` | every page is the requested format within 0.5 mm |
| `page-count` | at least one page, and no page that carries neither text nor drawing |
| `body-bounds` | every text block sits inside the 16 / 18 / 22 / 18 mm text area |
| `footer` | `Pagina N di M` and the left string on every page, at least 3 mm below the body, and nothing else in that band |
| `content-preserved` | every word of 4+ characters in the source is present in the PDF body |
| `no-leaked-tokens` | no internal renderer token and no unconverted `\pagebreak` |
| `chromium-version` | Chromium 131 or newer produced the file |

`content-preserved` is an inclusion test, not a count: the table header repeats on
every page, so counting would be wrong. The character ratio it prints is
indicative only.

## Reading a failure

The summary prints a `diagnosis` block. Apply the content-side remedy once, then
re-render once. If it still fails, deliver and state the residual problem - do
not loop, and never "fix" it by shrinking margins or fonts.

| Failure | Cause and remedy |
|---|---|
| `horizontal-overflow` | an unbreakable table header or an extremely wide table. Shorten the header, drop a column, move long text out of the table. |
| `footer-intrusion` | an unbreakable block reaching into the footer band. Split it into shorter blocks. Persisting means a renderer bug: report it. |
| `blank-page` | a forced break, most often a `\pagebreak`. Remove it. |
| `missing-tokens` | text lost to sanitisation: raw HTML, or an image. Rewrite that part in plain Markdown. |
| `footer-wrong`, `paper-wrong`, `top-overflow` | renderer bugs. Not fixable from the content: deliver and report. |
| `chromium-old` | run `scripts/setup.ps1` again. |

## Printing by hand

The `.md.html` is a single self-contained file: open it in a browser and it
scrolls continuously, with no simulated pages. The pagination only materialises
when printing, driven by the `@page` rule embedded in the file.

To print the HTML yourself:

1. Open it in an up-to-date Chromium-based browser (Chrome, Edge, Brave).
2. `Ctrl+P`.
3. Paper size: the same as `--paper` (A4 by default).
4. Scale: 100%, not "fit to page".
5. Margins: **Default** - the `@page` rule already sets 16 / 18 / 22 / 18 mm.
   Do not select "None": that duplicates nothing and only risks clipping.
6. Turn **off** the browser's own headers and footers, otherwise the browser URL
   and date print on top of the Kimera footer.

Printing the `.pdf` produced by `--verify` needs none of this: it is already
paginated. Prefer it whenever you can.

## Runtime

Dependencies live in one dedicated virtualenv, by default
`%LOCALAPPDATA%\kimera\venv`, created by `scripts/setup.ps1` and shared by every
installation of the skill. `python.txt` in the skill root records the absolute
path of that interpreter; it is machine-specific and not committed.

`render.py` bootstraps itself: current interpreter if it already has the
dependencies, then `KIMERA_PYTHON`, then `python.txt`, then the default venv
path. A `KIMERA_PYTHON` that does not resolve is a hard error rather than a
silent fallback. When nothing resolves it prints a structured JSON error on
stderr and exits 3.

`scripts/setup.ps1 [-Python -3.11] [-VenvPath PATH] [-Force]` is idempotent.
