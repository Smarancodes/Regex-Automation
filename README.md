# PDF Regex Automation

A fully local, no-API-key Python pipeline to **merge**, **OCR**, **pattern-match**, and **split** PDF documents using configurable regex patterns.

---

## Quick Start

### Prerequisites
1. **Python 3.9+** — [python.org/downloads](https://www.python.org/downloads/) *(tick "Add Python to PATH")*
2. **Tesseract-OCR** *(optional — only needed for scanned/image PDFs)*  
   Download: [github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)

### Setup (one time only)
```
Double-click setup.bat
```
This creates `venv/` and installs all Python packages automatically.

### Run the Pipeline
```
1. Drop your PDF files into:   input_pdfs\
2. Edit patterns if needed:    config\patterns.json
3. Activate venv + run:

   venv\Scripts\activate
   python src\pipeline.py
```
Output split PDFs will appear in `output_pdfs\`.

### Run with Specific Files
```
venv\Scripts\python src\pipeline.py --inputs path\to\doc1.pdf path\to\doc2.pdf
```

### Advanced Options
| Flag | Default | Description |
|------|---------|-------------|
| `--inputs` | `input_pdfs/*.pdf` | Override input PDF paths |
| `--patterns` | `config/patterns.json` | Path to regex patterns file |
| `--output` | `output_pdfs/` | Output directory |
| `--dpi` | `150` | Rasterization DPI for OCR (increase for scans) |
| `--lang` | `eng` | Tesseract language(s) e.g. `eng+hin` |
| `--log` | `INFO` | Log verbosity: `DEBUG` / `INFO` / `WARNING` |
| `--clean-temp` | off | Delete temp images after run |

### Run Tests (no real PDFs needed)
```
venv\Scripts\python tests\test_pipeline.py
```
Generates synthetic PDFs, runs the pipeline, and verifies outputs automatically.

---

## Project Structure
```
Regex Automation/
├── input_pdfs/          ← Drop your PDFs here
├── output_pdfs/         ← Split PDFs appear here
├── temp_images/         ← Temporary working files (auto-managed)
├── src/
│   ├── pdf_merger.py    ← Stage 1: Merge PDFs
│   ├── pdf_to_image.py  ← Stage 2a: Page → Image
│   ├── image_to_text.py ← Stage 2b: Image → Text (OCR)
│   ├── pattern_matcher.py ← Stage 3: Regex matching
│   ├── pdf_splitter.py  ← Stage 4: Split by label
│   └── pipeline.py      ← Orchestrator / CLI
├── config/
│   ├── config.py        ← Tunable settings
│   └── patterns.json    ← ★ Edit this to change patterns
├── tests/
│   └── test_pipeline.py ← Automated test suite
├── TECH_STACK.md        ← Manager-facing documentation
├── setup.bat            ← One-click environment setup
└── requirements.txt     ← Python dependencies
```

---

## Editing Patterns
Open `config/patterns.json` and add/edit entries:
```json
{
  "patterns": [
    {"name": "Invoice",  "regex": "(?i)invoice\\s*(?:no|#)?\\s*[\\d-]+"},
    {"name": "MyDoc",    "regex": "(?i)your_keyword_here"}
  ]
}
```
- **name** — becomes the output PDF filename label
- **regex** — standard Python regex (case-insensitive flag built-in with `(?i)`)
- Patterns are checked **first-match wins** in order

---

## Performance Tips (Office Laptops)
- **Digital PDFs**: Instant text extraction, no OCR needed — works great on any hardware
- **Scanned PDFs**: Set `--dpi 150` (default) for speed; increase to `200` only if accuracy is poor
- **Large batches**: Process a few PDFs at a time to keep memory low
