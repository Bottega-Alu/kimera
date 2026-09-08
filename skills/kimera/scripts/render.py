#!/usr/bin/env python3
"""Kimera 2.0 - render a Markdown source into a self-contained HTML document
and, with --verify, into a PDF that is checked against the real page geometry.

Pagination is delegated entirely to Chromium's print engine driven by CSS
@page (size, margins, footer margin boxes). This script never estimates page
heights and never positions a footer by hand.

Exit codes
    0  success (verified, or rendered without --verify)
    1  the PDF failed one or more verification checks
    2  internal error
    3  the Python runtime is missing (run scripts/setup.ps1)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

KIMERA_VERSION = "2.0.0"
SCRIPT_PATH = Path(__file__).resolve()
SCRIPTS_DIR = SCRIPT_PATH.parent
SKILL_ROOT = SCRIPTS_DIR.parent
ASSETS_DIR = SKILL_ROOT / "assets"

REQUIRED_MODULES = ("markdown", "pymdownx", "nh3", "playwright", "fitz")
MIN_CHROMIUM_MAJOR = 131

EXIT_OK = 0
EXIT_VERIFY_FAILED = 1
EXIT_INTERNAL = 2
EXIT_RUNTIME = 3


# --------------------------------------------------------------------------- #
# Runtime bootstrap - must run before markdown/nh3/playwright/fitz are imported
# --------------------------------------------------------------------------- #

def _emit_structured_error(payload: dict, code: int) -> None:
    sys.stderr.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    sys.stderr.flush()
    raise SystemExit(code)


def _setup_hint() -> str:
    return 'powershell -ExecutionPolicy Bypass -File "%s"' % (SCRIPTS_DIR / "setup.ps1")


def _modules_available() -> bool:
    from importlib.util import find_spec
    try:
        return all(find_spec(name) is not None for name in REQUIRED_MODULES)
    except (ImportError, ValueError):
        return False


def _missing_modules() -> list:
    from importlib.util import find_spec
    missing = []
    for name in REQUIRED_MODULES:
        try:
            if find_spec(name) is None:
                missing.append(name)
        except (ImportError, ValueError):
            missing.append(name)
    return missing


def _python_txt_path() -> "Path | None":
    marker = SKILL_ROOT / "python.txt"
    if not marker.is_file():
        return None
    try:
        raw = marker.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in raw.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return Path(line)
    return None


def _default_venv_python() -> "Path | None":
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "kimera" / "venv" / "Scripts" / "python.exe"
    if os.name == "nt":
        return None
    return Path.home() / ".local" / "share" / "kimera" / "venv" / "bin" / "python"


def _reexec(python_exe: Path, source: str) -> None:
    env = dict(os.environ)
    env["KIMERA_BOOTSTRAPPED"] = "1"
    try:
        completed = subprocess.run(
            [str(python_exe), str(SCRIPT_PATH), *sys.argv[1:]], env=env
        )
    except OSError as exc:
        _emit_structured_error(
            {
                "error": "runtime-missing",
                "reason": "interpreter-not-runnable",
                "interpreter": str(python_exe),
                "from": source,
                "detail": str(exc),
                "hint": _setup_hint(),
            },
            EXIT_RUNTIME,
        )
    raise SystemExit(completed.returncode)


def _bootstrap() -> None:
    """Find an interpreter that can actually run Kimera, and hand over to it."""
    if _modules_available():
        return

    tried = []

    if os.environ.get("KIMERA_BOOTSTRAPPED") == "1":
        _emit_structured_error(
            {
                "error": "runtime-missing",
                "reason": "dependencies-missing-after-bootstrap",
                "interpreter": sys.executable,
                "missing": _missing_modules(),
                "hint": _setup_hint(),
            },
            EXIT_RUNTIME,
        )

    override = (os.environ.get("KIMERA_PYTHON") or "").strip().strip('"')
    if override:
        candidate = Path(override)
        tried.append({"source": "KIMERA_PYTHON", "path": str(candidate)})
        if not candidate.is_file():
            # An explicit override that does not resolve is a hard error: falling
            # back silently would hide a broken configuration.
            _emit_structured_error(
                {
                    "error": "runtime-missing",
                    "reason": "kimera-python-not-found",
                    "message": "KIMERA_PYTHON points to a path that does not exist.",
                    "tried": tried,
                    "hint": _setup_hint(),
                },
                EXIT_RUNTIME,
            )
        _reexec(candidate, "KIMERA_PYTHON")

    for source, candidate in (
        ("python.txt", _python_txt_path()),
        ("LOCALAPPDATA venv", _default_venv_python()),
    ):
        if candidate is None:
            continue
        tried.append({"source": source, "path": str(candidate)})
        if candidate.is_file():
            _reexec(candidate, source)

    _emit_structured_error(
        {
            "error": "runtime-missing",
            "reason": "no-usable-interpreter",
            "message": "Kimera needs markdown, nh3, playwright and pymupdf.",
            "missing": _missing_modules(),
            "current_interpreter": sys.executable,
            "tried": tried,
            "hint": _setup_hint(),
        },
        EXIT_RUNTIME,
    )


_bootstrap()

# --------------------------------------------------------------------------- #

import argparse            # noqa: E402
import html as html_lib    # noqa: E402
import importlib.util      # noqa: E402
import re                  # noqa: E402
import string              # noqa: E402
import tempfile            # noqa: E402
import time                # noqa: E402

import markdown            # noqa: E402
import nh3                 # noqa: E402


def _load_verify_module():
    spec = importlib.util.spec_from_file_location(
        "kimera_verify", SCRIPTS_DIR / "verify.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

PAPERS = {
    # key: (display name, CSS size keyword, width mm, height mm)
    "a4": ("A4", "A4", 210.0, 297.0),
    "letter": ("Letter", "letter", 215.9, 279.4),
    "legal": ("Legal", "legal", 215.9, 355.6),
}

MARGINS_MM = {"top": 16.0, "right": 18.0, "bottom": 22.0, "left": 18.0}
FOOTER_PAD_TOP_MM = 5.0

FOOTER_FONT_STACK = (
    '"Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, '
    '"Helvetica Neue", Arial, sans-serif'
)

STRINGS = {
    "it": {
        "page_prefix": "Pagina ",
        "page_infix": " di ",
        "project": "Progetto",
        "author": "Autore",
        "date": "Data",
        "print_hint": (
            "Anteprima a schermo, scorrimento continuo. Per stampare: Chromium aggiornato, "
            "carta {paper}, scala 100%, margini predefiniti del CSS, intestazioni e "
            "piè di pagina del browser disattivati."
        ),
        "not_verified": "NON VERIFICATO",
    },
    "en": {
        "page_prefix": "Page ",
        "page_infix": " of ",
        "project": "Project",
        "author": "Author",
        "date": "Date",
        "print_hint": (
            "On-screen preview, continuous scroll. To print: up-to-date Chromium, "
            "{paper} paper, 100% scale, default CSS margins, browser headers and "
            "footers turned off."
        ),
        "not_verified": "NOT VERIFIED",
    },
}

MD_EXTENSIONS = [
    "meta",
    "tables",
    "fenced_code",
    "sane_lists",
    "admonition",
    "footnotes",
    "def_list",
    "abbr",
    "pymdownx.tilde",
]

# subscript off: `~x~` stays literal text, only `~~x~~` becomes <del>.
MD_EXTENSION_CONFIGS = {"pymdownx.tilde": {"subscript": False, "smart_delete": True}}

ALLOWED_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td",
    "pre", "code", "blockquote",
    "strong", "b", "em", "i", "a", "hr", "br",
    "del", "s", "sup", "sub",
    "dl", "dt", "dd",
    "div", "span", "abbr",
}

ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "id", "class"},
    "abbr": {"title"},
    "div": {"class"},
    "span": {"class"},
    "p": {"class"},
    "li": {"id"},
    "ol": {"start"},
    "sup": {"id"},
    "th": {"style"},
    "td": {"style"},
}

# Only these class names survive; every other class value is dropped. Note that
# raw HTML in the source CAN still carry one of these (a hand-written
# `<div class="admonition danger">` renders as a callout, a
# `<p class="page-break">` forces a page break). That is cosmetic, not a
# security hole: no script, style, event handler or positioning survives.
ALLOWED_CLASSES = {
    "admonition", "admonition-title",
    "footnote", "footnote-ref", "footnote-backref",
    "page-break",
    "note", "info", "tip", "success", "warning", "danger", "error",
}

_STYLE_RE = re.compile(r"text-align:\s*(?:left|center|right)\s*;?", re.IGNORECASE)
_ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9_:.\-]*")
_TAG_NAME_RE = re.compile(r"<\s*([a-zA-Z][a-zA-Z0-9]*)")
_IMG_ALT_RE = re.compile(r"<img\b[^>]*?\balt=\"([^\"]*)\"", re.IGNORECASE)
# Tags whose text content is discarded as well as the tag itself.
CONTENT_DISCARDING_TAGS = {"script", "style"}

PAGEBREAK_TOKEN = "KIMERA_PAGEBREAK_MARK"
_PAGEBREAK_LINE = re.compile(r"^(?:\\pagebreak|\\newpage)[ \t]*$")
_FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")

_TAG_RE = re.compile(r"<[^>]+>")
_H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)


class KimeraError(Exception):
    def __init__(self, code, message, **extra):
        super().__init__(message)
        self.code = code
        self.message = message
        self.extra = extra

    def payload(self):
        data = {"error": self.code, "message": self.message}
        data.update(self.extra)
        return data


# --------------------------------------------------------------------------- #
# Markdown -> sanitized HTML
# --------------------------------------------------------------------------- #

def protect_pagebreaks(source: str) -> str:
    """Normalise ``\\pagebreak`` / ``\\newpage`` directives, outside code fences.

    Every directive becomes a token standing alone in its own paragraph, with a
    blank line on each side, so the Markdown parser can never glue it to the
    text around it (inside a list item, at the end of a paragraph). Runs of
    consecutive directives - with or without blank lines between them - collapse
    into a single break, because two breaks in a row can only produce a blank
    page.
    """
    sentinel = "\x00KIMERA-PB\x00"
    lines = []
    fence_char = None
    fence_len = 0
    for line in source.split("\n"):
        fence = _FENCE.match(line)
        if fence:
            marker = fence.group(1)
            if fence_char is None:
                fence_char, fence_len = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len:
                fence_char, fence_len = None, 0
            lines.append(line)
            continue
        if fence_char is None and _PAGEBREAK_LINE.match(line):
            lines.append(sentinel)
            continue
        lines.append(line)

    out = []
    index = 0
    total = len(lines)
    while index < total:
        if lines[index] != sentinel:
            out.append(lines[index])
            index += 1
            continue
        while index < total and (lines[index] == sentinel or not lines[index].strip()):
            index += 1
        while out and not out[-1].strip():
            out.pop()
        out.extend(["", PAGEBREAK_TOKEN, ""])
    return "\n".join(out)


def _attribute_filter(tag: str, attribute: str, value: str):
    if attribute == "class":
        kept = [c for c in value.split() if c in ALLOWED_CLASSES]
        return " ".join(kept) if kept else None
    if attribute == "style":
        return value if _STYLE_RE.fullmatch(value.strip()) else None
    if attribute == "id":
        return value if _ID_RE.fullmatch(value) else None
    if attribute == "start":
        return value if value.isdigit() else None
    return value


def sanitize(raw_html: str) -> str:
    return nh3.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes={k: set(v) for k, v in ALLOWED_ATTRIBUTES.items()},
        attribute_filter=_attribute_filter,
        url_schemes={"http", "https", "mailto"},
        link_rel=None,
        strip_comments=True,
    )


def inspect_source_support(raw_html: str, clean_html: str) -> dict:
    """Compare the parser output with the sanitised output, before rendering.

    This is the only place that can tell the difference between "the PDF matches
    the HTML" and "the HTML matches what the author wrote". ``content-preserved``
    checks the former; this checks the latter.
    """
    before = {m.group(1).lower() for m in _TAG_NAME_RE.finditer(raw_html)}
    after = {m.group(1).lower() for m in _TAG_NAME_RE.finditer(clean_html)}
    dropped = sorted(tag for tag in before - after if tag not in ALLOWED_TAGS)
    # Only an `img` carrying an `alt` attribute counts as a lost figure: that is
    # what `![alt](src)` compiles to. A bare `<img src=x onerror=...>` smuggled in
    # as raw HTML is an attack payload, not content, and is merely reported as a
    # dropped tag.
    images = [alt.strip() for alt in _IMG_ALT_RE.findall(raw_html)]
    return {
        "images": images,
        "dropped_tags": dropped,
        "content_discarded_tags": sorted(t for t in dropped if t in CONTENT_DISCARDING_TAGS),
        "pagebreak_token_leaked": False,
    }


def markdown_to_html(source: str):
    """Return (sanitized body html, front-matter dict, source-support report)."""
    md = markdown.Markdown(
        extensions=MD_EXTENSIONS,
        extension_configs=MD_EXTENSION_CONFIGS,
        output_format="html",
    )
    raw = md.convert(protect_pagebreaks(source))
    meta = {}
    for key, values in getattr(md, "Meta", {}).items():
        if values:
            meta[key.strip().lower()] = " ".join(v.strip() for v in values).strip()
    body = sanitize(raw)
    support = inspect_source_support(raw, body)

    body = re.sub(
        r"<p>\s*(?:%s\s*)+</p>" % PAGEBREAK_TOKEN,
        '<div class="page-break"></div>',
        body,
    )
    # Belt and braces: the token must never reach the page, whatever block the
    # parser decided to wrap it in.
    if PAGEBREAK_TOKEN in body:
        support["pagebreak_token_leaked"] = True
        body = re.sub(r"\s*%s\s*" % PAGEBREAK_TOKEN, " ", body)
    # A break before any content only yields a header-only page; a break after
    # all content only yields a blank one.
    body = re.sub(r'\A(?:\s*<div class="page-break"></div>)+', "", body)
    body = re.sub(r'(?:\s*<div class="page-break"></div>)+\s*\Z', "", body)
    return body.strip(), meta, support


def html_to_text(fragment: str) -> str:
    return html_lib.unescape(_TAG_RE.sub(" ", fragment))


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def extract_and_maybe_drop_h1(body: str, explicit_title: "str | None"):
    """Return (body, h1_text). The first H1 is dropped when it duplicates the title."""
    match = _H1_RE.search(body)
    if not match:
        return body, None
    h1_text = re.sub(r"\s+", " ", html_to_text(match.group(1))).strip()
    if explicit_title is None or normalize_title(explicit_title) == normalize_title(h1_text):
        body = body[: match.start()] + body[match.end():]
        return body.strip(), h1_text
    return body, h1_text


# --------------------------------------------------------------------------- #
# CSS / template assembly
# --------------------------------------------------------------------------- #

def css_string_literal(value: str) -> str:
    """Escape a value for use inside a CSS double-quoted string.

    Leading and trailing spaces are meaningful here (the page counter is built
    from "Pagina " + counter(page) + " di " + counter(pages)), so they are kept.
    """
    cleaned = re.sub(r"[\r\n\t]+", " ", value or "")
    cleaned = "".join(ch for ch in cleaned if ch >= " ")
    cleaned = cleaned.replace("\\", "\\\\").replace('"', '\\"')
    return re.sub(r" {2,}", " ", cleaned)


def build_page_css(paper_key: str, footer_left: str, lang: str) -> str:
    _, css_size, _, _ = PAPERS[paper_key]
    strings = STRINGS[lang]
    m = MARGINS_MM
    boxes = []
    if footer_left:
        boxes.append(
            "  @bottom-left {\n"
            '    content: "%s";\n'
            "    font-family: %s;\n"
            "    font-size: 8pt;\n"
            "    color: #546e7a;\n"
            "    vertical-align: top;\n"
            "    padding-top: %gmm;\n"
            "    white-space: nowrap;\n"
            "    overflow: hidden;\n"
            "    text-overflow: ellipsis;\n"
            "  }" % (css_string_literal(footer_left), FOOTER_FONT_STACK, FOOTER_PAD_TOP_MM)
        )
    boxes.append(
        "  @bottom-right {\n"
        '    content: "%s" counter(page) "%s" counter(pages);\n'
        "    font-family: %s;\n"
        "    font-size: 8pt;\n"
        "    color: #546e7a;\n"
        "    vertical-align: top;\n"
        "    padding-top: %gmm;\n"
        "    white-space: nowrap;\n"
        "  }"
        % (
            css_string_literal(strings["page_prefix"]),
            css_string_literal(strings["page_infix"]),
            FOOTER_FONT_STACK,
            FOOTER_PAD_TOP_MM,
        )
    )
    return (
        "@page {\n"
        "  size: %s;\n"
        "  margin: %gmm %gmm %gmm %gmm;\n"
        "%s\n"
        "}\n" % (css_size, m["top"], m["right"], m["bottom"], m["left"], "\n".join(boxes))
    )


def esc(value: str) -> str:
    return html_lib.escape(value or "", quote=True)


def build_document(body: str, ctx: dict) -> str:
    template = string.Template((ASSETS_DIR / "template.html").read_text(encoding="utf-8"))
    css = build_page_css(ctx["paper_key"], ctx["footer_left"], ctx["lang"]) + "\n"
    css += (ASSETS_DIR / "kimera.css").read_text(encoding="utf-8")

    label_block = (
        '<div class="doc-label">%s</div>\n' % esc(ctx["label"]) if ctx["label"] else ""
    )
    title_block = '<h1 class="doc-title">%s</h1>\n' % esc(ctx["title"])
    subtitle_block = (
        '<p class="doc-subtitle">%s</p>\n' % esc(ctx["subtitle"]) if ctx["subtitle"] else ""
    )

    strings = STRINGS[ctx["lang"]]
    pairs = []
    for key in ("project", "author", "date"):
        if ctx.get(key):
            pairs.append("<dt>%s</dt><dd>%s</dd>" % (esc(strings[key]), esc(ctx[key])))
    meta_block = '<dl class="doc-meta">%s</dl>\n' % "".join(pairs) if pairs else ""

    end_block = (
        '<footer class="doc-end">%s</footer>\n' % esc(ctx["confidential"])
        if ctx["confidential"]
        else ""
    )

    print_hint = strings["print_hint"].format(paper=PAPERS[ctx["paper_key"]][0])

    document = template.safe_substitute(
        lang=esc(ctx["lang"]),
        title=esc(ctx["title"]),
        css=css,
        label_block=label_block,
        title_block=title_block,
        subtitle_block=subtitle_block,
        meta_block=meta_block,
        body=body,
        end_block=end_block,
        print_hint=esc(print_hint),
    )
    expected_text = " ".join(
        html_to_text(part)
        for part in (label_block, title_block, subtitle_block, meta_block, body, end_block)
    )
    return document, expected_text


def build_support_check(support: dict) -> dict:
    """Turn the source-support inventory into a check entry.

    Images are a hard failure: they vanish from the output entirely and no
    downstream check can see the loss. Tags stripped by the sanitiser only
    produce a warning, because their text survives.
    """
    problems = []
    ok = True
    level = "ok"
    if support["images"]:
        ok = False
        level = "error"
        shown = ", ".join(alt for alt in support["images"][:5] if alt) or "(no alt text)"
        problems.append(
            "%d image(s) in the source, not supported: %s" % (len(support["images"]), shown)
        )
    if support["dropped_tags"]:
        if ok:
            level = "warn"
        detail = "tag(s) removed by the sanitiser, their text kept: %s" % ", ".join(
            support["dropped_tags"]
        )
        if support["content_discarded_tags"]:
            detail += " (content discarded too: %s)" % ", ".join(
                support["content_discarded_tags"]
            )
        problems.append(detail)
    if support["pagebreak_token_leaked"]:
        if ok:
            level = "warn"
        problems.append("a page-break directive could not be converted and was removed")
    return {
        "name": "source-support",
        "ok": ok,
        "level": level,
        "details": "; ".join(problems) if problems else "no unsupported construct in the source",
    }


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #

def html_to_pdf(html_path: Path, pdf_path: Path) -> str:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            version = browser.version
            try:
                major = int(version.split(".")[0])
            except (ValueError, IndexError):
                major = 0
            if major < MIN_CHROMIUM_MAJOR:
                browser.close()
                raise KimeraError(
                    "chromium-too-old",
                    "Chromium %s is older than the required %d."
                    % (version, MIN_CHROMIUM_MAJOR),
                    chromium=version,
                    required=MIN_CHROMIUM_MAJOR,
                    hint=_setup_hint(),
                )
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri(), wait_until="load")
            page.emulate_media(media="print")
            page.pdf(
                path=str(pdf_path),
                prefer_css_page_size=True,
                print_background=True,
                display_header_footer=False,
            )
            browser.close()
            return version
    except PlaywrightError as exc:
        raise KimeraError(
            "browser-failed",
            "Chromium could not render the document: %s" % exc,
            hint=_setup_hint(),
        ) from exc


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="render.py",
        description="Kimera 2.0 - Markdown to print-ready HTML and verified PDF.",
    )
    p.add_argument("source", help="Markdown source file (UTF-8).")
    p.add_argument("--out", help="HTML output path (default: SOURCE with .md.html).")
    p.add_argument("--title")
    p.add_argument("--subtitle")
    p.add_argument("--project")
    p.add_argument("--author")
    p.add_argument("--date")
    p.add_argument("--label", help="Small uppercase kicker above the title.")
    p.add_argument("--lang", choices=sorted(STRINGS), help="Document language (default: it).")
    p.add_argument("--paper", help="A4 | Letter | Legal (default: A4).")
    p.add_argument("--confidential", help="Confidentiality line printed at the end.")
    p.add_argument("--verify", action="store_true", help="Produce the PDF and check it.")
    p.add_argument("--pdf", help="PDF output path (implies the default location otherwise).")
    p.add_argument("--no-pdf", action="store_true", help="Verify in a temp file, keep no PDF.")
    p.add_argument("--report", help="Write the JSON report to this path.")
    p.add_argument("--json", action="store_true", help="Print the JSON report instead of the summary.")
    return p


def resolve_paper(value: "str | None") -> str:
    if not value:
        return "a4"
    key = value.strip().lower().replace(" ", "").replace("-", "")
    key = {"us_letter": "letter", "usletter": "letter", "uslegal": "legal"}.get(key, key)
    if key not in PAPERS:
        raise KimeraError(
            "bad-paper",
            "Unknown paper %r; use A4, Letter or Legal." % value,
            allowed=sorted(PAPERS),
        )
    return key


def default_html_path(source: Path) -> Path:
    if source.name.lower().endswith(".md"):
        return source.with_name(source.name + ".html")
    return source.with_name(source.stem + ".md.html")


def default_pdf_path(html_path: Path) -> Path:
    name = html_path.name
    if name.lower().endswith(".md.html"):
        name = name[: -len(".md.html")]
    else:
        name = html_path.stem
    return html_path.with_name(name + ".pdf")


def pick(*values):
    for value in values:
        if value:
            return value.strip()
    return ""


def format_summary(report: dict) -> str:
    lines = []
    lines.append("Kimera 2.0 - %s" % report["title"])
    lines.append("  source    : %s" % report["source"])
    lines.append("  html      : %s" % report["html"])
    if report.get("pdf"):
        lines.append("  pdf       : %s" % report["pdf"])
    lines.append(
        "  paper     : %s (%.1f x %.1f mm), lang %s"
        % (report["paper"], report["paper_mm"][0], report["paper_mm"][1], report["lang"])
    )
    if report.get("pages"):
        lines.append("  pages     : %d" % report["pages"])
    if report.get("chromium"):
        lines.append("  chromium  : %s" % report["chromium"])
    timings = report.get("timings_s", {})
    lines.append(
        "  timings   : render %.2fs"
        % timings.get("render", 0.0)
        + (", pdf %.2fs" % timings["pdf"] if "pdf" in timings else "")
        + (", verify %.2fs" % timings["verify"] if "verify" in timings else "")
        + (", total %.2fs" % timings.get("total", 0.0))
    )
    lines.append("  status    : %s" % report["status"])
    for check in report.get("checks", []):
        mark = "ok" if check["ok"] else "FAIL"
        if check["ok"] and check.get("level") == "warn":
            mark = "warn"
        lines.append("     [%s] %-18s %s" % (mark, check["name"], check["details"]))
    if report.get("diagnosis"):
        lines.append("  diagnosis :")
        for item in report["diagnosis"]:
            lines.append("     - %s" % item)
    if not report["verified"] and report["status"].endswith("VERIFIED") and not report.get("checks"):
        lines.append("  note      : rendered without --verify; the PDF was not produced or checked.")
    return "\n".join(lines)


def run(argv) -> int:
    started = time.perf_counter()
    args = build_parser().parse_args(argv)

    source = Path(args.source).expanduser()
    if not source.is_file():
        raise KimeraError("source-not-found", "No such Markdown file: %s" % source)
    try:
        text = source.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise KimeraError(
            "source-not-utf8",
            "The source is not valid UTF-8 (byte %d: %s)." % (exc.start, exc.reason),
            source=str(source),
            hint="save the source as UTF-8 / salva il sorgente in UTF-8",
        ) from exc

    t0 = time.perf_counter()
    body, meta, support = markdown_to_html(text)

    lang = pick(args.lang, meta.get("lang")).lower() or "it"
    if lang not in STRINGS:
        lang = "it"
    paper_key = resolve_paper(pick(args.paper, meta.get("paper")))

    explicit_title = pick(args.title, meta.get("title")) or None
    body, h1_text = extract_and_maybe_drop_h1(body, explicit_title)
    title = explicit_title or h1_text or source.stem

    ctx = {
        "title": title,
        "subtitle": pick(args.subtitle, meta.get("subtitle")),
        "project": pick(args.project, meta.get("project")),
        "author": pick(args.author, meta.get("author")),
        "date": pick(args.date, meta.get("date")),
        "label": pick(args.label, meta.get("label")),
        "confidential": pick(args.confidential, meta.get("confidential")),
        "lang": lang,
        "paper_key": paper_key,
    }
    ctx["footer_left"] = ctx["project"] or title

    document, expected_text = build_document(body, ctx)

    html_path = Path(args.out).expanduser() if args.out else default_html_path(source)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(document, encoding="utf-8")
    render_s = time.perf_counter() - t0

    paper_name, _, width_mm, height_mm = PAPERS[paper_key]
    report = {
        "tool": "kimera",
        "version": KIMERA_VERSION,
        "source": str(source.resolve()),
        "html": str(html_path.resolve()),
        "pdf": None,
        "title": title,
        "paper": paper_name,
        "paper_mm": [width_mm, height_mm],
        "margins_mm": dict(MARGINS_MM),
        "lang": lang,
        "verified": False,
        "status": STRINGS[lang]["not_verified"] if lang != "it" else "NON VERIFICATO",
        "python": sys.executable,
        "timings_s": {"render": round(render_s, 3)},
        "checks": [],
        "diagnosis": [],
    }
    # The machine-readable status stays English on purpose.
    report["status"] = "NOT VERIFIED"

    if args.verify:
        if args.no_pdf:
            tmp = Path(tempfile.mkdtemp(prefix="kimera-")) / (html_path.stem + ".pdf")
            pdf_path, keep = tmp, False
        else:
            pdf_path = Path(args.pdf).expanduser() if args.pdf else default_pdf_path(html_path)
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            keep = True

        t1 = time.perf_counter()
        chromium = html_to_pdf(html_path, pdf_path)
        report["timings_s"]["pdf"] = round(time.perf_counter() - t1, 3)
        report["chromium"] = chromium

        verify = _load_verify_module()
        t2 = time.perf_counter()
        result = verify.verify_pdf(
            pdf_path,
            paper=paper_name,
            width_mm=width_mm,
            height_mm=height_mm,
            margins_mm=MARGINS_MM,
            footer_left=ctx["footer_left"],
            lang=lang,
            expected_text=expected_text,
            html_text=document,
            chromium_version=chromium,
            footer_gap_mm=3.0,
        )
        report["timings_s"]["verify"] = round(time.perf_counter() - t2, 3)

        # source-support is a render-time check (it needs the pre-sanitisation
        # HTML) but it only surfaces with --verify, next to content-preserved.
        support_check = build_support_check(support)
        checks = list(result["checks"])
        position = next(
            (i for i, c in enumerate(checks) if c["name"] == "content-preserved"), len(checks) - 1
        )
        checks.insert(position + 1, support_check)
        diagnosis = list(result["diagnosis"])
        if support["images"]:
            diagnosis.append(verify.DIAGNOSIS[lang]["unsupported-image"])

        report["checks"] = checks
        report["diagnosis"] = diagnosis
        report["source_support"] = support
        report["pages"] = result["pages"]
        report["verified"] = result["ok"] and support_check["ok"]
        report["status"] = "VERIFIED" if report["verified"] else "FAILED"
        report["pdf"] = str(pdf_path.resolve()) if keep else None
        if not keep:
            try:
                pdf_path.unlink()
                pdf_path.parent.rmdir()
            except OSError:
                pass

    report["timings_s"]["total"] = round(time.perf_counter() - started, 3)

    if args.report:
        report_path = Path(args.report).expanduser()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_summary(report))

    if args.verify and not report["verified"]:
        return EXIT_VERIFY_FAILED
    return EXIT_OK


def main() -> int:
    try:
        return run(sys.argv[1:])
    except KimeraError as exc:
        sys.stderr.write(json.dumps(exc.payload(), ensure_ascii=False, indent=2) + "\n")
        return EXIT_RUNTIME if exc.code in {"chromium-too-old", "browser-failed"} else EXIT_INTERNAL
    except KeyboardInterrupt:
        return EXIT_INTERNAL
    except Exception as exc:  # noqa: BLE001 - the CLI must always answer in JSON
        sys.stderr.write(
            json.dumps(
                {"error": "internal-error", "type": type(exc).__name__, "message": str(exc)},
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
