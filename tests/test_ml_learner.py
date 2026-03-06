# -*- coding: utf-8 -*-
"""
test_ml_learner.py
==================
Automated test for the ML pattern learning module.
"""

import os
import re
import sys
import tempfile
import shutil

import fitz  # PyMuPDF

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.ml_pattern_learner import learn_patterns

def _create_synthetic_pdf(path: str, header_text: str, num_pages: int = 3):
    doc = fitz.open()
    for _ in range(num_pages):
        page = doc.new_page(width=595, height=842)
        # Put text near the top (header zone)
        page.insert_text((50, 50), header_text, fontsize=12)
    doc.save(path)
    doc.close()

def test_learner():
    tmp_dir = tempfile.mkdtemp(prefix="ml_test_")
    
    try:
        print("Creating synthetic PDFs ...")
        # Cluster 1: Invoices
        pdf1 = os.path.join(tmp_dir, "invoice_1.pdf")
        pdf2 = os.path.join(tmp_dir, "invoice_2.pdf")
        _create_synthetic_pdf(pdf1, "INVOICE NUMBER: 1001\nDate: Jan 1")
        _create_synthetic_pdf(pdf2, "INVOICE\nBill To: John Doe")
        
        # Cluster 2: Contracts
        pdf3 = os.path.join(tmp_dir, "contract_1.pdf")
        pdf4 = os.path.join(tmp_dir, "contract_2.pdf")
        _create_synthetic_pdf(pdf3, "EMPLOYMENT CONTRACT\nTerms and Conditions")
        _create_synthetic_pdf(pdf4, "AGREEMENT OF CONTRACT\nConfidentiality terms")
        
        input_pdfs = [pdf1, pdf2, pdf3, pdf4]
        
        print(f"Running ML pattern learner on {len(input_pdfs)} PDFs ...")
        # Enforce 2 clusters for determinism in the test
        patterns = learn_patterns(input_pdfs, n_clusters=2)
        
        print("\nValidating results...")
        assert len(patterns) == 2, f"Expected 2 patterns, got {len(patterns)}"
        
        found_invoice_regex = False
        found_contract_regex = False
        
        for p in patterns:
            # Check compilation
            compiled = re.compile(p["regex"])
            
            # Check which topic it matched
            if compiled.search("Invoice"):
                found_invoice_regex = True
            if compiled.search("Contract"):
                found_contract_regex = True
                
        assert found_invoice_regex, "Failed to generate regex covering 'invoice'"
        assert found_contract_regex, "Failed to generate regex covering 'contract'"
        
        print("\nALL TESTS PASSED: ML learner correctly generated compilable, accurate regexes.")
        return 0
        
    except AssertionError as e:
        print(f"\n[FAIL] Assertion error: {e}")
        return 1
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

if __name__ == "__main__":
    sys.exit(test_learner())
