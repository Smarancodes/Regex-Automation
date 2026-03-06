# PDF Regex Automation — Complete Project Guide

**Location:** `c:\Users\Smaran\Desktop\Mphasis\Regex Automation\`  
**Version:** 1.0 | March 2026

---

## Table of Contents
1. [What This Project Does](#what-this-project-does)
2. [How to Run — Quick Reference](#how-to-run--quick-reference)
3. [Every File Explained](#every-file-explained)
4. [The 4-Stage Pipeline](#the-4-stage-pipeline)
5. [Customising Patterns](#customising-patterns)
6. [Accuracy Verification](#accuracy-verification)
7. [Troubleshooting](#troubleshooting)

---

## What This Project Does

Takes **2 or more PDFs**, merges them, reads every page, and sorts each page into a separate output PDF based on **what type of document it is** (Invoice, Contract, Purchase Order, etc.). The document type is detected using **regex patterns** you define in a JSON file — no AI, no internet, no API keys.

**Example:**
```
Input:  financial_report.pdf (17 pages) + accounts.pdf (15 pages)
           ↓  Merge → 32 pages total
           ↓  Read each page text
           ↓  Match against patterns
Output: split_Invoice.pdf      (pages 1, 4, 9)
        split_Contract.pdf     (pages 2, 3)
        split_Report.pdf       (pages 5, 6, 7)
        split_Unmatched.pdf    (all unrecognised pages)
```

---

## How to Run — Quick Reference

### First time only
```
Double-click setup.bat
```

### Every subsequent run
```bat
REM Step 1 — Clean old files (optional, asks for confirmation)
venv\Scripts\python src\pipeline.py --clean

REM Step 2 — Drop your PDFs into input_pdfs\

REM Step 3 — Run the pipeline
venv\Scripts\python src\pipeline.py

REM Step 4 — Check output_pdfs\ for results

