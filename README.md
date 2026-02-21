# Kimera(R) — Professional Print-Ready Document Generator

> **EN** Turn any AI conversation into a beautifully formatted, print-ready document.
> **IT** Trasforma qualsiasi conversazione AI in un documento professionale, pronto per la stampa.
> **PT** Transforme qualquer conversa de IA em um documento profissional, pronto para impressao.

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Buy Me an Aperitivo](https://img.shields.io/badge/Buy%20Me%20an%20Aperitivo-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/bottega.alu)

---

## Why "Kimera"?

**Kimera** is the Italian spelling of *Chimera* — the mythical creature that fuses different beings into one. Just like its namesake, Kimera fuses **Markdown structure** and **HTML rendering** into a single self-contained file: the `.md.html` format.

The name also carries a hidden play on words:

| Reading | Meaning |
|---------|---------|
| **Kimera** | Italian for Chimera — a fusion of different natures |
| **K + imera** | From Greek *khimaira* — "she-goat", a wild hybrid |

One name. Two worlds. One file.

*Kimera e la grafia italiana di Chimera — la creatura mitologica che fonde esseri diversi in uno. Proprio come il suo omonimo, Kimera fonde struttura Markdown e rendering HTML in un unico file autonomo.*

*Kimera e a grafia italiana de Quimera — a criatura mitologica que funde seres diferentes em um so. Assim como seu homonimo, Kimera funde estrutura Markdown e renderizacao HTML em um unico arquivo autonomo.*

---

## What is Kimera? | Cos'e Kimera? | O que e Kimera?

Kimera is a **document format and AI skill** that generates professional, paginated, print-ready documents from AI conversations. Output files use the `.md.html` dual format — markdown-structured content rendered as self-contained HTML.

**One file. Zero dependencies. Open in browser. Print. Edit in Word.**

### Key Features | Caratteristiche | Recursos

- **Print-perfect** — Fixed-height pages, correct pagination, no phantom blank pages
- **Self-contained** — Zero external dependencies (no CDN, no JS, no fonts to load)
- **Works offline** — Save the file, open it anywhere, anytime
- **LLM-agnostic** — Works with Claude, ChatGPT, Gemini, Llama, Copilot, and any LLM
- **Human & AI readable** — Clean semantic structure parseable by both humans and machines
- **Professional design** — 5-color semantic system, KPI cards, status badges, info boxes
- **Multi-format** — A4, US Letter, US Legal page sizes
- **Multi-type** — Status Memos, Sprint Reports, Technical Specs, Custom documents
- **Word processor compatible** — Open and edit in MS Word, LibreOffice Writer, Google Docs

---

## Word Processor Compatibility | Compatibilita Word Processor | Compatibilidade

Kimera `.md.html` files are standard HTML — they can be opened and edited in **any word processor** that supports HTML:

| Application | How to open | Edit | Print |
|------------|------------|------|-------|
| **Microsoft Word** | File → Open → select `.md.html` | Full editing, styles preserved | Direct print |
| **LibreOffice Writer** | File → Open → select `.md.html` | Full editing, styles preserved | Direct print |
| **Google Docs** | File → Open → Upload `.md.html` | Partial editing (some styles lost) | Direct print |
| **WPS Office** | File → Open → select `.md.html` | Full editing | Direct print |
| **Any browser** | Double-click the file | View only | `Ctrl+P` → Margins: None |

> **Tip / Suggerimento / Dica:** After opening in Word/LibreOffice, you can Save As `.docx` or `.odt` to continue editing in native format. Colors, tables, badges, and layout are preserved.
>
> *Dopo aver aperto in Word/LibreOffice, puoi salvare come `.docx` o `.odt` per continuare a editare nel formato nativo. Colori, tabelle, badge e layout sono preservati.*
>
> *Apos abrir no Word/LibreOffice, voce pode salvar como `.docx` ou `.odt` para continuar editando no formato nativo. Cores, tabelas, badges e layout sao preservados.*

---

## Quick Start | Inizio Rapido | Inicio Rapido

### Claude Code (Native Skill)

```bash
# Install as plugin | Installa come plugin | Instale como plugin
/plugin marketplace add Bottega-Alu/kimera
/plugin install kimera

# Or copy to your project | O copia nel tuo progetto | Ou copie para seu projeto
cp -r skills/kimera/ your-project/.claude/skills/kimera/

# Or install globally | O installa globalmente | Ou instale globalmente
cp -r skills/kimera/ ~/.claude/skills/kimera/

# Use it | Usalo | Use
/kimera status report for my project
```

### ChatGPT / Gemini / Any LLM

1. Open `kimera-universal-prompt.md`
2. Copy the entire **SYSTEM PROMPT** section
3. Paste as:
   - **ChatGPT**: Custom GPT instructions, or start of conversation
   - **Gemini**: System prompt or conversation prefix
   - **Any LLM API**: System message parameter
4. Ask: *"Generate a Kimera status memo for [your project]"*

### Manual | Manuale | Manual

1. Read the template in `skills/kimera/SKILL.md`
2. Copy the HTML/CSS template section
3. Fill in your content
4. Save as `yourfile.md.html`
5. Open in browser → `Ctrl+P` → Margins: None → Print
6. Or open in Word/LibreOffice to edit before printing

---

## The `.md.html` Format | Il formato `.md.html` | O formato `.md.html`

The Kimera format uses the dual extension `.md.html`:

| Aspect | Benefit |
|--------|---------|
| **`.html`** (last extension) | OS opens it in the browser natively |
| **`.md.`** (prefix) | Signals markdown-structured content to developers |
| **Self-contained** | Single file, no external resources needed |
| **Print-ready** | `Ctrl+P` → Margins: None → exact page count |
| **Word-editable** | Open in MS Word, LibreOffice, Google Docs for editing |
| **Offline** | Works without internet, forever |

---

## Design System | Sistema di Design | Sistema de Design

### 5-Color Semantic Palette

| Role | Color | Background | Usage |
|------|-------|-----------|-------|
| **Primary** | `#0d47a1` | `#e3f2fd` | Headers, titles, navigation |
| **Success** | `#2e7d32` | `#e8f5e9` | Healthy, active, completed |
| **Warning** | `#e65100` | `#fff3e0` | Attention, P1 priority |
| **Error** | `#c62828` | `#ffebee` | Critical, P0, confidential |
| **Accent** | `#6a1b9a` | `#f3e5f5` | New items, special |

### Components | Componenti | Componentes

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

## Critical Design Rules | Regole di Design Critiche | Regras Criticas de Design

These rules solve real print-layout bugs discovered through iteration:

*Queste regole risolvono bug reali di impaginazione scoperti durante lo sviluppo iterativo.*

*Essas regras resolvem bugs reais de layout de impressao descobertos durante o desenvolvimento iterativo.*

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

## Project Structure | Struttura Progetto | Estrutura do Projeto

```
kimera/
├── .claude-plugin/
│   └── plugin.json                # Plugin manifest for Claude Code
├── skills/
│   └── kimera/
│       └── SKILL.md               # Claude Code native skill
├── kimera-universal-prompt.md     # LLM-agnostic prompt (ChatGPT, Gemini, etc.)
├── examples/
│   └── (example outputs)
├── LICENSE                        # CC BY-NC 4.0 + Commercial dual license
├── MARKETING-PROMPT.md            # Growth marketing prompt template
└── README.md                      # This file
```

---

## Installation | Installazione | Instalacao

### Claude Code Plugin

```bash
# From GitHub | Da GitHub | Do GitHub
/plugin marketplace add Bottega-Alu/kimera
/plugin install kimera

# From local directory | Da cartella locale | De diretorio local
claude --plugin-dir ./kimera
```

### Global Skill (Claude Code)

```bash
# Copy to global skills | Copia nelle skills globali | Copie para skills globais
mkdir -p ~/.claude/skills/kimera
cp skills/kimera/SKILL.md ~/.claude/skills/kimera/

# Now /kimera is available in every project
# Ora /kimera e disponibile in ogni progetto
# Agora /kimera esta disponivel em todos os projetos
```

### Project Skill (Claude Code)

```bash
# Copy to your project | Copia nel tuo progetto | Copie para seu projeto
mkdir -p .claude/skills/kimera
cp skills/kimera/SKILL.md .claude/skills/kimera/

# Commit to share with your team
git add .claude/skills/kimera/
git commit -m "feat: add Kimera document generator skill"
```

---

## License | Licenza | Licenca

**Dual License:**

| Use Case | License | Cost |
|----------|---------|------|
| Personal, educational, open-source | CC BY-NC 4.0 | Free (with attribution) |
| Commercial use | Aperitivo License | [Buy me an aperitivo](https://buymeacoffee.com/bottega.alu) |

> **Commercial license = buy the author an aperitivo.** That's it. One coffee, one license. Salute!
>
> *Licenza commerciale = offrimi un aperitivo. Tutto qui. Un caffe, una licenza. Salute!*
>
> *Licenca comercial = me pague um aperitivo. So isso. Um cafe, uma licenca. Saude!*
>
> [![Buy Me an Aperitivo](https://img.shields.io/badge/Buy%20Me%20an%20Aperitivo-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/bottega.alu)

**Attribution required** (non-commercial use):
```
Based on Kimera(R) by Francesco Trani
https://github.com/Bottega-Alu/kimera
```

**Kimera(R)** is a trademark of Francesco Trani.

---

## Author | Autore | Autor

**Francesco Trani**
- GitHub: [@Bottega-Alu](https://github.com/Bottega-Alu)
- Aperitivo: [buymeacoffee.com/bottega.alu](https://buymeacoffee.com/bottega.alu)

---

*Made with passion. Designed for print. Built for AI.*
*Fatto con passione. Progettato per la stampa. Costruito per l'AI.*
*Feito com paixao. Projetado para impressao. Construido para IA.*
