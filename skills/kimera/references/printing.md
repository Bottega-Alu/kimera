# Printing and diagnosis

## Verification scope

`render.py FILE.md --verify` produces HTML and a PDF using Playwright Chromium
print media and CSS @page, then measures the PDF with PyMuPDF. Without `--verify`
it produces HTML only (`NOT VERIFIED`).

`VERIFIED` means the eight automated checks passed. It does not certify visual
quality or exact fidelity to the original source. JSON includes
`verification_scope` and `visual_review`; the renderer performs no visual review.

| Check | Scope |
|---|---|
| `paper-size` | requested dimensions within 0.5 mm |
| `page-count` | pages exist; none without both text and drawings |
| `body-bounds` | text blocks within 16 / 18 / 22 / 18 mm margins |
| `footer` | numbering and left string on every page, at least 3 mm below body |
| `content-preserved` | unique words of 4+ characters from rendered HTML appear in PDF body |
| `source-support` | parser output versus sanitised HTML: images fail; stripped tags warn |
| `no-leaked-tokens` | no renderer tokens or unconverted page-break directives |
| `chromium-version` | Chromium 131 or newer |

`content-preserved` does not check order, repetition counts, short words/numbers
or original-source equality. The character ratio is informational. Text removed
before HTML rendering cannot be detected by this check. `source-support` covers
sanitisation, not every possible Markdown parsing ambiguity.

## Failures

Exit 1: a check failed. Apply one content-preserving formatting correction and
rerun once. Keep unresolved artifacts labelled as failing. Never remove data,
columns or required figures to obtain a pass.

| Diagnosis | Action |
|---|---|
| `horizontal-overflow` | reflow the table or block while preserving content |
| `footer-intrusion`, `missing-tokens` | split the affected block without rewriting it |
| `blank-page` | remove an unnecessary forced break |
| `unsupported-image` | preserve the source image; report unsupported output |
| `footer-wrong`, `paper-wrong`, `top-overflow` | report renderer bug; no content workaround |
| `chromium-old` | run `scripts/setup.ps1` once |

Exit 2: input or internal error; inspect JSON stderr and correct the cause before
retrying. Exit 3: missing runtime; run setup once. Do not loop on unchanged errors.

## Manual printing

Prefer the generated PDF, already paginated. For HTML, use current Chromium,
matching paper size, 100% scale, Default margins, and browser headers/footers off.
The HTML scrolls continuously on screen; pagination happens only when printing.
Word/LibreOffice layout fidelity is unsupported.

## Runtime

Setup creates a shared venv at `%LOCALAPPDATA%\kimera\venv`; `python.txt` records
its machine-specific interpreter. Bootstrap tries the current interpreter,
`KIMERA_PYTHON`, `python.txt`, then the default venv. An invalid explicit override
fails when bootstrap reaches it. `scripts/setup.ps1 [-Python -3.11]
[-VenvPath PATH] [-Force]` is idempotent.