REM Step 5 — Verify accuracy (optional)
venv\Scripts\python verify_accuracy.py
```

### Run automated self-tests (no PDFs needed)
```
venv\Scripts\python tests\test_pipeline.py
```

### Generate sample PDFs for demo
```
venv\Scripts\python generate_samples.py
```

---

## Every File Explained

### Root-level Files

#### `setup.bat`
**Purpose:** One-click environment setup for Windows.  
**What it does:**
- Checks Python is installed
- Creates the `venv\` virtual environment
- Installs all required Python packages (PyMuPDF, pytesseract, Pillow)
- Checks if Tesseract-OCR is installed (optional, only for scanned PDFs)

**When to run:** Once, the very first time you use the project. No need to run again unless you delete `venv\`.

---

#### `requirements.txt`
**Purpose:** List of Python packages the project depends on, with exact version numbers.  
**Contents:**
```
PyMuPDF==1.24.1      ← PDF operations (merge, split, render, extract text)
pytesseract==0.3.10  ← Python wrapper for Tesseract OCR
Pillow==10.3.0       ← Image handling (used by pytesseract)
```
**When to use:** Only referenced by `setup.bat`. You don't need to edit this.

---

#### `generate_samples.py`
**Purpose:** Creates 2 realistic 10-page Mphasis-style sample PDFs for testing when you don't have real PDFs handy.  
**What it generates:**
- `input_pdfs\sample_doc1_march2024.pdf` — mix of Invoices, POs, Contract, Receipt, Report, Memo
- `input_pdfs\sample_doc2_march2024.pdf` — mix of Invoices, Contracts, Receipts, Reports, POs

**When to run:**
```
venv\Scripts\python generate_samples.py
```

---

#### `download_real_pdfs.py`
**Purpose:** Attempts to download real public PDFs from the internet into `input_pdfs\` for testing.  
**Note:** May fail if office firewall blocks external downloads. If it fails, manually download any PDF from your browser and drop it into `input_pdfs\`.

**When to run:**
```
venv\Scripts\python download_real_pdfs.py
```

---

#### `verify_accuracy.py`
**Purpose:** Accuracy checker — re-reads every PDF in `output_pdfs\`, extracts text from each page, and verifies the page's text actually matches the label/pattern it was sorted under. Gives a % accuracy score per file and overall.  
**Output example:**
```
split_Invoice.pdf     10/10 pages  100.0%  [PASS]
split_Contract.pdf     3/3 pages  100.0%  [PASS]
OVERALL ACCURACY: 32/32 pages = 100.0%
```
**When to run:** After every pipeline run to confirm results are correct.
```
venv\Scripts\python verify_accuracy.py
```

---

#### `README.md`
**Purpose:** Short quick-start guide. Covers prerequisites, setup, CLI flags, and pattern editing in brief.

---

#### `TECH_STACK.md`
**Purpose:** **Manager-facing documentation.** Contains full architecture diagram, data flow, technology choices with justifications, performance benchmarks, security & compliance notes, and a complete file inventory. Share this with your manager to explain the project.

---

### `src\` — Core Pipeline Modules

#### `src\pipeline.py` ⭐ (Main entry point)
**Purpose:** Orchestrates all 4 pipeline stages end-to-end. This is the only file you directly run.  
**What it does:**
1. Reads input PDFs from `input_pdfs\` (or from `--inputs` flag)
2. Calls `pdf_merger.py` → merge
3. Calls `image_to_text.py` for each page → extract text
4. Calls `pattern_matcher.py` → assign labels
5. Calls `pdf_splitter.py` → write output PDFs
6. Prints a full results table

**CLI flags:**
| Flag | Effect |
|------|--------|
| `--clean` | Clear input + output folders (asks confirmation) |
| `--inputs a.pdf b.pdf` | Specify exact input files instead of auto-discovering |
| `--patterns path/to/file.json` | Use a custom patterns file |
| `--dpi 200` | Increase OCR resolution (default: 150) |
| `--lang eng+hin` | Add Hindi OCR support |
| `--log DEBUG` | Show detailed debug logs |
| `--clean-temp` | Delete temp_images/ after run |

---

#### `src\pdf_merger.py`
**Purpose:** Merges multiple PDF files into a single PDF in memory order.  
**Key function:** `merge_pdfs(pdf_paths, output_path)` — opens each PDF and inserts its pages sequentially into a new document. Validates all files exist before starting. Logs page count.  
**Technology:** PyMuPDF (`fitz`)

---

#### `src\pdf_to_image.py`
**Purpose:** Converts a single PDF page into a PIL (Python Imaging Library) image for OCR processing.  
**Key function:** `pdf_page_to_image(pdf_path, page_num, dpi=150)` — renders the PDF page at the specified DPI using PyMuPDF's built-in renderer. Returns a PIL Image in RGB format.  
**Technology:** PyMuPDF (no Poppler required)  
**Note:** Only used as a fallback when native text extraction fails (scanned PDFs).

---

#### `src\image_to_text.py` ⭐ (Accuracy-critical)
**Purpose:** Extracts text from a single PDF page using the smartest available method.  
**Dual-mode strategy:**
1. **Try native text extraction first** — PyMuPDF reads the PDF's embedded text layer. Instant, 100% accurate. Works for any PDF created digitally (Word, Excel, SAP exports, etc.)
2. **If native text is too short (<20 chars), fall back to Tesseract OCR** — rasterises the page to an image and runs OCR. Used only for scanned paper documents.

**Key function:** `extract_text(pdf_path, page_num, dpi, lang, native_min_chars)` → returns `{"page": int, "method": "native"|"ocr", "text": str}`  
**Technology:** PyMuPDF + pytesseract

---

#### `src\pattern_matcher.py`
**Purpose:** Loads regex patterns from JSON and assigns a label to each page's text.  
**Key functions:**
- `load_patterns(json_path)` — reads `patterns.json`, compiles each regex once for efficiency
- `match_page(text, patterns)` — first-match wins, returns label name or "Unmatched"
- `match_all_pages(page_texts, patterns)` — applies matching to all pages, logs results

**Technology:** Python `re` module (built-in, no dependencies)

---

#### `src\pdf_splitter.py`
**Purpose:** Groups pages by their matched label and writes one output PDF per group.  
**Key functions:**
- `build_page_groups(matched_pages)` — groups page indices: `{"Invoice": [0,1,8], "Contract": [4]}`
- `split_pdf_by_groups(merged_pdf, page_groups, output_dir)` — copies specific page indices into new PDFs, sanitises label names for safe filenames

**Technology:** PyMuPDF

---

#### `src\__init__.py`
**Purpose:** Makes `src\` a Python package so modules inside it can import each other cleanly.  
**Content:** Nearly empty — just a comment. Never needs editing.

---

### `config\` — Settings & Pattern Rules

#### `config\patterns.json` ⭐ (The only file non-developers need to edit)
**Purpose:** Defines what keywords/phrases identify each document type. One entry per document type.  
**Format:**
```json
{
  "patterns": [
    {"name": "Invoice",        "regex": "(?i)invoice\\s*(?:no|#)?\\s*[\\d-]*"},
    {"name": "Purchase_Order", "regex": "(?i)purchase\\s*order"},
    {"name": "Contract",       "regex": "(?i)\\b(agreement|contract|terms and conditions)\\b"},
    {"name": "Receipt",        "regex": "(?i)\\b(receipt|payment received)\\b"},
    {"name": "Report",         "regex": "(?i)\\b(report|summary|analysis|findings)\\b"}
  ]
}
```
**Rules:**
- `name` → becomes the output PDF filename (`split_<name>.pdf`)
- `regex` → Python regular expression. `(?i)` = case-insensitive
- Patterns are checked **in order** — first match wins
- Add as many patterns as you need — no code changes required

---

#### `config\config.py`
**Purpose:** Central settings file for paths and performance parameters.  
**Key settings:**
```python
RASTER_DPI = 150          # OCR resolution. Increase to 200 for better accuracy on blurry scans
TESSERACT_LANG = "eng"    # OCR language. Use "eng+hin" for Hindi documents
NATIVE_TEXT_MIN_CHARS = 20 # Minimum chars to consider a page "digital" (skip OCR)
```
**When to edit:** If OCR accuracy is poor on scanned docs, increase `RASTER_DPI` to 200. Change `TESSERACT_LANG` for non-English documents.

---

#### `config\__init__.py`
**Purpose:** Makes `config\` a Python package for clean imports. Never needs editing.

---

### `tests\` — Automated Tests

#### `tests\test_pipeline.py`
**Purpose:** Self-contained end-to-end test suite. Generates its own test PDFs with known content, runs the full pipeline, and asserts every page ends up in the correct output PDF.  
**Does NOT need any external PDFs.** Creates and deletes its own temp files automatically.  
**Result:** Prints PASS/FAIL per document type and an overall PASS/FAIL verdict.

**When to run:** Any time you change `patterns.json` or any `src\` file, run this to confirm nothing broke.
```
venv\Scripts\python tests\test_pipeline.py
```

---

### Folders

| Folder | Purpose |
|--------|---------|
| `venv\` | Python virtual environment. **Never touch or delete this** (re-run `setup.bat` if deleted) |
| `input_pdfs\` | **Drop your input PDFs here.** All `.pdf` files in this folder are auto-processed |
| `output_pdfs\` | **Collect your split output PDFs from here.** One PDF per matched pattern |
| `temp_images\` | Temporary working files created during OCR. Auto-managed — safe to delete manually if disk space is low |

---

## The 4-Stage Pipeline

```
Stage 1: MERGE
  input_pdfs/*.pdf  →  temp_images/_merged.pdf
  (all input PDFs combined into one file, pages in order)

Stage 2: EXTRACT TEXT
  For each page in merged PDF:
    → Try native PDF text (instant, 100% for digital PDFs)
    → If blank, run Tesseract OCR (for scanned pages)
  Output: list of {page, method, text}

Stage 3: PATTERN MATCH
  For each page text:
    → Test against each regex in patterns.json (in order)
    → Assign first matching label, or "Unmatched"
  Output: list of {page, label}

Stage 4: SPLIT
  Group pages by label
  Write one PDF per group to output_pdfs/
  Output: split_Invoice.pdf, split_Contract.pdf, etc.
```

---

## Customising Patterns

Open `config\patterns.json` — add a new entry:

```json
{"name": "Delivery_Note", "regex": "(?i)delivery\\s*note|challan"}
```

**Tips for writing regex:**
- `(?i)` at the start = case-insensitive (always include this)
- `\\s*` = allow spaces between words
- `\\b` = word boundary (prevents partial matches)
- `|` = OR (match either side)
- Test your regex at: https://regex101.com (select Python flavour)

---

## Accuracy Verification

Run after every pipeline execution:
```
venv\Scripts\python verify_accuracy.py
```

**What it checks:** For each output PDF, re-reads every page and confirms the text actually matches the label. If `split_Invoice.pdf` contains a page with no invoice keywords, it will flag it as a mismatch.

**Expected result for digital PDFs:** 100% accuracy  
**Expected result for scanned PDFs:** 85–97% (depends on scan quality)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `No PDFs found in input_pdfs/` | Drop at least one `.pdf` file into `input_pdfs\` |
| Pages in wrong output file | Edit regex in `config\patterns.json` to be more specific |
| OCR text is garbled | Increase `RASTER_DPI` to 200 in `config\config.py` |
| Tesseract not found | Only needed for scanned PDFs. Install from https://github.com/UB-Mannheim/tesseract/wiki |
| `venv` missing | Re-run `setup.bat` |
| Need to start fresh | Run `venv\Scripts\python src\pipeline.py --clean` |
