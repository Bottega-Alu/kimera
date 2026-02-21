---
name: kimera
description: Parse conversations and format print-ready .md.html documents with professional layout. Use when user asks for memos, reports, specs, status updates, sprint reports, or any printable document.
argument-hint: "[topic or document type]"
allowed-tools: Read, Grep, Glob, Write, AskUserQuestion, Bash
---

# Kimera(R) — Professional Print-Ready Document Parser & Formatter v1.0

> **Format:** `.md.html` — Markdown-structured content rendered as self-contained HTML.
> Opens natively in any browser. Print-ready with `Ctrl+P` (margins: None).
> No external dependencies. Works offline. Human & AI readable.

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

## PHASE 3 — FORMATTING

### File naming:
```
{PROJECT}_{TYPE}_{YYYY-MM-DD}.md.html
```
Examples: `LEXE_STATUS_2026-02-21.md.html`, `MYAPP_SPRINT-8_2026-02-21.md.html`

Place in project root directory.

### Page planning:
1. Estimate content volume BEFORE writing
2. Plan which sections go on which page
3. Each `.page` div = exactly 1 printed page (fixed height, overflow hidden)
4. Target: 2-5 pages. If content exceeds 5 pages, condense
5. Footer page numbers MUST match: Page 1/{total}, Page 2/{total}, etc.

---

## HTML/CSS TEMPLATE

Use this EXACT template structure. Adapt colors, sections, and content but preserve the
layout system, print behavior, and design patterns.

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
  .hdr {
    display: flex; justify-content: space-between; align-items: flex-end;
    border-bottom: 2.5px solid #0d47a1; padding-bottom: 6px; margin-bottom: 10px;
  }
  .hdr-left h1 { font-size: 15pt; font-weight: 700; color: #0d47a1; }
  .hdr-left .sub { font-size: 8pt; color: #546e7a; margin-top: 1px; }
  .hdr-right { text-align: right; font-size: 7.5pt; color: #455a64; line-height: 1.45; }
  .hdr-right .dt { font-weight: 700; color: #0d47a1; font-size: 8.5pt; }
  .conf {
    background: #b71c1c; color: #fff; text-align: center;
    padding: 4px 0; font-size: 7pt; font-weight: 700;
    letter-spacing: 2.5px; text-transform: uppercase; margin-bottom: 10px;
  }
  .ftr {
    position: absolute; bottom: 10mm; left: 16mm; right: 16mm;
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1.5px solid #0d47a1; padding-top: 4px; font-size: 7pt; color: #546e7a;
  }
  .ftr-l { font-weight: 600; color: #0d47a1; }
  .ftr-c { color: #b71c1c; font-weight: 700; letter-spacing: .8px; font-size: 6.5pt; }
  .ftr-r { font-weight: 600; }
  h2 {
    font-size: 11pt; color: #0d47a1; font-weight: 700;
    border-left: 3.5px solid #1565c0; padding-left: 8px; margin: 11px 0 6px 0;
  }
  h3 { font-size: 9.5pt; color: #1565c0; margin: 8px 0 4px 0; font-weight: 600; }
  strong { color: #0d47a1; }
  table { width: 100%; border-collapse: collapse; margin: 4px 0 8px 0; font-size: 8pt; }
  thead th {
    background: #0d47a1; color: #fff; padding: 4px 6px;
    text-align: left; font-weight: 600; font-size: 7.5pt;
    text-transform: uppercase; letter-spacing: .4px;
  }
  tbody td { padding: 3.5px 6px; border-bottom: 1px solid #e0e0e0; }
  tbody tr:nth-child(even) { background: #f5f7fa; }
  .b { display: inline-block; padding: 1px 6px; border-radius: 8px; font-size: 6.5pt; font-weight: 700; }
  .b-ok  { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
  .b-w   { background: #fff3e0; color: #e65100; border: 1px solid #ffcc80; }
  .b-err { background: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
  .b-i   { background: #e3f2fd; color: #0d47a1; border: 1px solid #90caf9; }
  .b-n   { background: #f3e5f5; color: #6a1b9a; border: 1px solid #ce93d8; }
  .bx { border-radius: 4px; padding: 6px 10px; margin: 5px 0; font-size: 8pt; }
  .bx-b { background: #e3f2fd; border-left: 3px solid #1565c0; }
  .bx-g { background: #e8f5e9; border-left: 3px solid #2e7d32; }
  .bx-o { background: #fff3e0; border-left: 3px solid #e65100; }
  .bx-r { background: #ffebee; border-left: 3px solid #c62828; }
  .kpi { display: flex; gap: 8px; margin: 8px 0 10px 0; }
  .kc {
    flex: 1; background: #f5f7fa; border: 1px solid #e0e0e0;
    border-top: 3px solid #1565c0; border-radius: 0 0 4px 4px;
    padding: 7px 6px; text-align: center;
  }
  .kc.g { border-top-color: #2e7d32; } .kc.o { border-top-color: #e65100; }
  .kc.p { border-top-color: #6a1b9a; } .kc.r { border-top-color: #c62828; }
  .kv { font-size: 16pt; font-weight: 700; color: #0d47a1; line-height: 1; }
  .kc.g .kv { color: #2e7d32; } .kc.o .kv { color: #e65100; }
  .kc.p .kv { color: #6a1b9a; } .kc.r .kv { color: #c62828; }
  .kl { font-size: 6.5pt; color: #78909c; text-transform: uppercase; letter-spacing: .4px; margin-top: 2px; }
  .hl { background: #e8f5e9 !important; }
  .author-block {
    text-align: center; margin-top: 14px; padding: 10px 14px;
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
  <!-- CONTENT -->
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
| Format     | Width   | Height  | CSS @page  |
|-----------|--------|--------|-----------|
| A4        | 210mm  | 297mm  | A4        |
| US Letter | 216mm  | 279mm  | letter    |
| US Legal  | 216mm  | 356mm  | legal     |

---

## CRITICAL DESIGN RULES

1. **FIXED page height** — `.page { height: XXXmm; }` — never `min-height`
2. **overflow: hidden** on `.page` — prevents phantom blank print pages
3. **NO @page margins** — all spacing inside `.page` padding. `@page { margin: 0; }`
4. **Footer = absolute, NOT fixed** — `position: absolute` inside each `.page` div
5. **Each .page gets its own footer** with hardcoded `Page N / X`
6. **Header + confidential banner on EVERY page** — repeated manually per `.page` div
7. **Subtitle varies per page** — describes that page's content focus
8. **print-color-adjust: exact** — forces browsers to print background colors
9. **No external resources** — zero CDN fonts, zero external CSS/JS. 100% self-contained
10. **Screen shadow, print clean** — box-shadow on screen, removed in @media print
11. **Author block only on last page** — before footer, centered, with IP notice
12. **Language: English** for structural elements. Content follows user preference
13. **File extension: `.md.html`** — OS reads last ext as HTML. Opens in browser natively
14. **Compact spacing** — Tables: 4px margin. Sections: 11px. Boxes: 5px
15. **Badge triad** — always background + border + text color for accessibility

---

## PRINT INSTRUCTIONS

Tell the user after generating:
> Open in browser → `Ctrl+P` → Margins: **None** → Background graphics: **On** → Print or Save as PDF.

---

$ARGUMENTS
