"""
header_footer_extractor.py
==========================
Extract text from the HEADER zone (top 15 % of a page) and
FOOTER zone (bottom 15 % of a page) for every page in one or
more PDF files.

Uses PyMuPDF block-level geometry — no additional pip packages
beyond what is already in Requirements.txt.

Public API
----------
extract_zones(pdf_paths)  ->  list of dicts
    [
        {
            "source":  "invoice.pdf",
            "page":    0,           # 0-indexed
            "header":  "INVOICE NO. 1234 | Date: 01-Jan-2024",
            "footer":  "Page 1 of 3  |  Acme Corp Confidential",
        },
        ...
    ]
"""

import logging
import os
import re
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Fraction of page height considered "header" / "footer" zone
HEADER_FRACTION = 0.15
FOOTER_FRACTION = 0.15

# Minimum characters needed for a zone to be considered non-empty
MIN_ZONE_CHARS = 3


def _clean(text: str) -> str:
    """Collapse whitespace and strip control characters."""
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _extract_page_zones(page: fitz.Page) -> tuple[str, str]:
    """
    Return (header_text, footer_text) for a single fitz.Page.

    Strategy:
        1. Get all text blocks with their bounding boxes.
        2. Any block whose TOP edge is within the top HEADER_FRACTION of the
           page is considered header text.
        3. Any block whose BOTTOM edge is within the bottom FOOTER_FRACTION of
           the page is considered footer text.
    """
    page_height = page.rect.height
    header_max_y = page_height * HEADER_FRACTION
    footer_min_y = page_height * (1.0 - FOOTER_FRACTION)

    header_parts = []
    footer_parts = []

    # blocks → list of (x0, y0, x1, y1, "text", block_no, block_type)
    blocks = page.get_text("blocks")
    for block in blocks:
        x0, y0, x1, y1, block_text, *_ = block
        block_text = _clean(block_text)
        if not block_text:
            continue

        if y0 <= header_max_y:
            header_parts.append(block_text)
        if y1 >= footer_min_y:
            footer_parts.append(block_text)

    return " ".join(header_parts), " ".join(footer_parts)


def extract_zones(pdf_paths: list[str]) -> list[dict]:
    """
    Extract header and footer text zones from every page of every PDF.

    Parameters
    ----------
    pdf_paths : list of str
        Absolute or relative paths to PDF files.

    Returns
    -------
    list of dict
        Each dict:  {"source", "page", "header", "footer"}
    """
    results = []

    for pdf_path in pdf_paths:
        if not os.path.isfile(pdf_path):
            logger.warning("PDF not found, skipping: %s", pdf_path)
            continue

        source_name = os.path.basename(pdf_path)
        logger.info("Extracting header/footer zones from: %s", source_name)

        try:
            doc = fitz.open(pdf_path)
        except Exception as exc:
            logger.error("Cannot open PDF %s: %s", pdf_path, exc)
            continue

        with doc:
            page_count = len(doc)
            for page_num in range(page_count):
                page = doc[page_num]
                header, footer = _extract_page_zones(page)

                # Skip completely blank zones
                has_content = (
                    len(header) >= MIN_ZONE_CHARS or len(footer) >= MIN_ZONE_CHARS
                )
                if not has_content:
                    logger.debug(
                        "  %s page %d — no usable header/footer text, skipping",
                        source_name, page_num + 1,
                    )

                results.append(
                    {
                        "source": source_name,
                        "page": page_num,
                        "header": header,
                        "footer": footer,
                    }
                )

                logger.debug(
                    "  %s page %3d | header=%d chars | footer=%d chars",
                    source_name, page_num + 1, len(header), len(footer),
                )

        logger.info(
            "  Done — %d page(s) processed from %s", page_count, source_name
        )

    logger.info("Total zones extracted: %d", len(results))
    return results


# ── Quick self-test when run directly ────────────────────────────────────────
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)-7s │ %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python src/header_footer_extractor.py <file1.pdf> [file2.pdf ...]")
        sys.exit(1)

    zones = extract_zones(sys.argv[1:])
    print(f"\n{'PDF':<30} {'Page':>4}  │  {'HEADER':<50}  │  FOOTER")
    print("─" * 110)
    for z in zones:
        h = (z["header"] or "(empty)")[:50]
        f = (z["footer"] or "(empty)")[:40]
        print(f"  {z['source']:<28} {z['page']+1:>4}  │  {h:<50}  │  {f}")
