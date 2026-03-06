# PDF Regex Automation — Tech Stack & Project Explainer

**Document prepared for:** Mphasis Project Review  
**Date:** March 2026  
**Project:** PDF Regex Automation Pipeline  

---

## 1. What This Project Does

This project automates the processing of large PDF documents by performing these steps in order:

```
INPUT PDFs
    │
    ▼  Stage 1: PDF Merge
  MERGED PDF (single file)
    │
    ▼  Stage 2: Text Extraction (Dual-Mode)
  PAGE TEXTS (one string per page)
    │
    ▼  Stage 3: Regex Pattern Matching
  PAGE LABELS (each page assigned a document type)
    │
    ▼  Stage 4: PDF Split
  OUTPUT PDFs (one file per document type)
```

**Example:** Two 10-page PDFs are provided. After processing, pages containing "Invoice" keywords go into `split_Invoice.pdf`, pages with "Purchase Order" go into `split_Purchase_Order.pdf`, and so on.

---

## 2. Technology Stack

### Python 3.9+
- **Why:** Free, open-source, runs on all Windows machines. No licensing cost.
- **Libraries used:** Only 3 third-party packages (see below). Everything else is Python's standard library.

---

### PyMuPDF (`fitz`) — PDF Operations
**Handles:** PDF merge, PDF split, page-to-image rasterisation, native text extraction  
**Version:** 1.24.1  
**Why chosen:**
- Includes its own PDF rendering engine — no heavy system dependencies needed
- Handles all 4 PDF operations in one package (merge, split, render, extract text)
- Works offline, no internet required
- Lightweight — 20–30 MB installed size
- Alternative `pdf2image` requires Poppler (complex C binary install) — avoided here

---

### Pytesseract + Tesseract-OCR — Image-to-Text
**Handles:** Converting scanned page images to machine-readable text  
**Version:** pytesseract 0.3.10  
**Why chosen:**
- Tesseract is the world's most widely used open-source OCR engine (developed at HP, maintained by Google)
- Free, no API keys, fully offline
- `pytesseract` is just a thin Python wrapper — tiny install size
- Alternative (cloud OCR like Google Vision, AWS Textract) was explicitly ruled out for compliance reasons

**Note:** Only needed for scanned PDFs. For digitally-created PDFs (PDFs typed on a computer), text is extracted directly without OCR — faster and 100% accurate.

---

### Pillow — Image Processing
**Version:** 10.3.0  
**Why:** Required by pytesseract to handle image data. Also used for image format conversion.

---

### Python `re` Module — Regex Engine
**Handles:** Matching patterns against extracted page text  
**Why:** This is Python's built-in regular expression engine — zero extra dependency. Supports full POSIX regex syntax, case-insensitive flags, multi-line matching.

---

### JSON (stdlib) — Pattern Configuration
**Handles:** Loading the regex rules from `config/patterns.json`  
**Why:** JSON is human-readable and editable by non-developers. The team can modify document-type detection rules without touching any Python code.

---

## 3. Architecture — Detailed Data Flow

```
┌──────────────────────────────────────────────────────┐
│                   STAGE 1: MERGE                     │
│  pdf_merger.py                                       │
│  Input: [doc1.pdf, doc2.pdf, ...]                    │
│  Tool:  PyMuPDF                                      │
│  Output: merged_temp.pdf (all pages combined)        │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│              STAGE 2: TEXT EXTRACTION                │
│  image_to_text.py + pdf_to_image.py                  │
│                                                      │
│  For each page (0 … N-1):                            │
│    ─── Try A: Native PDF Text ──────────────────     │
│        PyMuPDF reads the PDF's internal text layer   │
│        (Only works if PDF was digitally created)     │
│        Speed: Instant  |  Accuracy: 100%             │
│                                                      │
│    ─── If text too short, Try B: OCR ───────────     │
│        PyMuPDF renders page to PNG image             │
│        Tesseract-OCR reads the image → text          │
│        (Used for scanned / image-based PDFs)         │
│        Speed: 1-3s/page  |  Accuracy: 85-97%        │
│                                                      │
│  Output: [{page: 0, method: "native", text: "..."}, │
│           {page: 1, method: "ocr",    text: "..."}, │
│           ...]                                       │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│            STAGE 3: PATTERN MATCHING                 │
│  pattern_matcher.py                                  │
│                                                      │
│  Loads config/patterns.json:                         │
│  → Compiles each regex once (fast re-use)            │
│  → Tests each page's text against patterns           │
│  → First-match wins: assigns a label to each page   │
│  → Unmatched pages get label "Unmatched"            │
│                                                      │
│  Output: [{page:0, label:"Invoice"}, ...]           │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│               STAGE 4: PDF SPLIT                     │
│  pdf_splitter.py                                     │
│                                                      │
│  Groups pages by label:                              │
│  {"Invoice": [0,1,8], "Contract": [4], ...}         │
│                                                      │
│  Writes one PDF per group:                           │
│  split_Invoice.pdf, split_Contract.pdf, ...         │
│                                                      │
│  Tool: PyMuPDF (copy specific pages to new file)    │
└──────────────────────────────────────────────────────┘
```

