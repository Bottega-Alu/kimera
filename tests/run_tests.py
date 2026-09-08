#!/usr/bin/env python3
"""Kimera 2.0 end-to-end test suite (no pytest).

Generates six Markdown fixtures full of unique MRK-#### markers, renders each of
them on A4, Letter and Legal through the real CLI, and then checks the PDF that
Chromium actually produced:

  * every verify.py check must pass;
  * every marker must appear EXACTLY once in the PDF (catches both dropped and
    duplicated content - a repeated table header must not duplicate body text);
  * fixtures that cannot fit on one page must really span several pages.

It also renders examples/demo-it.md when present, exports PNGs of representative
pages for visual inspection, and writes tests/results/test-results.json with the
measured timings.

    python tests/run_tests.py            # exit 0 only if everything passes
    python tests/run_tests.py --keep     # do not clear tests/results first
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = REPO_ROOT / "skills" / "kimera"
RENDER = SKILL_ROOT / "scripts" / "render.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures"
RESULTS = REPO_ROOT / "tests" / "results"
PNG_DIR = RESULTS / "png"
DEMO = REPO_ROOT / "examples" / "demo-it.md"

PAPERS = ("A4", "Letter", "Legal")


# --------------------------------------------------------------------------- #
# Minimal runtime bootstrap (the suite itself needs PyMuPDF)
# --------------------------------------------------------------------------- #

def _resolve_runtime() -> Path:
    from importlib.util import find_spec

    if find_spec("fitz") is not None:
        return Path(sys.executable)
    candidates = []
    override = (os.environ.get("KIMERA_PYTHON") or "").strip().strip('"')
    if override:
        candidates.append(Path(override))
    marker = SKILL_ROOT / "python.txt"
    if marker.is_file():
        for line in marker.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                candidates.append(Path(line))
                break
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "kimera" / "venv" / "Scripts" / "python.exe")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    sys.stderr.write(
        "Kimera runtime not found. Run: powershell -ExecutionPolicy Bypass -File "
        '"%s"\n' % (SKILL_ROOT / "scripts" / "setup.ps1")
    )
    raise SystemExit(3)


PYTHON = _resolve_runtime()
if Path(sys.executable) != PYTHON and os.environ.get("KIMERA_TESTS_BOOTSTRAPPED") != "1":
    env = dict(os.environ, KIMERA_TESTS_BOOTSTRAPPED="1")
    raise SystemExit(
        subprocess.run([str(PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]], env=env).returncode
    )

import re          # noqa: E402
import shutil      # noqa: E402
import time        # noqa: E402
from datetime import datetime, timezone  # noqa: E402

import fitz        # noqa: E402


# --------------------------------------------------------------------------- #
# Fixture generation
# --------------------------------------------------------------------------- #

_counter = {"n": 0}


def mark() -> str:
    _counter["n"] += 1
    return "MRK-%04d" % _counter["n"]


LOREM = (
    "La pipeline di rendering delega l'impaginazione al motore di stampa e non "
    "stima mai l'altezza delle pagine; ogni blocco di testo puo continuare sulla "
    "pagina successiva senza perdere contenuto, anche quando la sorgente contiene "
    "paragrafi molto lunghi, tabelle estese o blocchi di codice. "
)


def fixture_short() -> str:
    m = [mark() for _ in range(9)]
    return f"""Title: Documento breve realistico
Subtitle: Fixture (a) - struttura mista
Project: Kimera Test Suite
Label: Fixture A

# Documento breve realistico

