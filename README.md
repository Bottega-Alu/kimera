# Chimera(R) — Professional Print-Ready Document Generator

> **Turn any AI conversation into a beautifully formatted, print-ready document.**

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

---

## What is Chimera?

Chimera is a **document format and AI skill** that generates professional, paginated, print-ready documents from AI conversations. Output files use the `.md.html` dual format — markdown-structured content rendered as self-contained HTML.

**One file. Zero dependencies. Open in browser. Print.**

### Key Features

- **Print-perfect** — Fixed-height pages, correct pagination, no phantom blank pages
- **Self-contained** — Zero external dependencies (no CDN, no JS, no fonts to load)
- **Works offline** — Save the file, open it anywhere, anytime
- **LLM-agnostic** — Works with Claude, ChatGPT, Gemini, Llama, Copilot, and any LLM
- **Human & AI readable** — Clean semantic structure parseable by both humans and machines
- **Professional design** — 5-color semantic system, KPI cards, status badges, info boxes
- **Multi-format** — A4, US Letter, US Legal page sizes
- **Multi-type** — Status Memos, Sprint Reports, Technical Specs, Custom documents

---

## Quick Start

### Claude Code (Native Skill)

```bash
# Install as plugin
claude /plugin install kimera

# Or copy to your project
cp -r skills/chimera/ your-project/.claude/skills/chimera/

# Or install globally
cp -r skills/chimera/ ~/.claude/skills/chimera/

# Use it
claude> /chimera status report for my project
```

### ChatGPT / Gemini / Any LLM

1. Open `chimera-universal-prompt.md`
2. Copy the entire **SYSTEM PROMPT** section
3. Paste as:
   - **ChatGPT**: Custom GPT instructions, or start of conversation
   - **Gemini**: System prompt or conversation prefix
   - **Any LLM API**: System message parameter
4. Ask: *"Generate a Chimera status memo for [your project]"*

### Manual (Any Editor)

1. Read the template in `skills/chimera/SKILL.md`
2. Copy the HTML/CSS template section
3. Fill in your content
4. Save as `yourfile.md.html`
5. Open in browser → `Ctrl+P` → Margins: None → Print

---

## The `.md.html` Format

The Chimera format uses the dual extension `.md.html`:

| Aspect | Benefit |
|--------|---------|
| **`.html`** (last extension) | OS opens it in the browser natively |
| **`.md.`** (prefix) | Signals markdown-structured content to developers |
| **Self-contained** | Single file, no external resources needed |
| **Print-ready** | `Ctrl+P` → Margins: None → exact page count |
| **Offline** | Works without internet, forever |

---

## Design System

### 5-Color Semantic Palette

| Role | Color | Background | Usage |
|------|-------|-----------|-------|
| **Primary** | `#0d47a1` | `#e3f2fd` | Headers, titles, navigation |
| **Success** | `#2e7d32` | `#e8f5e9` | Healthy, active, completed |
| **Warning** | `#e65100` | `#fff3e0` | Attention, P1 priority |
| **Error** | `#c62828` | `#ffebee` | Critical, P0, confidential |
| **Accent** | `#6a1b9a` | `#f3e5f5` | New items, special |

### Components

- **KPI Cards** — Large metric numbers with colored top borders
- **Status Badges** — Inline colored pills (OK/Warning/Error/Info/New)
- **Info Boxes** — Left-border accent callouts (blue/green/orange/red)
- **Tables** — Dark headers, alternating rows, uppercase labels
- **Author Block** — Centered signature with IP notice

### Typography Scale

```
15pt  — Page title (h1)
11pt  — Section heading (h2) with left border
9.5pt — Subsection (h3)
9pt   — Body text
8pt   — Table content, info boxes
7.5pt — Header metadata
7pt   — Footer, badges
6.5pt — Legal text, fine print
```

---

## Critical Design Rules

These rules solve real print-layout bugs discovered through iteration:

| # | Rule | Why |
|---|------|-----|
| 1 | `height: 297mm` (fixed, not min-height) | Prevents content overflow to extra pages |
| 2 | `overflow: hidden` on `.page` | Prevents phantom blank pages in print |
| 3 | `@page { margin: 0 }` | All spacing inside `.page` padding for consistency |
| 4 | Footer `position: absolute` (not fixed) | `fixed` causes all footers to stack on last page |
| 5 | Hardcoded `Page N/X` per page | CSS counters are unreliable across print engines |
| 6 | Header + banner repeated per `.page` div | Manual repetition — CSS can't reliably repeat headers |
| 7 | `print-color-adjust: exact` | Forces browsers to print background colors |
| 8 | No external resources | Ensures offline functionality and longevity |
| 9 | `box-shadow` screen-only | Clean print output via `@media print` removal |
| 10 | Badge triad (bg + border + text) | Accessibility — readable even without color |

---

## Project Structure

```
kimera/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest for Claude Code
├── skills/
│   └── chimera/
│       └── SKILL.md             # Claude Code native skill
├── chimera-universal-prompt.md  # LLM-agnostic prompt (ChatGPT, Gemini, etc.)
├── examples/
│   └── (example outputs)
├── LICENSE                      # CC BY-NC 4.0 + Commercial dual license
└── README.md                    # This file
```

---

## Installation

### Claude Code Plugin

```bash
# From GitHub
/plugin marketplace add Bottega-Alu/kimera
/plugin install kimera

# From local directory
claude --plugin-dir ./chimera-plugin
```

### Global Skill (Claude Code)

```bash
# Copy to global skills directory
mkdir -p ~/.claude/skills/chimera
cp skills/chimera/SKILL.md ~/.claude/skills/chimera/

# Now /chimera is available in every project
```

### Project Skill (Claude Code)

```bash
# Copy to your project
mkdir -p .claude/skills/chimera
cp skills/chimera/SKILL.md .claude/skills/chimera/

# Commit to share with your team
git add .claude/skills/chimera/
git commit -m "feat: add Chimera document generator skill"
```

---

## License

**Dual License:**

| Use Case | License | Cost |
|----------|---------|------|
| Personal, educational, open-source | CC BY-NC 4.0 | Free (with attribution) |
| Commercial use | Commercial License | Contact author |

**Attribution required** (non-commercial use):
```
Based on Kimera(R) by Francesco Trani
https://github.com/Bottega-Alu/kimera
```

**Chimera(R)** is a trademark of Francesco Trani.

---

## Author

**Francesco Trani**
- GitHub: [@Bottega-Alu](https://github.com/Bottega-Alu)

---

*Made with passion. Designed for print. Built for AI.*
