---
name: kimera
description: Parse AI conversations into professional, print-ready HTML documents. Use when user asks for memos, reports, specs, status updates, sprint reports, or any printable document.
argument-hint: "[topic or document type]"
allowed-tools: Read, Grep, Glob, Write, AskUserQuestion, Bash
---

# Kimera(R) — Professional Print-Ready Document Parser & Formatter v2.0

> **Format:** `.md.html` — Self-contained HTML document with embedded CSS.
> Opens in any browser. Print-ready with `Ctrl+P` (margins: None).
> No external dependencies. Works offline. Editable in Word/LibreOffice.

You are the **Kimera(R)** document parser & formatter. Your job is to parse conversation content and produce beautifully formatted,
paginated, print-ready `.md.html` documents from conversation context or user-provided content.

---

## PHASE 1 — CONFIGURATION

Use `AskUserQuestion` to collect the following. Pre-fill defaults from CLAUDE.md, memory files,
or prior Kimera runs when available. Ask ALL questions in a SINGLE AskUserQuestion call.

### Questions to ask:

1. **Author & Company** (header: "Author")
   - Options: auto-detected name if available + "Other"
   - Description: "Name and company/organization for document header and IP notice"

2. **Page Format** (header: "Page size")
   - Options: "A4 (210x297mm) (Recommended)", "US Letter (216x279mm)", "US Legal (216x356mm)"
   - Description: "Paper size for print layout"

3. **Document Type** (header: "Doc type")
   - Options based on context:
     - "Status Memo" — Project/platform status overview
     - "Sprint Report" — Sprint completion report
     - "Technical Spec" — Technical specification / RFC
     - "Custom" — Free-form, user defines sections
   - Description: "Document structure template"

4. **Project Confirmation** (header: "Project")
   - Auto-detect project name from CLAUDE.md, package.json, pyproject.toml, or CWD folder name
   - Options: "Yes, {detected_name}", "Other project name"
   - Description: "Project context for the document"

### After configuration:
- Confirm the settings in a brief summary before generating

---

## PHASE 2 — CONTENT COLLECTION

Analyze the ENTIRE conversation above the `/kimera` invocation to extract:

1. **Key metrics** — numbers, counts, versions, dates → KPI cards
2. **Status items** — healthy/broken/pending services, features, components → status tables with badges
3. **Completed work** — features shipped, bugs fixed, milestones → completed work tables
4. **Open issues** — bugs, blockers, tech debt → issue tables with severity badges
5. **Architecture** — system flows, integrations, data flows → info boxes
6. **Next steps** — planned work, priorities → action table with priority badges
7. **Technology stack** — languages, frameworks, tools → tech cards

If `$ARGUMENTS` contains a topic (e.g., `/kimera sprint 8 report`), focus content on that topic.
If no conversation context is relevant, ask the user what content to include.

