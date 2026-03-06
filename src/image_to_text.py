"""
image_to_text.py - Extract text from a PDF page.

Strategy (dual-mode for max accuracy + speed):
  1. Try PyMuPDF native text extraction  →  instant, 100% accurate for digital PDFs
  2. If text is too sparse, fall back to Tesseract OCR  →  handles scanned pages
"""
import logging
import sys
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# Import siblings
sys.path.insert(0, __file__.rsplit("src", 1)[0])
from src.pdf_to_image import pdf_page_to_image

logger = logging.getLogger(__name__)


def _native_text(pdf_path: str, page_num: int) -> str:
    """Extract text using PyMuPDF's built-in text layer (digital PDFs only)."""
    with fitz.open(pdf_path) as doc:
        page = doc[page_num]
        # "text" mode gives clean plain text; "blocks" gives layout-aware extraction
        text = page.get_text("text")
    return text.strip()


def _ocr_text(pdf_path: str, page_num: int, dpi: int, lang: str) -> str:
    """Rasterise the page and run Tesseract OCR on it."""
    image: Image.Image = pdf_page_to_image(pdf_path, page_num, dpi=dpi)
    # --psm 3 = auto page segmentation (best for full-page docs)
    custom_config = f"--oem 3 --psm 3 -l {lang}"
    text = pytesseract.image_to_string(image, config=custom_config)
    return text.strip()


def extract_text(
    pdf_path: str,
    page_num: int,
    dpi: int = 150,
    lang: str = "eng",
    native_min_chars: int = 20,
) -> dict:
    """
    Extract text from a single PDF page using the best available method.

    Returns:
        {
            "page": page_num,
            "method": "native" | "ocr",
            "text": "<extracted text>"
        }
    """
    native = _native_text(pdf_path, page_num)

    if len(native) >= native_min_chars:
        logger.debug("Page %d: native text extracted (%d chars)", page_num, len(native))
        return {"page": page_num, "method": "native", "text": native}

    logger.debug("Page %d: native text too short (%d chars), running OCR …", page_num, len(native))
    try:
        ocr = _ocr_text(pdf_path, page_num, dpi=dpi, lang=lang)
        return {"page": page_num, "method": "ocr", "text": ocr}
    except pytesseract.TesseractNotFoundError:
        logger.error(
            "Tesseract not found on PATH. "
            "Install it from: https://github.com/UB-Mannheim/tesseract/wiki"
        )
        # Return whatever little native text we have rather than crashing
        return {"page": page_num, "method": "native_fallback", "text": native}