Paragrafo introduttivo {m[0]} con **grassetto**, *corsivo*, `codice inline`
e un [collegamento](https://example.org/documentazione/guida).

## Stato dei componenti

| Componente | Stato | Nota |
|---|---|---|
| Renderer | Attivo | {m[1]} |
| Verifica | Attivo | {m[2]} |
| Runtime | Attivo | {m[3]} |

### Elenco delle attivita

1. Prima attivita {m[4]}
2. Seconda attivita con sotto-elenco:
   - dettaglio uno {m[5]}
   - dettaglio due
3. Terza attivita

!!! warning "Rischio residuo"
    Callout di prova {m[6]} con accenti: perche, citta, piu, cosi.

> Citazione con virgolette caporali e trattino lungo. {m[7]}

```python
def render(source: str) -> str:
    # {m[8]}
    return source.upper()
```

\\pagebreak

## Sezione dopo interruzione

Questa sezione comincia su una nuova pagina perche la sorgente contiene una
interruzione esplicita. L'interruzione finale che segue non deve produrre una
pagina vuota.

\\pagebreak
"""


def fixture_long_table() -> str:
    rows = []
    for i in range(1, 81):
        rows.append(
            "| R-%03d | %s | Voce di riepilogo numero %d con testo sufficiente a "
            "riempire la cella | %d,%02d |" % (i, mark(), i, i * 37, i % 100)
        )
    body = "\n".join(rows)
    return f"""Title: Tabella multipagina
Subtitle: Fixture (b) - 80 righe, intestazione ripetuta
Project: Kimera Test Suite
Label: Fixture B

# Tabella multipagina

| Riferimento | Marcatore | Descrizione | Valore |
|---|---|---|---|
{body}

Paragrafo di chiusura dopo la tabella.
"""


def fixture_tall_row() -> str:
    marks = [mark() for _ in range(6)]
    chunks = []
    for i in range(150):
        if i == 0:
            chunks.append(marks[0])
        elif i == 30:
            chunks.append(marks[1])
        elif i == 70:
            chunks.append(marks[2])
        elif i == 110:
            chunks.append(marks[3])
        elif i == 149:
            chunks.append(marks[4])
        chunks.append(
            "Riga interna numero %d della cella molto alta, con testo continuo che "
            "obbliga il motore di stampa a spezzare la riga di tabella." % (i + 1)
        )
    cell = " ".join(chunks)
    return f"""Title: Riga di tabella piu alta della pagina
Subtitle: Fixture (c) - una sola riga, molte pagine
Project: Kimera Test Suite
Label: Fixture C

# Riga di tabella piu alta della pagina

| Voce | Contenuto |
|---|---|
| Cella unica {marks[5]} | {cell} |

Paragrafo dopo la tabella.
"""


def fixture_long_paragraph() -> str:
    marks = [mark() for _ in range(5)]
    at = {0: 0, 20: 1, 40: 2, 60: 3, 69: 4}
    parts = []
    for i in range(70):
        if i in at:
            parts.append(marks[at[i]])
        parts.append(LOREM.strip())
    return f"""Title: Paragrafo piu lungo di una pagina
Subtitle: Fixture (d) - nessun a capo
Project: Kimera Test Suite
Label: Fixture D

# Paragrafo piu lungo di una pagina

{" ".join(parts)}
"""


def fixture_code() -> str:
    lines = []
    for i in range(1, 201):
        if i % 40 == 1:
            lines.append("# %s" % mark())
        lines.append(
            "def funzione_%03d(parametro_uno, parametro_due=None):  # riga %d"
            % (i, i)
        )
    code = "\n".join(lines)
    return f"""Title: Blocco di codice multipagina
Subtitle: Fixture (e) - 200 righe
Project: Kimera Test Suite
Label: Fixture E

# Blocco di codice multipagina

```python
{code}
```

Paragrafo dopo il blocco di codice.
"""


def fixture_long_lines() -> str:
    marks = [mark() for _ in range(6)]
    url = "https://esempio.test/" + "segmento-molto-lungo/" * 13 + "fine?a=1&b=2"
    blob = "X" * 400
    accents = "àèéìòùÀÈÉ ß € « » — ’ “ ” 中文 œ Æ ñ ç"
    return f"""Title: Righe lunghe e caratteri accentati
Subtitle: Fixture (f) - overflow orizzontale
Project: Kimera Test Suite
Label: Fixture F

# Righe lunghe e caratteri accentati

Paragrafo con un URL molto lungo {marks[0]}: <{url}>

Stringa senza spazi {marks[1]}: {blob}

Caratteri {marks[2]}: {accents}

| Colonna | Contenuto lungo |
|---|---|
| URL {marks[3]} | {url} |
| Blob | {blob} |
| Accenti | {accents} |

```text
{marks[4]} {url}
{blob}
{accents}
```

Chiusura {marks[5]}.
"""


def fixture_pagebreaks() -> str:
    """Regression for I-1 and I-2 (page-break normalisation and false leak)."""
    m = [mark() for _ in range(6)]
    fence = "```\n\\pagebreak\n```"
    return f"""Title: Interruzioni di pagina
Project: Kimera Test Suite
Label: Fixture G

\\pagebreak

# Interruzioni di pagina

Primo paragrafo {m[0]}, preceduto da una interruzione iniziale che va ignorata.

\\pagebreak
\\pagebreak

Dopo due interruzioni consecutive {m[1]}: devono valere per una sola.

- primo elemento {m[2]}
\\pagebreak
- secondo elemento dopo una interruzione dentro la lista {m[3]}

Dentro un blocco di codice la direttiva deve restare testo visibile {m[4]}:

{fence}

Ultimo paragrafo {m[5]}, seguito da una interruzione finale da ignorare.

\\pagebreak
"""


def fixture_image() -> str:
    """Regression for I-3: an image must FAIL, not disappear silently."""
    m = [mark() for _ in range(2)]
    return f"""Title: Documento con immagine
Project: Kimera Test Suite
Label: Fixture H

# Documento con immagine

Paragrafo prima della figura {m[0]}.

![Diagramma ALTTESTOPERSO della piattaforma](figura.png)

Paragrafo dopo la figura {m[1]}.
"""


def fixture_raw_html() -> str:
    """Regression for I-3 (warn) and M-4 (classes surviving from raw HTML)."""
    m = [mark() for _ in range(5)]
    return f"""Title: Sanitizzazione HTML grezzo
Project: Kimera Test Suite
Label: Fixture I

# Sanitizzazione {m[0]}

<script>var perso = "SCRIPTLEAKTEST";</script>

<style>body {{ display: none }} /* STYLELEAKTEST */</style>

<iframe src="https://esempio.test/IFRAMELEAKTEST"></iframe>

<div style="position:fixed;top:0">Div con stile rimosso {m[1]}</div>

<a href="javascript:alert(1)">Link neutralizzato {m[2]}</a>

<p class="page-break">Classe consentita da HTML grezzo {m[3]}</p>

Fine del documento {m[4]}.
"""


def fixture_syntax() -> str:
    """Regression for I-4 (~~del~~) and M-3 (ol start) and M-8 (list levels)."""
    m = [mark() for _ in range(9)]
    return f"""Title: Sintassi ricca
Project: Kimera Test Suite
Label: Fixture J

# Sintassi ricca

- Livello uno {m[0]}
    - Livello due {m[1]}
        - Livello tre {m[2]}
            - Livello quattro {m[3]}

7. settimo {m[4]}
8. ottavo {m[5]}
9. nono {m[6]}

Testo con ~~barrato {m[7]}~~ e una nota[^n].

[^n]: Corpo della nota {m[8]}.
"""


# (name, builder, min_pages, options)
FIXTURE_BUILDERS = [
    ("a-short-doc", fixture_short, 1, {}),
    ("b-table-80-rows", fixture_long_table, 2, {}),
    ("c-tall-table-row", fixture_tall_row, 2, {}),
    ("d-long-paragraph", fixture_long_paragraph, 2, {}),
    ("e-code-200-lines", fixture_code, 2, {}),
    ("f-long-lines", fixture_long_lines, 1, {}),
    ("g-pagebreaks", fixture_pagebreaks, 3, {
        "assert_pdf_text": [("\\pagebreak", 1), ("KIMERA_", 0)],
        "assert_html_absent": ["KIMERA_"],
        "max_pages": 3,
    }),
    ("h-image", fixture_image, 1, {
        "expect_fail_check": "source-support",
        "assert_diagnosis": "mmagini non supportate",
    }),
    ("i-raw-html", fixture_raw_html, 1, {
        "expect_warn_check": "source-support",
        # NB: the template always embeds one legitimate <style> block, so the
        # assertion targets the smuggled payloads, not the tag names.
        "assert_html_absent": [
            "<script", "<iframe", "onerror", "javascript:", "position:fixed",
            "SCRIPTLEAKTEST", "STYLELEAKTEST", "IFRAMELEAKTEST",
        ],
        "assert_html": ['class="page-break"'],
        "assert_pdf_text": [("SCRIPTLEAKTEST", 0), ("STYLELEAKTEST", 0), ("IFRAMELEAKTEST", 0)],
        "min_pages": 2,
    }),
    ("j-rich-syntax", fixture_syntax, 1, {
        "assert_html": ['<ol start="7">', "<del>"],
        "assert_pdf_text": [("~~", 0), ("settimo", 1)],
    }),
]

_MARK_RE = re.compile(r"MRK-\d{4}")


# --------------------------------------------------------------------------- #
# Running
# --------------------------------------------------------------------------- #

def flat_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    text = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    doc.close()
    # Long tokens can be broken across lines by overflow-wrap: anywhere.
    return re.sub(r"\s+", "", text)


def export_pngs(pdf_path: Path, stem: str, all_pages: bool = False):
    doc = fitz.open(pdf_path)
    total = doc.page_count
    if all_pages:
        wanted = list(range(total))
    else:
        wanted = sorted({0, max(0, total // 2), total - 1})
    saved = []
    for index in wanted:
        out = PNG_DIR / ("%s-p%02d.png" % (stem, index + 1))
        doc[index].get_pixmap(dpi=70).save(out)
        saved.append(str(out))
    doc.close()
    return saved


def run_case(name: str, source: Path, paper: str, expected_marks, min_pages: int,
             all_pages_png: bool = False, opts=None) -> dict:
    opts = opts or {}
    expect_fail = opts.get("expect_fail_check")
    stem = "%s-%s" % (name, paper.lower())
    out_html = RESULTS / (stem + ".md.html")
    report_path = RESULTS / (stem + ".report.json")
    cmd = [
        str(PYTHON), str(RENDER), str(source),
        "--out", str(out_html),
        "--paper", paper,
        "--verify",
        "--report", str(report_path),
    ]
    started = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    wall = time.perf_counter() - started

    case = {
        "fixture": name,
        "paper": paper,
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "wall_s": round(wall, 3),
        "problems": [],
    }
    wanted_exit = 1 if expect_fail else 0
    if proc.returncode != wanted_exit:
        case["problems"].append(
            "render.py exited %d, expected %d" % (proc.returncode, wanted_exit)
        )
        if not report_path.is_file():
            case["stderr"] = (proc.stderr or "")[-2000:]
            case["stdout"] = (proc.stdout or "")[-2000:]
            case["ok"] = False
            return case

    report = json.loads(report_path.read_text(encoding="utf-8"))
    case["checks"] = report["checks"]
    case["pages"] = report["pages"]
    case["timings_s"] = report["timings_s"]
    case["chromium"] = report.get("chromium")
    case["pdf"] = report["pdf"]
    case["source_support"] = report.get("source_support")

    seen_expected_failure = False
    for check in report["checks"]:
        if expect_fail and check["name"] == expect_fail:
            seen_expected_failure = True
            if check["ok"]:
                case["problems"].append(
                    "check %s was expected to FAIL but passed" % expect_fail
                )
            continue
        if not check["ok"]:
            case["problems"].append("check %s: %s" % (check["name"], check["details"]))
    if expect_fail and not seen_expected_failure:
        case["problems"].append("check %s never ran" % expect_fail)

    warn_name = opts.get("expect_warn_check")
    if warn_name:
        warned = [
            c for c in report["checks"]
            if c["name"] == warn_name and c["ok"] and c.get("level") == "warn"
        ]
        if not warned:
            case["problems"].append("check %s was expected to warn" % warn_name)

    needle = opts.get("assert_diagnosis")
    if needle and not any(needle in d for d in report.get("diagnosis", [])):
        case["problems"].append("diagnosis does not mention %r" % needle)

    html_text = out_html.read_text(encoding="utf-8")
    for fragment in opts.get("assert_html", []):
        if fragment not in html_text:
            case["problems"].append("HTML is missing %r" % fragment)
    for fragment in opts.get("assert_html_absent", []):
        if fragment in html_text:
            case["problems"].append("HTML still contains %r" % fragment)

    pdf_path = Path(report["pdf"])
    flat = flat_text(pdf_path)
    for fragment, expected_count in opts.get("assert_pdf_text", []):
        actual = flat.count(fragment.replace(" ", ""))
        if actual != expected_count:
            case["problems"].append(
                "PDF contains %r %d time(s), expected %d" % (fragment, actual, expected_count)
            )
    bad_marks = []
    for marker in expected_marks:
        count = flat.count(marker)
        if count != 1:
            bad_marks.append("%s x%d" % (marker, count))
    stray = set(_MARK_RE.findall(flat)) - set(expected_marks)
    if stray:
        bad_marks.append("unexpected %s" % ", ".join(sorted(stray)[:5]))
    case["markers"] = {"expected": len(expected_marks), "problems": bad_marks}
    if bad_marks:
        case["problems"].append("markers: %s" % "; ".join(bad_marks[:10]))

    floor = opts.get("min_pages", min_pages)
    if report["pages"] < floor:
        case["problems"].append("expected at least %d pages, got %d" % (floor, report["pages"]))
    ceiling = opts.get("max_pages")
    if ceiling is not None and report["pages"] > ceiling:
        case["problems"].append("expected at most %d pages, got %d" % (ceiling, report["pages"]))

    if paper == "A4" or all_pages_png:
        case["png"] = export_pngs(pdf_path, stem, all_pages=all_pages_png)

    case["ok"] = not case["problems"]
    return case


def _load_verify():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "kimera_verify_tests", SKILL_ROOT / "scripts" / "verify.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unit_checks(cases) -> list:
    """Regressions that live inside verify.py and have no CLI surface.

    M-1: the footer check must fail when the left string is absent.
    M-2: the whitespace-free fallback of content-preserved must be per page, so
         that two words on either side of a page break cannot spell out a token
         that was never printed.
    """
    verify = _load_verify()
    results = []

    sample = next(
        (c for c in cases
         if c["fixture"] == "b-table-80-rows" and c["paper"] == "A4" and c.get("pdf")),
        None,
    )
    if sample is None:
        return [{"name": "setup", "ok": False, "details": "no sample PDF available"}]
    pdf = Path(sample["pdf"])

    # M-1 --------------------------------------------------------------------
    result = verify.verify_pdf(pdf, paper="A4", footer_left="STRINGA-CHE-NON-ESISTE", lang="it")
    footer = next(c for c in result["checks"] if c["name"] == "footer")
    results.append({
        "name": "M-1-footer-left",
        "ok": not footer["ok"],
        "details": "absent left footer string is rejected"
        if not footer["ok"] else "MISSED: %s" % footer["details"],
    })
    # ...and still passes with the real one.
    result = verify.verify_pdf(pdf, paper="A4", footer_left="Kimera Test Suite", lang="it")
    footer_ok = next(c for c in result["checks"] if c["name"] == "footer")
    results.append({
        "name": "M-1-no-false-pos",
        "ok": footer_ok["ok"],
        "details": "the real left footer string is accepted"
        if footer_ok["ok"] else "FALSE POSITIVE: %s" % footer_ok["details"],
    })

    # M-2 --------------------------------------------------------------------
    doc = fitz.open(pdf)
    words_p1 = re.findall(r"\w{4,}", doc[0].get_text())
    words_p2 = re.findall(r"\w{4,}", doc[1].get_text()) if doc.page_count > 1 else []
    doc.close()
    if words_p1 and words_p2:
        straddling = (words_p1[-1] + words_p2[0]).lower()
        result = verify.verify_pdf(
            pdf, paper="A4", footer_left="Kimera Test Suite", lang="it",
            expected_text=straddling,
        )
        content = next(c for c in result["checks"] if c["name"] == "content-preserved")
        results.append({
            "name": "M-2-flat-per-page",
            "ok": not content["ok"],
            "details": "a token straddling a page break is reported missing (%r)" % straddling[:32]
            if not content["ok"] else "MISSED: %s" % content["details"],
        })
    else:
        results.append({"name": "M-2-flat-per-page", "ok": False,
                        "details": "could not build a straddling token"})
    return results


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    keep = "--keep" in argv

    if RESULTS.exists() and not keep:
        shutil.rmtree(RESULTS)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)

    print("Kimera 2.0 test suite")
    print("  python  : %s" % PYTHON)
    print("  renderer: %s" % RENDER)
    print()

    cases = []
    started = time.perf_counter()

    for name, builder, min_pages, opts in FIXTURE_BUILDERS:
        before = _counter["n"]
        text = builder()
        markers = ["MRK-%04d" % i for i in range(before + 1, _counter["n"] + 1)]
        source = FIXTURES / ("%s.md" % name)
        source.write_text(text, encoding="utf-8")
        for paper in PAPERS:
            case_opts = dict(opts)
            if paper != "A4":
                # Page-count expectations are calibrated on A4 only.
                case_opts.pop("max_pages", None)
                case_opts.pop("min_pages", None)
            case = run_case(name, source, paper, markers, min_pages, opts=case_opts)
            cases.append(case)
            print("  [%s] %-18s %-7s %s pages, %.2fs%s"
                  % ("ok" if case["ok"] else "FAIL", name, paper,
                     case.get("pages", "?"), case["wall_s"],
                     "" if case["ok"] else "  <- " + case["problems"][0][:110]))

    if DEMO.is_file():
        case = run_case("demo-it", DEMO, "A4", [], 1, all_pages_png=True)
        cases.append(case)
        print("  [%s] %-18s %-7s %s pages, %.2fs%s"
              % ("ok" if case["ok"] else "FAIL", "demo-it", "A4",
                 case.get("pages", "?"), case["wall_s"],
                 "" if case["ok"] else "  <- " + case["problems"][0][:110]))
    else:
        print("  [--] demo-it            skipped (examples/demo-it.md not present)")

    units = unit_checks(cases)
    for unit in units:
        print("  [%s] unit %-14s %s"
              % ("ok" if unit["ok"] else "FAIL", unit["name"], unit["details"]))

    total_wall = time.perf_counter() - started
    passed = [c for c in cases if c["ok"]]
    failed = [c for c in cases if not c["ok"]]
    failed_units = [u for u in units if not u["ok"]]

    def avg(key):
        values = [c["timings_s"][key] for c in cases if "timings_s" in c and key in c["timings_s"]]
        return round(sum(values) / len(values), 3) if values else None

    skill_md = SKILL_ROOT / "SKILL.md"
    summary = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python": str(PYTHON),
        "python_version": sys.version.split()[0],
        "chromium": next((c.get("chromium") for c in cases if c.get("chromium")), None),
        "skill_md_bytes": skill_md.stat().st_size if skill_md.is_file() else None,
        "papers": list(PAPERS),
        "totals": {"runs": len(cases), "passed": len(passed), "failed": len(failed),
                   "unit_checks": len(units), "unit_failed": len(failed_units)},
        "unit_checks": units,
        "timings_s": {
            "render_avg": avg("render"),
            "pdf_avg": avg("pdf"),
            "verify_avg": avg("verify"),
            "cli_total_avg": avg("total"),
            "wall_avg": round(sum(c["wall_s"] for c in cases) / len(cases), 3) if cases else None,
            "wall_total": round(total_wall, 3),
        },
        "runs": cases,
    }
    out = RESULTS / "test-results.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("  runs      : %d  passed %d  failed %d  (+%d unit checks, %d failed)"
          % (len(cases), len(passed), len(failed), len(units), len(failed_units)))
    t = summary["timings_s"]
    print("  measured  : render avg %ss, pdf avg %ss, verify avg %ss, wall avg %ss, wall total %ss"
          % (t["render_avg"], t["pdf_avg"], t["verify_avg"], t["wall_avg"], t["wall_total"]))
    print("  SKILL.md  : %s bytes" % summary["skill_md_bytes"])
    print("  results   : %s" % out)
    print("  png       : %s" % PNG_DIR)
    if failed or failed_units:
        print()
        print("FAILURES:")
        for unit in failed_units:
            print("  unit %s: %s" % (unit["name"], unit["details"]))
        for case in failed:
            print("  %s / %s" % (case["fixture"], case["paper"]))
            for problem in case["problems"]:
                print("     - %s" % problem)
        return 1
    print()
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