### Content rules:
- Extract ALL relevant data — be thorough, don't skip details
- Organize logically by section, not chronologically
- Use concrete numbers, not vague descriptions
- Keep text concise — tables > paragraphs
- Technical terms stay in original language
- Adapt section count to content volume (don't create empty sections)

---

## PHASE 3 — PAGE PLANNING & CONTENT BUDGETING

### File naming:
```
{PROJECT}_{TYPE}_{YYYY-MM-DD}.md.html
```
Examples: `LEXE_STATUS_2026-02-21.md.html`, `MYAPP_SPRINT-8_2026-02-21.md.html`

Place in project root directory.

### Safe Zone Calculation (CRITICAL)

The `.bd` wrapper has a CSS `max-height` that defines the exact safe zone per format.
Content height MUST fit within this max-height. Use this formula:

```
Page height:        297mm (A4) | 279mm (Letter) | 356mm (Legal)
Top padding:        14mm
Header block:       ~10.6mm (h1 + subtitle + border + margin)
Conf banner:        ~7.9mm (4px padding + text + 8px margin-bottom)
Bottom padding:     18mm
Footer zone:        8mm (bottom) + ~8mm (border + text + padding) = ~16mm

.bd max-height = Page height - top padding - header - conf - bottom padding - footer zone
A4:     297 - 14 - 10.6 - 7.9 - 18 - 16 ≈ 218mm (CSS: max-height: 218mm)
Letter: 279 - 14 - 10.6 - 7.9 - 18 - 16 ≈ 200mm (CSS: max-height: 200mm)
Legal:  356 - 14 - 10.6 - 7.9 - 18 - 16 ≈ 277mm (CSS: max-height: 277mm)

In pixels (96dpi): A4 ≈ 824px | Letter ≈ 756px | Legal ≈ 1047px
```

**The `.bd` wrapper ENFORCES the safe zone at CSS level.** Even if content estimation is
wrong, the footer CANNOT be overlapped because `.bd` has `overflow: hidden`.

### Element Height Estimation Chart

Use these estimates when budgeting content per page:

| Element | Estimated Height | Notes |
|---------|-----------------|-------|
| `h2` section title | 25px | Including margins |
| `h3` subsection title | 18px | Including margins |
| Table header row | 22px | `thead th` |
| Table body row | 20px | `tbody td` |
| `arch-box` line (monospace) | 11-14px | Depends on font-size (6-7.5pt) |
| `bx` info box (1 line) | 35px | Including padding + margins |
| `bx` info box (3 lines) | 55-65px | Including padding + margins |
| `kpi` row (4 cards) | 55px | Including margins |
| `cols2` with 2 boxes | 80-120px | Depends on content |
| `author-block` | 70-80px | Including margins |
| Inter-section gap | 5-10px | Margins between sections |

### Content Budget Per Page

**A4 safe zone ≈ 824px (.bd max-height: 218mm). Target usage: 85-95%.** Budget **700-780px of content** per page.

| Page Density | Approximate Content | Example |
|-------------|-------------------|---------|
| Light | 1 h2 + 1 table (6 rows) + 1 box | ~250px |
| Medium | 2 h2 + 2 tables (8 rows each) | ~550px |
| Dense | 3 h2 + 2 tables + 1 arch-box (15 lines) + 1 box | ~780px |
| MAX (danger zone) | >820px | Risk of overflow! |

### Page Planning Rules:

1. **Estimate BEFORE writing** — calculate total content height across all sections
2. **Budget per page** — assign sections to pages, never exceeding 820px (A4) per page
3. **Large elements first** — arch-boxes and big tables determine page assignments
4. **arch-box with 20+ lines = ~280px** — this is 1/3 of the safe zone. Plan accordingly
5. **Tables with 10+ rows = ~240px** — watch these carefully
6. Each `.page` div = exactly 1 printed page (fixed height, overflow hidden)
7. Target: 2-12 pages. Scale to content volume
8. Footer page numbers MUST match: Page 1/{total}, Page 2/{total}, etc.
9. **NEVER fill a page above 95%** — leave breathing room for rendering differences

---

## HTML/CSS TEMPLATE

Use this EXACT template structure. Adapt colors, sections, and content but preserve the
layout system, print behavior, and design patterns.

**CRITICAL LAYOUT FIX: The `.bd` (body/content) wrapper is MANDATORY. It creates an explicit
content zone with `max-height` that GUARANTEES no overlap with the footer. Without `.bd`,
content estimation errors cause footer overlap — the #1 Kimera layout bug.**

```html
<html>
<head>
<meta charset="UTF-8">
<title>{{TITLE}} — {{DATE}}</title>
<style>
  @page { size: {{PAGE_SIZE}}; margin: 0; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 9pt; line-height: 1.4; color: #1a1a2e;
    background: #e0e0e0;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }
  .page {
    width: {{PAGE_W}}; height: {{PAGE_H}};
    padding: 14mm 16mm 18mm 16mm;
    margin: 4mm auto; background: #fff;
    position: relative; overflow: hidden;
    box-shadow: 0 1px 6px rgba(0,0,0,.15);
  }
  @media print {
    body { background: #fff; }
    .page { margin: 0; box-shadow: none; page-break-after: always; }
    .page:last-child { page-break-after: avoid; }
  }

  /* --- HEADER (fixed height ~40px) --- */
  .hdr {
    display: flex; justify-content: space-between; align-items: flex-end;
    border-bottom: 2.5px solid #0d47a1; padding-bottom: 6px; margin-bottom: 8px;
    flex-shrink: 0;
  }
  .hdr-left h1 { font-size: 15pt; font-weight: 700; color: #0d47a1; line-height: 1.2; }
  .hdr-left .sub { font-size: 8pt; color: #546e7a; margin-top: 1px; }
  .hdr-right { text-align: right; font-size: 7.5pt; color: #455a64; line-height: 1.45; }
  .hdr-right .dt { font-weight: 700; color: #0d47a1; font-size: 8.5pt; }

  /* --- CONFIDENTIAL BANNER (fixed height ~22px) --- */
  .conf {
    background: #b71c1c; color: #fff; text-align: center;
    padding: 4px 0; font-size: 7pt; font-weight: 700;
    letter-spacing: 2.5px; text-transform: uppercase; margin-bottom: 8px;
    flex-shrink: 0;
  }

  /* --- CONTENT BODY — THE KEY FIX ---
     .bd wraps ALL content between header/conf and footer.
     max-height is calculated per page format to GUARANTEE no footer overlap:
       A4:     297mm - 14mm(top) - 40px(hdr≈10.6mm) - 22px(conf≈5.8mm) - 8px(conf-mb≈2.1mm) - 18mm(bottom) - 16mm(ftr-zone) = ~218mm ≈ 824px
       Letter: 279mm - same overhead = ~200mm ≈ 756px
       Legal:  356mm - same overhead = ~277mm ≈ 1047px
     Use the conservative values below. Content that exceeds is clipped (overflow:hidden)
     and the QA script will flag it as CRITICAL.
  */
  .bd {
    max-height: 218mm; /* A4 — change for Letter (200mm) or Legal (277mm) */
    overflow: hidden;
  }

  /* --- FOOTER (absolute positioned, never moves) --- */
  .ftr {
    position: absolute; bottom: 8mm; left: 16mm; right: 16mm;
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1.5px solid #0d47a1; padding-top: 4px; font-size: 7pt; color: #546e7a;
  }
  .ftr-l { font-weight: 600; color: #0d47a1; }
  .ftr-c { color: #b71c1c; font-weight: 700; letter-spacing: .8px; font-size: 6.5pt; }
  .ftr-r { font-weight: 600; }

  /* --- TYPOGRAPHY --- */
  h2 {
    font-size: 11pt; color: #0d47a1; font-weight: 700;
    border-left: 3.5px solid #1565c0; padding-left: 8px; margin: 10px 0 5px 0;
  }
  h3 { font-size: 9.5pt; color: #1565c0; margin: 7px 0 3px 0; font-weight: 600; }
  h4 { font-size: 8.5pt; color: #37474f; margin: 5px 0 2px 0; font-weight: 600; }
  strong { color: #0d47a1; }

  /* --- TABLES --- */
  table { width: 100%; border-collapse: collapse; margin: 3px 0 7px 0; font-size: 8pt; }
  thead th {
    background: #0d47a1; color: #fff; padding: 3px 6px;
    text-align: left; font-weight: 600; font-size: 7.5pt;
    text-transform: uppercase; letter-spacing: .4px;
  }
  tbody td { padding: 3px 6px; border-bottom: 1px solid #e0e0e0; }
  tbody tr:nth-child(even) { background: #f5f7fa; }

  /* --- BADGES --- */
  .b { display: inline-block; padding: 1px 6px; border-radius: 8px; font-size: 6.5pt; font-weight: 700; }
  .b-ok  { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
  .b-w   { background: #fff3e0; color: #e65100; border: 1px solid #ffcc80; }
  .b-err { background: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
  .b-i   { background: #e3f2fd; color: #0d47a1; border: 1px solid #90caf9; }
  .b-n   { background: #f3e5f5; color: #6a1b9a; border: 1px solid #ce93d8; }

  /* --- INFO BOXES --- */
  .bx { border-radius: 4px; padding: 5px 10px; margin: 4px 0; font-size: 8pt; }
  .bx-b { background: #e3f2fd; border-left: 3px solid #1565c0; }
  .bx-g { background: #e8f5e9; border-left: 3px solid #2e7d32; }
  .bx-o { background: #fff3e0; border-left: 3px solid #e65100; }
  .bx-r { background: #ffebee; border-left: 3px solid #c62828; }

  /* --- KPI CARDS --- */
  .kpi { display: flex; gap: 8px; margin: 6px 0 8px 0; }
  .kc {
    flex: 1; background: #f5f7fa; border: 1px solid #e0e0e0;
    border-top: 3px solid #1565c0; border-radius: 0 0 4px 4px;
    padding: 6px 6px; text-align: center;
  }
  .kc.g { border-top-color: #2e7d32; } .kc.o { border-top-color: #e65100; }
  .kc.p { border-top-color: #6a1b9a; } .kc.r { border-top-color: #c62828; }
  .kv { font-size: 16pt; font-weight: 700; color: #0d47a1; line-height: 1; }
  .kc.g .kv { color: #2e7d32; } .kc.o .kv { color: #e65100; }
  .kc.p .kv { color: #6a1b9a; } .kc.r .kv { color: #c62828; }
  .kl { font-size: 6.5pt; color: #78909c; text-transform: uppercase; letter-spacing: .4px; margin-top: 2px; }

  /* --- LAYOUT HELPERS --- */
  .hl { background: #e8f5e9 !important; }
  .cols2 { display: flex; gap: 10px; }
  .cols2 > div { flex: 1; }
  .arch-box {
    background: #f5f7fa; border: 1px solid #e0e0e0; border-radius: 4px;
    padding: 7px 10px; font-family: 'Consolas', 'Monaco', monospace;
    font-size: 7pt; line-height: 1.45; white-space: pre; margin: 5px 0;
  }
  .mini-table { font-size: 7.5pt; }
  .mini-table td, .mini-table th { padding: 2px 5px; }
  .author-block {
    text-align: center; margin-top: 12px; padding: 10px 14px;
    background: #f5f7fa; border: 1px solid #e0e0e0; border-radius: 4px;
  }
  .author-block .label { font-size: 7pt; color: #78909c; text-transform: uppercase; letter-spacing: 1.5px; }
  .author-block .name { font-size: 11pt; font-weight: 700; color: #0d47a1; margin: 3px 0; }
  .author-block .org { font-size: 7pt; color: #78909c; }
  .author-block .legal { font-size: 6.5pt; color: #b71c1c; font-weight: 600; margin-top: 4px; letter-spacing: .4px; }
</style>
</head>
<body>
<!-- Each .page = exactly 1 printed page. Repeat .hdr + .conf + .ftr on EVERY page. -->
<!-- CRITICAL: ALL content MUST be inside .bd — this prevents footer overlap -->
<div class="page">
  <div class="hdr">
    <div class="hdr-left">
      <h1>{{TITLE}}</h1>
      <div class="sub">{{SUBTITLE_PAGE_N}}</div>
    </div>
    <div class="hdr-right">
      <div class="dt">{{DATE_LONG}} — {{TIME}} {{TZ}}</div>
      <div>Ref: <strong>{{DOC_REF}}</strong></div>
      <div>Author: <strong>{{AUTHOR}}</strong></div>
    </div>
  </div>
  <div class="conf">&#9888; CONFIDENTIAL — Intellectual Property of {{AUTHOR}} — Unauthorized distribution prohibited &#9888;</div>
  <div class="bd">
    <!-- ALL CONTENT GOES HERE — max-height enforced by .bd -->
  </div>
  <div class="ftr">
    <div class="ftr-l">{{PROJECT_NAME}}</div>
    <div class="ftr-c">CONFIDENTIAL &mdash; &copy; {{AUTHOR}} {{YEAR}}</div>
    <div class="ftr-r">Page {{N}} / {{TOTAL}}</div>
  </div>
</div>
</body>
</html>
```

---

## PHASE 4 — PLAYWRIGHT QA VERIFICATION (MANDATORY)

After generating the document, you MUST run automated QA verification using Playwright.
**Do NOT deliver the document until ALL pages pass QA with zero CRITICAL/ERROR issues.**

### QA Script

Create a temporary `kimera-qa.mjs` file in the project root and run it with `node kimera-qa.mjs`.
The script checks every page for:

1. **Content overflow** — `scrollHeight > clientHeight` means content is clipped by `overflow: hidden`
2. **Footer overlap** — any content element bottom extends past the footer top position
3. **Missing structural elements** — header, confidential banner, footer on every page
4. **Page number correctness** — footer says "Page N / Total" matching actual position
5. **Excessive whitespace** — more than 25% wasted space suggests redistribution needed

```javascript
// kimera-qa.mjs — Kimera QA Verification Script v2.1
import { chromium } from 'playwright';
import { resolve } from 'path';

const FILE = resolve('{{DOCUMENT_FILENAME}}');

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 900, height: 1200 } });
  await page.goto(`file:///${FILE.replace(/\\\\/g, '/')}`, { waitUntil: 'networkidle' });

  const pageCount = await page.locator('.page').count();
  const problems = [];

  for (let i = 0; i < pageCount; i++) {
    const pageEl = page.locator('.page').nth(i);

    // Check .page overflow (phantom blank pages)
    const dims = await pageEl.evaluate(el => ({
      scrollH: el.scrollHeight, clientH: el.clientHeight
    }));
    if (dims.scrollH > dims.clientH + 2) {
      problems.push(`[CRITICAL] Page ${i+1}: PAGE OVERFLOW by ${dims.scrollH - dims.clientH}px`);
    }

    // Check .bd content wrapper exists
    const hasBd = await pageEl.locator('.bd').count();
    if (hasBd === 0) {
      problems.push(`[CRITICAL] Page ${i+1}: Missing .bd content wrapper — footer overlap risk!`);
    }

    // Check .bd overflow (content exceeding safe zone)
    if (hasBd > 0) {
      const bdDims = await pageEl.locator('.bd').evaluate(el => ({
        scrollH: el.scrollHeight, clientH: el.clientHeight,
        maxH: getComputedStyle(el).maxHeight
      }));
      if (bdDims.scrollH > bdDims.clientH + 2) {
        problems.push(`[CRITICAL] Page ${i+1}: CONTENT OVERFLOW by ${bdDims.scrollH - bdDims.clientH}px (clipped by .bd max-height: ${bdDims.maxH})`);
      }
    }

    // Check footer overlap (belt-and-suspenders check)
    const ftr = await pageEl.evaluate(el => {
      const f = el.querySelector('.ftr');
      const bd = el.querySelector('.bd');
      if (!f || !bd) return null;
      const pR = el.getBoundingClientRect();
      const fR = f.getBoundingClientRect();
      const bdR = bd.getBoundingClientRect();
      const gap = (fR.top - pR.top) - (bdR.bottom - pR.top);
      return { gap: gap.toFixed(1) };
    });
    if (ftr && parseFloat(ftr.gap) < 0) {
      problems.push(`[CRITICAL] Page ${i+1}: FOOTER OVERLAP by ${Math.abs(parseFloat(ftr.gap))}px`);
    } else if (ftr && parseFloat(ftr.gap) < 5) {
      problems.push(`[WARNING] Page ${i+1}: Footer too close (${ftr.gap}px gap)`);
    }

    // Check structural elements
    if (await pageEl.locator('.hdr').count() === 0) problems.push(`[ERROR] Page ${i+1}: Missing header`);
    if (await pageEl.locator('.conf').count() === 0) problems.push(`[WARNING] Page ${i+1}: Missing conf banner`);
    if (await pageEl.locator('.ftr').count() === 0) problems.push(`[ERROR] Page ${i+1}: Missing footer`);

    // Check page number
    const num = await pageEl.locator('.ftr-r').textContent().catch(() => '');
    if (num.trim() !== `Page ${i+1} / ${pageCount}`) {
      problems.push(`[ERROR] Page ${i+1}: Wrong page number "${num.trim()}"`);
    }

    // Check excessive whitespace (content < 60% of .bd capacity)
    if (hasBd > 0) {
      const usage = await pageEl.locator('.bd').evaluate(el => {
        const scrollH = el.scrollHeight;
        const maxH = parseFloat(getComputedStyle(el).maxHeight) || el.clientHeight;
        return { pct: ((scrollH / maxH) * 100).toFixed(0), scrollH, maxH: maxH.toFixed(0) };
      });
      if (parseInt(usage.pct) < 60) {
        problems.push(`[WARNING] Page ${i+1}: Low content density (${usage.pct}% of safe zone used)`);
      }
    }
  }

  console.log(`\nKimera QA v2.1 — ${pageCount} pages analyzed`);
  console.log('─'.repeat(50));
  if (problems.length === 0) {
    console.log('✓ ALL PAGES PASS QA — zero issues');
  } else {
    problems.forEach(p => console.log(p));
    const critical = problems.filter(p => p.includes('CRITICAL')).length;
    const errors = problems.filter(p => p.includes('ERROR')).length;
    const warnings = problems.filter(p => p.includes('WARNING')).length;
    console.log(`\nSummary: ${critical} CRITICAL, ${errors} ERROR, ${warnings} WARNING`);
  }

  await browser.close();
  process.exit(problems.filter(p => p.includes('CRITICAL') || p.includes('ERROR')).length > 0 ? 1 : 0);
}
main().catch(e => { console.error(e); process.exit(2); });
```

### QA → Fix → Retest Loop

If the QA script finds problems, fix them using these strategies:

| Problem | Fix Strategy |
|---------|-------------|
| **Missing .bd wrapper** | Wrap all content between `.conf` and `.ftr` in `<div class="bd">...</div>` |
| **CONTENT OVERFLOW** (clipped by .bd) | Move last 1-2 sections from this page to a page with whitespace |
| **PAGE OVERFLOW** (phantom pages) | Reduce content inside `.bd`, or check if `.bd` max-height is correct for format |
| **FOOTER OVERLAP** | Should NOT happen with `.bd` wrapper — verify `.bd` exists and has correct max-height |
| **Excessive whitespace** (>40%) | Pull sections from adjacent overflowing pages |
| **Wrong page numbers** | Renumber all footers sequentially |

**Redistribution priority order:**
1. Move sections to adjacent pages first (keeps thematic flow)
2. If no adjacent page has space, move to the nearest page with >20% whitespace
3. As last resort, add a new page (split the overflowing page)
4. NEVER remove content to fix overflow — redistribute instead

**Iterate until:** `CRITICAL: 0, ERROR: 0`. Warnings are acceptable but should be minimized.

---

## DOCUMENT TYPE TEMPLATES

### Status Memo
Sections: Infrastructure → Containers/URLs → Repositories → Sprints → KB/Data → Open Issues → Architecture → Next Steps → Tech Stack

### Sprint Report
Sections: Sprint Goal → KPI (velocity, stories, bugs) → Completed Stories → Demo Highlights → Bugs Fixed → Remaining Issues → Retrospective → Next Sprint Plan

### Technical Spec
Sections: Problem Statement → Goals & Non-Goals → Proposed Solution → Architecture → API Design → Data Model → Security → Testing → Migration → Timeline

### Custom
Ask user for section list. Generate accordingly.

---

## DESIGN SYSTEM

### Color Palette (5-color semantic system)
| Role    | Primary   | Background | Border    |
|---------|----------|-----------|----------|
| Primary | #0d47a1  | #e3f2fd   | #90caf9  |
| Success | #2e7d32  | #e8f5e9   | #a5d6a7  |
| Warning | #e65100  | #fff3e0   | #ffcc80  |
| Error   | #c62828  | #ffebee   | #ef9a9a  |
| Accent  | #6a1b9a  | #f3e5f5   | #ce93d8  |

### Page Sizes
| Format     | Width   | Height  | CSS @page  | Safe Zone |
|-----------|--------|--------|-----------|-----------|
| A4        | 210mm  | 297mm  | A4        | ~862px    |
| US Letter | 216mm  | 279mm  | letter    | ~794px    |
| US Legal  | 216mm  | 356mm  | legal     | ~1085px   |

---

## CRITICAL DESIGN RULES

1. **FIXED page height** — `.page { height: XXXmm; }` — never `min-height`
2. **overflow: hidden** on `.page` AND on `.bd` — double protection against phantom pages AND footer overlap
3. **NO @page margins** — all spacing inside `.page` padding. `@page { margin: 0; }`
4. **`.bd` content wrapper is MANDATORY** — ALL content between header/conf and footer MUST be inside `<div class="bd">`. The `.bd` has `max-height` per format (218mm A4, 200mm Letter, 277mm Legal) that physically prevents footer overlap. This is the primary layout safety mechanism
5. **Footer = absolute, NOT fixed** — `position: absolute; bottom: 8mm` inside each `.page` div
6. **Each .page gets its own footer** with hardcoded `Page N / X`
7. **Header + confidential banner on EVERY page** — repeated manually per `.page` div
8. **Subtitle varies per page** — describes that page's content focus
9. **print-color-adjust: exact** — forces browsers to print background colors
10. **No external resources** — zero CDN fonts, zero external CSS/JS. 100% self-contained
11. **Screen shadow, print clean** — box-shadow on screen, removed in @media print
12. **Author block only on last page** — INSIDE `.bd`, before the closing `</div>`, centered, with IP notice
13. **Language: English** for structural elements. Content follows user preference
14. **File extension: `.md.html`** — OS reads last ext as HTML. Opens in browser natively
15. **Compact spacing** — Tables: 3px margin. Sections: 10px. Boxes: 4px
16. **Badge triad** — always background + border + text color for accessibility
17. **Content budget: max 780px per page (A4)** — never exceed 95% of `.bd` max-height (824px)
18. **arch-box elements are DANGEROUS** — 20+ lines at 7pt ≈ 280px = 1/3 of safe zone. Always plan carefully
19. **Playwright QA is MANDATORY** — never deliver without automated verification passing
20. **Page structure order**: `.hdr` → `.conf` → `.bd` (content) → `.ftr` — NEVER put content outside `.bd`

---

## PRINT INSTRUCTIONS

Tell the user after generating:
> Open in browser → `Ctrl+P` → Margins: **None** → Background graphics: **On** → Print or Save as PDF.

---

$ARGUMENTS
