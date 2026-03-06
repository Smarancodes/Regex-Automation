"""
pdf_splitter.py - Split a merged PDF into separate PDFs based on pattern-matched page groups.
"""
import json
import os
import logging
import fitz  # PyMuPDF
from collections import defaultdict

logger = logging.getLogger(__name__)


def build_page_groups(matched_pages: list) -> dict:
    """
    Group page numbers by their matched label.

    Args:
        matched_pages: Output of pattern_matcher.match_all_pages()
                       Each item: {"page": int, "label": str, ...}

    Returns:
        Dict: {"Invoice": [0, 1, 2], "Contract": [5, 6], "Unmatched": [3, 4]}
    """
    groups = defaultdict(list)
    for item in matched_pages:
        groups[item["label"]].append(item["page"])
    return dict(groups)


def split_pdf_by_groups(
    merged_pdf_path: str,
    page_groups: dict,
    output_dir: str,
    base_name: str = "split",
) -> list:
    """
    Write one output PDF per label group.

    Args:
        merged_pdf_path: Path to the merged PDF.
        page_groups:     {"LabelName": [page_indices], ...}
        output_dir:      Directory to write split PDFs.
        base_name:       Prefix for output file names.

    Returns:
        List of {"label": str, "pages": list, "output_file": str}
    """
    os.makedirs(output_dir, exist_ok=True)
    src = fitz.open(merged_pdf_path)
    results = []

    for label, pages in sorted(page_groups.items()):
        if not pages:
            continue

        # Sanitise label for use in filename
        safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
        out_filename = f"{base_name}_{safe_label}.pdf"
        out_path = os.path.join(output_dir, out_filename)

        out_doc = fitz.open()
        for pg in sorted(pages):
            out_doc.insert_pdf(src, from_page=pg, to_page=pg)

        out_doc.save(out_path)
        out_doc.close()

        logger.info(
            "Written split PDF: %s  (%d page%s: %s)",
            out_filename,
            len(pages),
            "s" if len(pages) != 1 else "",
            ", ".join(str(p + 1) for p in sorted(pages)),
        )
        results.append({"label": label, "pages": pages, "output_file": out_path})

    src.close()
    return results


def write_json_by_groups(
    matched_pages: list,
    page_groups: dict,
    json_dir: str,
    base_name: str = "split",
) -> list:
    """
    Write one output JSON per label group containing the text of its pages.
    """
    os.makedirs(json_dir, exist_ok=True)
    results = []

    # create a lookup of page -> text
    page_text_map = {item["page"]: item["text"] for item in matched_pages}

    for label, pages in sorted(page_groups.items()):
        if not pages:
            continue

        safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
        out_filename = f"{base_name}_{safe_label}.json"
        out_path = os.path.join(json_dir, out_filename)

        group_data = {
            "label": label,
            "pages": []
        }
        
        for pg in sorted(pages):
            group_data["pages"].append({
                "page": pg,
                "text": page_text_map.get(pg, "")
            })

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(group_data, f, indent=2, ensure_ascii=False)

        logger.info("Written split JSON: %s", out_filename)
        results.append(out_path)

    return results
