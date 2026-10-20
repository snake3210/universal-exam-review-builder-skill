---
name: universal-exam-review-builder
description: >-
  Builds a complete, interactive visual exam review system (SPA + single-file
  offline HTML bundle) for any subject or certification exam (from elementary
  school math/social studies to national professional licensing exams like
  Firefighter Equipment, EMT-P/ACLS, Law, or Engineering). Supports three input
  modes: (1) local PDF/Word/image exam papers, (2) web scraping of public past
  exams, or (3) AI-generated question banks by topic. Performs image/diagram
  cropping, 4-dimensional clinical/logical reverse-engineering (algorithm_path,
  key_triggers, confusion_trap, guideline_check), 5-tab quick cheat sheets, and
  Dark/Light dual-theme responsive UI with mobile sticky navigation and
  pinch-to-zoom.
---

# Universal Exam Review Builder (萬用考題拆解與視覺化複習系統建置器)

## Overview

This skill packages a battle-tested 5-stage methodology for transforming any raw exam source (local past-paper PDFs, public web exam archives, or user-specified study topics) into an interactive **Visual Exam Review System** comprising:
1. **Structured Deep-Analysis Question Bank (`exam_questions.json` & `exam_data.js`)**: Every question is reverse-engineered into a 4-dimensional pedagogical structure (`algorithm_path`, `key_triggers`, `confusion_trap`, `guideline_check`), with automatic handling of disputed/bonus questions (`is_disputed: true`).
2. **High-Resolution Diagram/Figure Cropping (`images/<id>.png`)**: Extracts embedded figures, charts, ECGs, geometry diagrams, or maps without adding text spoilers to the question stem.
3. **Dual-Theme Responsive SPA (`index.html`)**: Features a **Dark Tactical Dashboard (深色戰情室)** and **Light Eye-Care Theme (明亮護眼模式)** toggle, 6-category weakness radar (highlighting <70% accuracy), multi-dimensional filters, trigger-word highlighter, 5-tab Quick Cheat Sheet modal, keyboard shortcuts, mobile sticky bottom navigation bar, and pinch-to-zoom figure lightbox.
4. **Zero-Dependency Single-File Offline Bundle (`<Subject>_終極單一獨立版.html`)**: Inlines the CSS engine, question bank, and optimized Base64 images into a single `.html` file (~2–3 MB) that opens offline on iOS, Android, iPad, Mac, and Windows.

---

## Dependencies

- **`uv`** (`C:\Users\良\.gemini\config\plugins\science\skills\uv\SKILL.md`): Always use `uv run` to execute `scripts/exam_builder_cli.py` and manage packages like `pymupdf`.
- **`managing-python-dependencies`** (`C:\Users\良\.gemini\config\plugins\data-agent-kit-plugin\skills\managing-python-dependencies\SKILL.md`): Never run global `pip install`; keep any project-specific dependencies inside the workspace virtual environment.

---

## Quick Start

```bash
# 1. Inspect or extract text & figure candidates from local exam PDFs
uv run --with pymupdf python "C:/Users/良/.gemini/config/skills/universal-exam-review-builder/scripts/exam_builder_cli.py" extract-pdf \
  --pdf-dir ./pdfs \
  --limit 500 \
  --output ./extracted_raw_questions.json

# 2. Validate the structured 4-dimension question bank JSON
uv run python "C:/Users/良/.gemini/config/skills/universal-exam-review-builder/scripts/exam_builder_cli.py" validate-json \
  --input ./exam_questions.json \
  --limit 500 \
  --output ./validation_report.json

# 3. Build both index.html (SPA) and the Single-File Offline Bundle
uv run --with pymupdf python "C:/Users/良/.gemini/config/skills/universal-exam-review-builder/scripts/exam_builder_cli.py" build-spa \
  --questions ./exam_questions.json \
  --subject-config ./subject_config.json \
  --output ./build_manifest.json
```

---

## Mandatory Workflow & Pilot Gate Protocol

### Stage 0: Assessment Proposal & 3–5 Question Pilot Gate (MANDATORY FIRST STEP)
Before generating a full question bank or writing frontend files, you **MUST** present an assessment and proposal to the user and wait for confirmation:
1. **Identify Input Mode**:
   - **Mode A (Local Files)**: Inspect local PDFs/docs using `extract-pdf`. If a PDF is a pure scanned image without a text layer, notify the user and fall back to multimodal vision page reading.
   - **Mode B (Web Archive)**: Identify official exam URLs and download via `fetch-urls`.
   - **Mode C (Topic Generation)**: Design a syllabus blueprint based on the user's target grade/certification (e.g., Elementary Grade 5 Math, Firefighter Equipment Licensing Exam).
2. **Propose Subject Customization (`subject_config.json`)**:
   - **Categories (4 to 6 domains)** for the top Weakness Radar.
   - **Default Theme**: Recommend `dark` (Dark Tactical Dashboard) for adult/professional licensing exams (EMT-P, Firefighter, Law, Engineering) or `light` (Light Eye-Care Mode) for K-12/elementary school subjects (note: the UI always includes a 1-click `🌙/☀️` toggle button).
   - **Adaptive Card Titles**: Customize the 3 right-pane analysis headers for the subject:
     - Card 1 (`algorithm_path`): e.g., `解題思考決策路徑 (Step-by-Step Path)`
     - Card 2 (`confusion_trap`): e.g., `易混淆誘答陷阱拆解 (Confusion Trap Alert)`
     - Card 3 (`guideline_check`): e.g., `最新法規/修法檢核` (Firefighter/Law), `AHA 最新指引檢核` (Medical), or `核心公式與課綱觀念檢核` (K-12 Math/Science).
