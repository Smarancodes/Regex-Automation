"""
pdf_to_image.py - Convert a single PDF page to a PIL Image using PyMuPDF.
No Poppler required — PyMuPDF bundles its own renderer.
"""
import logging
import fitz  # PyMuPDF
from PIL import Image
import io

logger = logging.getLogger(__name__)


def pdf_page_to_image(pdf_path: str, page_num: int, dpi: int = 150) -> Image.Image:
    """
    Render a single PDF page as a PIL Image.

    Args:
        pdf_path: Path to the PDF file.
        page_num: Zero-based page index.
        dpi:      Resolution for rasterisation (150 is fast; 200 is more accurate).

    Returns:
        PIL.Image.Image in RGB mode.
    """
    zoom = dpi / 72.0  # 72 dpi is the internal PDF unit
    matrix = fitz.Matrix(zoom, zoom)

    doc = fitz.open(pdf_path)
    try:
        page = doc[page_num]
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        logger.debug("Rasterised page %d at %d dpi  (%dx%d px)", page_num, dpi, image.width, image.height)
        return image
    finally:
        doc.close()
