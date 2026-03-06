"""
train.py
========
CLI entrypoint to learn regex patterns from a batch of PDFs.

Usage:
    python train.py
        -> Auto-discovers PDFs in input_pdfs/ and runs learning
        
    python train.py --inputs path/to/pdf1.pdf path/to/pdf2.pdf
    python train.py --clusters 5
"""

import argparse
import logging
import os
import sys

from config.config import INPUT_DIR, PATTERNS_FILE
from src.ml_pattern_learner import learn_patterns, save_patterns

def main():
    parser = argparse.ArgumentParser(
        description="Learn regex patterns from PDF headers and footers."
    )
    parser.add_argument(
        "--inputs", nargs="+", metavar="PDF",
        help="Input PDF paths (default: all .pdf files in input_pdfs/ folder)"
    )
    parser.add_argument(
        "--clusters", type=int, default=None,
        help="Number of document types to discover (default: auto via elbow method)"
    )
    parser.add_argument(
        "--output", default=PATTERNS_FILE, metavar="JSON",
        help=f"Where to save the patterns (default: {PATTERNS_FILE})"
    )
    parser.add_argument("--log", default="INFO", help="Log level: DEBUG/INFO/WARNING")
    
    args = parser.parse_args()

    level = getattr(logging, args.log.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s │ %(levelname)-7s │ %(message)s", datefmt="%H:%M:%S")

    if args.inputs:
        input_paths = [os.path.abspath(p) for p in args.inputs]
    else:
        if not os.path.isdir(INPUT_DIR):
            print(f"ERROR: Input directory not found: {INPUT_DIR}")
            sys.exit(1)
            
        pdfs = sorted(f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf"))
        if not pdfs:
            print(f"ERROR: No PDFs found in '{INPUT_DIR}'. Drop files there or use --inputs.")
            sys.exit(1)
        input_paths = [os.path.join(INPUT_DIR, p) for p in pdfs]

    print("=" * 60)
    print("  ML REGEX PATTERN LEARNER")
    print("=" * 60)
    print(f"  Analysing {len(input_paths)} PDF(s) ...\n")
    
    try:
        patterns = learn_patterns(input_paths, n_clusters=args.clusters)
        
        print("\n" + "=" * 60)
        print("  LEARNED PATTERNS")
        print("=" * 60)
        for p in patterns:
            print(f"  {p['name']:15s}  ->  {p['regex']}")
        print()
        
        save_patterns(patterns, args.output)
        print(f"\n  Successfully generated and saved patterns to: {args.output}")
        print("  Tip: You can rename 'DocType_N' to meaningful names (e.g. 'Invoice')")
        print("  in the JSON file before running the main pipeline.\n")
        
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