3. **Generate 3–5 Pilot Questions**:
   - Produce 3–5 fully annotated sample questions following `resources/question_schema_example.json` and ask the user to approve before scaling to the full dataset.

### Stage 1: Question Extraction & Figure Cropping (No Spoilers)
- Use `crop-images` (250 DPI via PyMuPDF) to crop every figure/chart/diagram into `images/<id>.png`.
- **Inspect every cropped image using multimodal vision** to verify that the figure is complete and to extract visual reasoning steps.
- **No Spoilers Rule**: Never insert AI-interpreted figure descriptions into the `question` field. Place all visual interpretation inside `algorithm_path` and `key_triggers`.

### Stage 2: 4-Dimensional Reverse-Engineering (`exam_questions.json`)
Every question in `exam_questions.json` must include:
- `id`: String identifier (e.g., `"114-55"` or `"MATH-01"`).
- `question`: Exact original stem without spoilers.
- `options`: Array of 4 strings `["(A) ...", "(B) ...", "(C) ...", "(D) ..."]`.
- `answer`: String `"A"` or array `["A", "D"]` for multi-answer questions.
- `category`: Must match one of the configured categories in `subject_config.json`.
- `algorithm_path`: Array of 3–4 sequential reasoning steps `[Step 1, Step 2, ..., Final Conclusion]`. The frontend renders the final step in highlighted emerald green.
- `key_triggers`: Array of short trigger phrases from the stem (highlighted when the user toggles `💡 破題線索`).
- `confusion_trap`: Bullet list starting with `• ` and separated by `\n• `. Explain **why** the distractor options are tempting, cross-reference recurring past-exam families, and wrap key terms in `**bold**` or `` `code` ``.
- `guideline_check`: Bullet list starting with `• ` and separated by `\n• `. Flag any law amendments, updated clinical guidelines, or core formulas.
- Optional `image`: `"images/<id>.png"`.
- Optional `is_disputed`: `true` and `official_answer`: `"B(送分)"` for disputed/bonus items.

### Stage 3: Build 5-Tab Quick Cheat Sheet & Dual-Theme SPA
- Author 5 high-yield comparison tables in `subject_config.json` (`cheat_sheets` array, 5 tabs) summarizing the most frequently tested numbers, formulas, law articles, or differential diagnoses across the question bank.
- Run `validate-json` and `build-spa` to generate `index.html`, `exam_data.js`, and `<Subject>_終極單一獨立版.html`.

---

## Utility Scripts (`scripts/exam_builder_cli.py`)

Always invoke via `uv run` and write outputs to files via `--output`:

1. **`fetch-urls`**: Downloads exam PDFs from a JSON list of `{"id": "...", "url": "..."}` with 1 req/sec rate limiting and exponential backoff.
   - Required args: `--urls-file`, `--limit`, `--output`
2. **`extract-pdf`**: Extracts raw text per page from a folder of PDFs and flags pages with low text density (scanned PDFs) or figure keywords (`如圖`, `下圖`, `圖一`).
   - Required args: `--pdf-dir`, `--limit`, `--output`
3. **`crop-images`**: Crops bounding boxes `[x0, y0, x1, y1]` from PDF pages at 250 DPI into `images/<id>.png`.
   - Required args: `--config`, `--output`
4. **`validate-json`**: Verifies schema completeness, category validity, `• ` bullet formatting, and image existence.
   - Required args: `--input`, `--limit`, `--output`
5. **`build-spa`**: Compiles `index.html`, `exam_data.js`, and the self-contained single-file HTML bundle (`*_終極單一獨立版.html`) with Base64-encoded images and local Tailwind engine.
   - Required args: `--questions`, `--subject-config`, `--output`

---

## Rate Limiting

- `fetch-urls` enforces a cross-process file-locked rate limit of **1 request per second** (`REQUESTS_PER_SECOND = 1.0`) using `time.monotonic()`.
- Transient HTTP 5xx errors are retried up to 3 times with exponential backoff (`2**attempt` seconds) logged to `stderr`.
- HTTP 429 raises `RateLimitError`; HTTP 4xx reads and reports the full response body.

---

## Common Mistakes

1. **Adding Figure Spoilers to `question`**: Never write `(圖中顯示 ST 段上升...)` or `(圖中三角形底為 10 公分...)` inside `question`. Keep `question` pure and put visual findings in `algorithm_path` and `key_triggers`.
2. **Wall-of-Text Explanations**: Failing to format `confusion_trap` and `guideline_check` with `• ` and `\n• ` breaks the bullet-card renderer. Always validate with `validate-json`.
3. **Forgetting Outdated Law/Guideline Warnings**: Old past-exam answers often become wrong after law amendments (e.g., Firefighter Safety Standards, Traffic Laws, or AHA Guidelines). Always highlight the discrepancy in `guideline_check`.
