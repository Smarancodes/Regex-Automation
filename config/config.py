"""
config.py - Global settings for PDF Regex Automation pipeline
"""
import os

# ── Base paths ────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR   = os.path.join(BASE_DIR, "input_pdfs")
OUTPUT_DIR  = os.path.join(BASE_DIR, "output_pdfs")
JSON_DIR    = os.path.join(BASE_DIR, "output_json")
TEMP_DIR    = os.path.join(BASE_DIR, "temp_images")
PATTERNS_FILE = os.path.join(BASE_DIR, "config", "patterns.json")
MERGED_PDF  = os.path.join(BASE_DIR, "temp_images", "_merged.pdf")

# ── OCR / rasterisation settings ─────────────────────────────────────────────
# DPI: 150 is a sweet spot for office laptops (fast) vs accuracy
# Increase to 200 if OCR gives poor results on scanned docs
RASTER_DPI  = 150

# Tesseract language(s) to use. "eng" = English only (fastest).
# For multi-language docs set e.g. "eng+hin"
TESSERACT_LANG = "eng"

# Minimum characters extracted via native PDF text before we consider
# a page "digital" (and skip OCR for it)
NATIVE_TEXT_MIN_CHARS = 20

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"   # DEBUG / INFO / WARNING
