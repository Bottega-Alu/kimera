#!/usr/bin/env python3
"""Kimera 2.0 - verification of the PDF that Chromium actually produced.

Everything here is measured on the real file with PyMuPDF: page geometry, text
block bounding boxes, footer band content and token preservation. Nothing is
estimated from the HTML.

Importable (``verify_pdf``) and runnable as a CLI.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import fitz

MM = 72.0 / 25.4
MIN_CHROMIUM_MAJOR = 131

PAPERS = {
    "A4": (210.0, 297.0),
    "Letter": (215.9, 279.4),
    "Legal": (215.9, 355.6),
}

DEFAULT_MARGINS_MM = {"top": 16.0, "right": 18.0, "bottom": 22.0, "left": 18.0}

PAGE_STRINGS = {
    "it": ("Pagina ", " di "),
    "en": ("Page ", " of "),
}

DIAGNOSIS = {
    "it": {
        "horizontal-overflow": (
            "Overflow orizzontale: una cella di tabella o una riga di codice non spezzabile "
            "esce dall'area di testo. Accorcia o spezza quel contenuto nel Markdown "
            "(nomi/URL lunghi su piu righe, meno colonne). Non toccare margini o font."
        ),
        "footer-intrusion": (
            "Il testo entra nella banda del piè di pagina. Di norma e la conseguenza di un "
            "blocco non frazionabile; riscrivi il contenuto in blocchi piu corti. "
            "Se persiste e un bug del renderer: consegna segnalandolo."
        ),
        "top-overflow": (
            "Testo sopra il margine superiore: elemento fuori flusso. Bug del renderer, "
            "non risolvibile lato contenuto."
        ),
        "blank-page": (
            "Pagina vuota: quasi sempre un `\\pagebreak` finale o un elemento con "
            "interruzione forzata. Rimuovi l'interruzione dal Markdown."
        ),
        "missing-tokens": (
            "Testo perso rispetto al sorgente: HTML grezzo rimosso dalla sanitizzazione, "
            "un'immagine (non supportata in questa versione) o un blocco troncato. "
            "Riscrivi quella parte in Markdown puro."
        ),
        "footer-wrong": (
            "Piè di pagina errato o assente: bug del renderer, non risolvibile lato "
            "contenuto. Consegna segnalando il problema."
        ),
        "paper-wrong": (
            "Formato carta diverso da quello richiesto: bug del renderer o CSS @page "
            "sovrascritto. Consegna segnalando il problema."
        ),
        "leaked-token": (
            "Token interno rimasto nel documento: la direttiva `\\pagebreak` non e stata "
            "convertita. Assicurati che stia da sola su una riga, fuori dai blocchi di codice."
        ),
        "chromium-old": (
            "Chromium troppo vecchio: esegui scripts/setup.ps1 per aggiornare il browser."
        ),
    },
    "en": {
        "horizontal-overflow": (
            "Horizontal overflow: an unbreakable table cell or code line runs past the text "
            "area. Shorten or split that content in the Markdown. Do not touch margins or fonts."
        ),
        "footer-intrusion": (
            "Text reaches into the footer band, usually because of an unbreakable block. "
            "Rewrite it as shorter blocks. If it persists it is a renderer bug: report it."
        ),
        "top-overflow": (
            "Text above the top margin: an element escaped the flow. Renderer bug, not "
            "fixable from the content."
        ),
        "blank-page": (
            "Blank page: almost always a trailing `\\pagebreak` or a forced break. "
            "Remove the break from the Markdown."
        ),
        "missing-tokens": (
            "Text lost with respect to the source: raw HTML removed by sanitisation, an image "
            "(unsupported in this version) or a truncated block. Rewrite that part in plain Markdown."
        ),
        "footer-wrong": (
            "Wrong or missing footer: renderer bug, not fixable from the content. "
            "Deliver while reporting the problem."
        ),
        "paper-wrong": (
            "Paper size differs from the requested one: renderer bug or overridden @page CSS. "
            "Deliver while reporting the problem."
        ),
        "leaked-token": (
            "Internal token left in the document: the `\\pagebreak` directive was not converted. "
            "Make sure it sits alone on its own line, outside code blocks."
        ),
        "chromium-old": "Chromium is too old: run scripts/setup.ps1 to refresh the browser.",
    },
}

_TOKEN_RE = re.compile(r"\w{4,}", re.UNICODE)
_ALNUM_RE = re.compile(r"\w", re.UNICODE)
_LEAK_LINE_RE = re.compile(r"^\s*\\(?:pagebreak|newpage)\s*$")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", text or "").casefold()


def _tokens(text: str) -> set:
    return set(_TOKEN_RE.findall(_norm(text)))


def _flat(text: str) -> str:
    return re.sub(r"\s+", "", _norm(text))


def _text_blocks(page):
    out = []
    for block in page.get_text("blocks"):
        x0, y0, x1, y1, text = block[0], block[1], block[2], block[3], block[4]
        btype = block[6] if len(block) > 6 else 0
        if btype != 0 or not text.strip():
            continue
        out.append((x0, y0, x1, y1, text))
    return out


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _check(name, ok, details):
    return {"name": name, "ok": bool(ok), "details": details}


# --------------------------------------------------------------------------- #
# main entry point
# --------------------------------------------------------------------------- #

def verify_pdf(
    pdf_path,
    *,
    paper="A4",
    width_mm=None,
    height_mm=None,
    margins_mm=None,
    footer_left="",
    lang="it",
    expected_text="",
    chromium_version=None,
    footer_gap_mm=3.0,
    tolerance_pt=1.0,
    paper_tolerance_mm=0.5,
):
    """Run every geometric and textual check on a rendered PDF.

    Returns ``{"ok", "pages", "checks", "diagnosis", "paper", ...}``.
    """
    pdf_path = Path(pdf_path)
    lang = lang if lang in PAGE_STRINGS else "it"
    diag_table = DIAGNOSIS[lang]
    margins = dict(margins_mm or DEFAULT_MARGINS_MM)
    if width_mm is None or height_mm is None:
        width_mm, height_mm = PAPERS.get(paper, PAPERS["A4"])

    checks = []
    diagnosis = []
    seen_diag = set()

    def add_diag(key):
        if key not in seen_diag:
            seen_diag.add(key)
            diagnosis.append(diag_table[key])

    doc = fitz.open(pdf_path)
    total = doc.page_count

    ml = margins["left"] * MM
    mr = margins["right"] * MM
    mt = margins["top"] * MM
    mb = margins["bottom"] * MM
    gap = footer_gap_mm * MM

    # ---------------------------------------------------------- 1 paper-size --
    bad_size = []
    for index in range(total):
        rect = doc[index].rect
        w_mm = rect.width / MM
        h_mm = rect.height / MM
        if (
            abs(w_mm - width_mm) > paper_tolerance_mm
            or abs(h_mm - height_mm) > paper_tolerance_mm
        ):
            bad_size.append("p%d %.2fx%.2fmm" % (index + 1, w_mm, h_mm))
    if bad_size:
        checks.append(
            _check("paper-size", False, "%s expected %.1fx%.1fmm; got %s"
                   % (paper, width_mm, height_mm, ", ".join(bad_size[:5])))
        )
        add_diag("paper-wrong")
    else:
        first = doc[0].rect if total else fitz.Rect(0, 0, 0, 0)
        checks.append(
            _check("paper-size", True, "%s, %d page(s) at %.2fx%.2fmm (+/-%.1fmm)"
                   % (paper, total, first.width / MM, first.height / MM, paper_tolerance_mm))
        )

    # ---------------------------------------------- gather per-page blocks ----
    pages = []
    for index in range(total):
        page = doc[index]
        height = page.rect.height
        body_bottom = height - mb
        body_blocks, footer_blocks = [], []
        for block in _text_blocks(page):
            (footer_blocks if block[1] >= body_bottom else body_blocks).append(block)
        pages.append(
            {
                "page": page,
                "index": index,
                "width": page.rect.width,
                "height": height,
                "body_bottom": body_bottom,
                "body": body_blocks,
                "footer": footer_blocks,
            }
        )

    # ---------------------------------------------------------- 2 page-count --
    blank = []
    for info in pages:
        if info["body"]:
            continue
        if info["page"].get_drawings():
            continue
        blank.append(info["index"] + 1)
    if total < 1:
        checks.append(_check("page-count", False, "the PDF has no pages"))
    elif blank:
        checks.append(
            _check("page-count", False,
                   "%d page(s); blank page(s): %s" % (total, ", ".join(map(str, blank))))
        )
        add_diag("blank-page")
    else:
        checks.append(_check("page-count", True, "%d page(s), none blank" % total))

    # --------------------------------------------------------- 3 body-bounds --
    violations = []
    kinds = set()
    for info in pages:
        left = ml - tolerance_pt
        right = info["width"] - mr + tolerance_pt
        top = mt - tolerance_pt
        bottom = info["body_bottom"] + tolerance_pt
        for x0, y0, x1, y1, text in info["body"]:
            kind = None
            if x1 > right or x0 < left:
                kind = "horizontal-overflow"
            elif y1 > bottom:
                kind = "footer-intrusion"
            elif y0 < top:
                kind = "top-overflow"
            if kind:
                kinds.add(kind)
                violations.append(
                    "p%d %s bbox=(%.1f,%.1f,%.1f,%.1f)pt %r"
                    % (info["index"] + 1, kind, x0, y0, x1, y1, _collapse(text)[:60])
                )
    if violations:
        checks.append(
            _check("body-bounds", False,
                   "%d block(s) outside the text area: %s"
                   % (len(violations), " | ".join(violations[:5])))
        )
        for kind in kinds:
            add_diag(kind)
    else:
        checks.append(
            _check("body-bounds", True,
                   "every text block inside %.0f/%.0f/%.0f/%.0f mm (tol %.1fpt)"
                   % (margins["top"], margins["right"], margins["bottom"], margins["left"],
                      tolerance_pt))
        )

    # -------------------------------------------------------------- 4 footer --
    # Comparisons collapse runs of whitespace (PyMuPDF joins the two margin
    # boxes into one block with a newline) but do NOT delete spaces: a footer
    # rendered as "Pagina1di1" must fail.
    prefix, infix = PAGE_STRINGS[lang]
    footer_problems = []
    min_gap_mm = None
    for info in pages:
        number = info["index"] + 1
        expected = "%s%d%s%d" % (prefix, number, infix, total)
        band = _collapse(" ".join(b[4] for b in info["footer"]))
        if not info["footer"]:
            footer_problems.append("p%d: no footer" % number)
            continue
        top_of_footer = min(b[1] for b in info["footer"])
        this_gap = (top_of_footer - info["body_bottom"]) / MM
        min_gap_mm = this_gap if min_gap_mm is None else min(min_gap_mm, this_gap)
        if expected not in band:
            footer_problems.append("p%d: %r missing from %r" % (number, expected, band[:80]))
            continue
        remainder = _collapse(band.replace(expected, " ", 1))
        if footer_left:
            left_text = _collapse(footer_left)
            stem = remainder.rstrip(".… ")
            if remainder == left_text:
                remainder = ""
            elif stem and left_text.startswith(stem) and remainder != stem:
                remainder = ""  # the left box was ellipsised by text-overflow
            elif left_text and left_text in remainder:
                remainder = _collapse(remainder.replace(left_text, " ", 1))
        if remainder:
            footer_problems.append("p%d: unexpected footer text %r" % (number, remainder[:80]))
        if this_gap < footer_gap_mm:
            footer_problems.append(
                "p%d: footer only %.2fmm below the body (min %.1fmm)" % (number, this_gap, footer_gap_mm)
            )
    if footer_problems:
        checks.append(
            _check("footer", False, "%d problem(s): %s"
                   % (len(footer_problems), " | ".join(footer_problems[:5])))
        )
        add_diag("footer-wrong")
    else:
        checks.append(
            _check("footer", True,
                   "'%s1%s%d' .. '%s%d%s%d' present on every page, %.1fmm below the body"
                   % (prefix, infix, total, prefix, total, infix, total, min_gap_mm or 0.0))
        )

    # -------------------------------------------------- 5 content-preserved --
    body_text = "\n".join(b[4] for info in pages for b in info["body"])
    full_text = "\n".join(doc[i].get_text() for i in range(total))
    if expected_text.strip():
        want = _tokens(expected_text)
        got = _tokens(body_text)
        missing = sorted(want - got)
        if missing:
            flat = _flat(body_text)
            missing = [token for token in missing if token not in flat]
        want_chars = len(_ALNUM_RE.findall(_norm(expected_text)))
        got_chars = len(_ALNUM_RE.findall(_norm(body_text)))
        ratio = (got_chars / want_chars) if want_chars else 1.0
        if missing:
            checks.append(
                _check("content-preserved", False,
                       "%d/%d source token(s) missing from the PDF body (chars %.2fx): %s"
                       % (len(missing), len(want), ratio, ", ".join(missing[:20])))
            )
            add_diag("missing-tokens")
        else:
            checks.append(
                _check("content-preserved", True,
                       "all %d source token(s) present; characters %.2fx source (indicative)"
                       % (len(want), ratio))
            )
    else:
        checks.append(_check("content-preserved", True, "no source text supplied - skipped"))

    # ------------------------------------------------------ 6 leaked tokens --
    leaks = []
    if "KIMERA_" in full_text:
        leaks.append("KIMERA_ token")
    for line in full_text.splitlines():
        if _LEAK_LINE_RE.match(line):
            leaks.append("unconverted %r" % line.strip())
            break
    if leaks:
        checks.append(_check("no-leaked-tokens", False, "; ".join(leaks)))
        add_diag("leaked-token")
    else:
        checks.append(_check("no-leaked-tokens", True, "no renderer token in the PDF"))

    # --------------------------------------------------- 7 chromium version --
    if chromium_version:
        try:
            major = int(str(chromium_version).split(".")[0])
        except (ValueError, IndexError):
            major = 0
        ok = major >= MIN_CHROMIUM_MAJOR
        checks.append(
            _check("chromium-version", ok,
                   "%s (minimum %d)" % (chromium_version, MIN_CHROMIUM_MAJOR))
        )
        if not ok:
            add_diag("chromium-old")
    else:
        checks.append(_check("chromium-version", True, "not reported - standalone run"))

    doc.close()

    return {
        "ok": all(c["ok"] for c in checks),
        "pdf": str(pdf_path.resolve()),
        "paper": paper,
        "pages": total,
        "checks": checks,
        "diagnosis": diagnosis,
        "chromium": chromium_version,
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="verify.py", description="Check a Kimera PDF against the real page geometry."
    )
    parser.add_argument("pdf")
    parser.add_argument("--paper", default="A4", choices=sorted(PAPERS))
    parser.add_argument("--lang", default="it", choices=sorted(PAGE_STRINGS))
    parser.add_argument("--footer-left", default="")
    parser.add_argument("--expected-text-file", help="UTF-8 file with the expected body text.")
    parser.add_argument("--chromium", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    expected = ""
    if args.expected_text_file:
        expected = Path(args.expected_text_file).read_text(encoding="utf-8")

    width_mm, height_mm = PAPERS[args.paper]
    result = verify_pdf(
        args.pdf,
        paper=args.paper,
        width_mm=width_mm,
        height_mm=height_mm,
        footer_left=args.footer_left,
        lang=args.lang,
        expected_text=expected,
        chromium_version=args.chromium,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("%s - %s (%d pages)" % (Path(args.pdf).name,
                                      "VERIFIED" if result["ok"] else "FAILED",
                                      result["pages"]))
        for check in result["checks"]:
            print("  [%s] %-18s %s" % ("ok" if check["ok"] else "FAIL",
                                       check["name"], check["details"]))
        for item in result["diagnosis"]:
            print("  - %s" % item)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
