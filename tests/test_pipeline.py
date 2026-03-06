# -*- coding: utf-8 -*-
"""
test_pipeline.py - Automated end-to-end test for the PDF Regex Automation pipeline.

Generates its own test PDFs with known content, runs the full pipeline,
and verifies outputs, so you don't need any external PDFs to validate the setup.

Run:
    venv\\Scripts\\python tests/test_pipeline.py
"""
import os
import sys
import shutil
import tempfile
import io

# Force UTF-8 output on Windows so Unicode chars print safely
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import fitz  # PyMuPDF
from src.pipeline import run_pipeline
from config.config import TEMP_DIR
import json

# ── Test PDF generation ───────────────────────────────────────────────────────

PAGE_CONTENTS = [
    # (text_on_page, expected_label)
    ("INVOICE NO. 12345\nDate: 01-Jan-2024\nBill To: ABC Corp", "Invoice"),
    ("INVOICE NO. 12346\nDate: 02-Jan-2024\nService Rendered: Consulting", "Invoice"),
    ("PURCHASE ORDER No. 98765\nVendor: XYZ Ltd\nAmount: 50000", "Purchase_Order"),
    ("PURCHASE ORDER #98766\nDelivery Date: 15-Jan-2024", "Purchase_Order"),
    ("AGREEMENT\nThis contract is entered into between Party A and Party B.", "Contract"),
    ("RECEIPT\nPayment Received from ABC Corp\nAmount: INR 25,000", "Receipt"),
    ("REPORT\nQuarterly Sales Analysis\nSummary of Findings for Q4", "Report"),
    ("General document page with no specific keywords.", "Unmatched"),
    ("Another invoice page. Invoice # 99999 for services.", "Invoice"),
    ("Random administrative content. No matching pattern here.", "Unmatched"),
]


def _make_test_pdf(path: str, pages: list):
    """Create a PDF where each page contains the given text."""
    doc = fitz.open()
    for text, _ in pages:
        page = doc.new_page(width=595, height=842)  # A4
        page.insert_text((50, 100), text, fontsize=14)
    doc.save(path)
    doc.close()


def _run_tests():
    print("=" * 60)
    print("  PDF REGEX AUTOMATION - AUTOMATED TEST SUITE")
    print("=" * 60)

    tmp_dir = tempfile.mkdtemp(prefix="regex_auto_test_")
    try:
        # Split pages into two PDFs (simulating user's 2-input scenario)
        pdf1_pages = PAGE_CONTENTS[:5]
        pdf2_pages = PAGE_CONTENTS[5:]

        pdf1_path = os.path.join(tmp_dir, "test_doc1.pdf")
        pdf2_path = os.path.join(tmp_dir, "test_doc2.pdf")
        _make_test_pdf(pdf1_path, pdf1_pages)
        _make_test_pdf(pdf2_path, pdf2_pages)
        print(f"\n  [OK] Created test PDF 1: {len(pdf1_pages)} pages")
        print(f"  [OK] Created test PDF 2: {len(pdf2_pages)} pages")

        out_dir    = os.path.join(tmp_dir, "output")
        json_dir   = os.path.join(tmp_dir, "json_output")
        merged_pdf = os.path.join(tmp_dir, "merged.pdf")
        patterns_json = os.path.join(tmp_dir, "patterns.json")
        
        # Write test patterns
        test_patterns = {
            "patterns": [
                {"name": "Invoice", "regex": "(?i)invoice"},
                {"name": "Purchase_Order", "regex": "(?i)purchase\\s*order"},
                {"name": "Contract", "regex": "(?i)contract|agreement"},
                {"name": "Receipt", "regex": "(?i)receipt"},
                {"name": "Report", "regex": "(?i)report"}
            ]
        }
        with open(patterns_json, 'w') as f:
            json.dump(test_patterns, f)

        print("\n  Running full pipeline ...\n")
        split_results = run_pipeline(
            input_paths=[pdf1_path, pdf2_path],
            patterns_file=patterns_json,
            output_dir=out_dir,
            json_dir=json_dir,
            temp_dir=TEMP_DIR,
            merged_pdf=merged_pdf,
            dpi=72,        # Fast DPI for test; native text will be used anyway
            lang="eng",
            native_min_chars=10,
        )

        # ── Assertions ────────────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  ASSERTIONS")
        print("=" * 60)

        expected_groups = {}
        for idx, (_, label) in enumerate(PAGE_CONTENTS):
            expected_groups.setdefault(label, []).append(idx)

        passes = 0
        failures = 0

        result_map = {sr["label"]: sr for sr in split_results}

        for label, expected_pages in sorted(expected_groups.items()):
            safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
            if safe_label in result_map:
                actual_pages = sorted(result_map[safe_label]["pages"])
                expected_sorted = sorted(expected_pages)
                if actual_pages == expected_sorted:
                    print(f"  PASS: {label:15s}  pages={[p+1 for p in actual_pages]}")
                    passes += 1
                else:
                    print(f"  FAIL: {label:15s}  expected pages {[p+1 for p in expected_sorted]}, "
                          f"got {[p+1 for p in actual_pages]}")
                    failures += 1
            else:
                print(f"  FAIL: {label:15s}  --- no output PDF generated")
                failures += 1

        # Check output files exist
        for sr in split_results:
            fname = os.path.basename(sr["output_file"])
            if os.path.isfile(sr["output_file"]):
                print(f"  PASS: File exists -> {fname}")
                passes += 1
            else:
                print(f"  FAIL: File missing -> {fname}")
                failures += 1
                
            # Check JSON counterparts exist
            json_fname = fname.replace(".pdf", ".json")
            json_path = os.path.join(json_dir, json_fname)
            if os.path.isfile(json_path):
                print(f"  PASS: JSON exists -> {json_fname}")
                passes += 1
            else:
                print(f"  FAIL: JSON missing -> {json_fname}")
                failures += 1

        print("\n" + "=" * 60)
        print(f"  Results: {passes} passed, {failures} failed")
        print("=" * 60)

        if failures == 0:
            print("\n  *** ALL TESTS PASSED - Pipeline is working correctly! ***\n")
        else:
            print("\n  !!! SOME TESTS FAILED - Check output above for details. !!!\n")
        return failures

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(_run_tests())