---

## 4. Performance Characteristics

| Scenario | Speed | Notes |
|----------|-------|-------|
| Digital PDF, 20 pages | ~2–5 seconds | No OCR needed, native text only |
| Scanned PDF, 20 pages | ~30–60 seconds | Tesseract OCR per page |
| Mixed PDF (30% scanned) | ~10–20 seconds | OCR only where needed |

**Tested configuration:**
- DPI: 150 (default) — fast, accurate for most docs
- RAM: < 200 MB peak (single page processed at a time)
- CPU: Uses a single core — won't freeze the machine

---

## 5. Configuration — How to Customise

### Changing Document Types
Edit **`config/patterns.json`**:
```json
{
  "patterns": [
    {"name": "Invoice",   "regex": "(?i)invoice\\s*(?:no|#)?\\s*[\\d-]+"},
    {"name": "YourType", "regex": "(?i)your_keyword_or_phrase"}
  ]
}
```
- `name` = output PDF label (becomes part of filename)
- `regex` = Python regular expression
- `(?i)` = case-insensitive matching
- No coding required to add new document types

### Changing Performance Settings
Edit **`config/config.py`**:
```python
RASTER_DPI = 150         # Increase to 200 for better OCR on low-quality scans
TESSERACT_LANG = "eng"   # Change to "eng+hin" for Hindi+English docs
```

---

## 6. What Is NOT Used (and Why)

| Excluded Technology | Reason |
|---------------------|--------|
| OpenAI / GPT APIs | Compliance — no external API calls |
| Google Cloud Vision | Compliance — no external API calls |
| AWS Textract | Compliance — no external API calls |
| pdf2image / Poppler | Complex Windows install; PyMuPDF does the same thing |
| EasyOCR / PaddleOCR | Too heavy for office laptops (deep learning models) |
| Docker | Not required; pure Python venv is sufficient |

---

## 7. Security & Compliance

- **100% offline** — no data leaves the machine
- **No API keys** — nothing to manage or rotate
- **No database** — files in, files out
- **Open-source licences only:** PyMuPDF (AGPL/commercial), pytesseract (Apache 2.0), Pillow (HPND), Tesseract (Apache 2.0)

---

## 8. File Inventory

| File / Folder | Purpose |
|---------------|---------|
| `setup.bat` | One-click environment setup (Windows) |
| `requirements.txt` | Python package list with pinned versions |
| `config/config.py` | All tunable settings (paths, DPI, language) |
| `config/patterns.json` | Regex rules — only file non-developers need to edit |
| `src/pdf_merger.py` | Stage 1: Merge multiple PDFs into one |
| `src/pdf_to_image.py` | Stage 2a: Render PDF page as image |
| `src/image_to_text.py` | Stage 2b: Extract text (native + OCR fallback) |
| `src/pattern_matcher.py` | Stage 3: Load patterns and label each page |
| `src/pdf_splitter.py` | Stage 4: Write grouped pages as separate PDFs |
| `src/pipeline.py` | CLI entrypoint — runs all stages end-to-end |
| `tests/test_pipeline.py` | Automated test suite (generates its own test PDFs) |
| `input_pdfs/` | Drop input PDFs here |
| `output_pdfs/` | Split output PDFs appear here |
| `temp_images/` | Temporary working files (auto-managed) |

---

## 9. How to Run

```
Step 1: (One time) Double-click setup.bat
Step 2: Drop PDF files into input_pdfs\
Step 3: venv\Scripts\python src\pipeline.py
```

Output PDFs appear in `output_pdfs\` named by document type.
