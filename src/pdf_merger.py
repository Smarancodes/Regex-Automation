"""
pdf_merger.py - Merge multiple PDF files into a single PDF
"""
import os
import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def merge_pdfs(pdf_paths: list, output_path: str) -> str:
    """
    Merge a list of PDF files into one output PDF.

    Args:
        pdf_paths: Ordered list of absolute paths to input PDFs.
        output_path: Absolute path where the merged PDF will be saved.

    Returns:
        output_path on success.

    Raises:
        FileNotFoundError: If any source PDF does not exist.
        ValueError: If pdf_paths is empty.
    """
    if not pdf_paths:
        raise ValueError("pdf_paths must contain at least one PDF file path.")

    for p in pdf_paths:
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Input PDF not found: {p}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    merged = fitz.open()

    for idx, pdf_path in enumerate(pdf_paths):
        logger.info("Merging PDF %d/%d: %s", idx + 1, len(pdf_paths), os.path.basename(pdf_path))
        try:
            src = fitz.open(pdf_path)
            merged.insert_pdf(src)
            src.close()
        except Exception as exc:
            logger.error("Failed to merge '%s': %s", pdf_path, exc)
            raise

    merged.save(output_path)
    merged.close()

    total_pages = fitz.open(output_path).page_count
    logger.info("Merged %d PDFs → %s  (%d total pages)", len(pdf_paths), output_path, total_pages)
    return output_path


def get_page_count(pdf_path: str) -> int:
    """Return the number of pages in a PDF."""
    with fitz.open(pdf_path) as doc:
        return doc.page_count
