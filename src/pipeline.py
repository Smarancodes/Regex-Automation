"""
pipeline.py - End-to-end orchestrator for the PDF Regex Automation pipeline.

Usage:
    python src/pipeline.py
    python src/pipeline.py --inputs doc1.pdf doc2.pdf --patterns config/patterns.json
    python src/pipeline.py --dpi 200 --lang eng
"""
import argparse
import logging
import os
import sys
import time
import shutil
import io

# Force UTF-8 on Windows console to avoid cp1252 errors
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── Bootstrap path so we can import siblings ──────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from config.config import (
    INPUT_DIR, OUTPUT_DIR, JSON_DIR, TEMP_DIR, PATTERNS_FILE, MERGED_PDF,
    RASTER_DPI, TESSERACT_LANG, NATIVE_TEXT_MIN_CHARS, LOG_LEVEL,
)
from src.pdf_merger import merge_pdfs, get_page_count
from src.image_to_text import extract_text
from src.pattern_matcher import load_patterns, match_all_pages
from src.pdf_splitter import build_page_groups, split_pdf_by_groups, write_json_by_groups


# ── Logging setup ─────────────────────────────────────────────────────────────
def setup_logging(level_str: str):
    level = getattr(logging, level_str.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
        datefmt="%H:%M:%S",
    )


# ── Helpers ───────────────────────────────────────────────────────────────────
def _separator(char="─", width=60):
    print(char * width)


def _print_summary(matched_pages: list, split_results: list):
    _separator("═")
    print("  PIPELINE RESULTS")
    _separator("═")

    # Per-page table
    print(f"  {'Page':>4}  │  {'Method':<12}  │  Label")
    _separator()
    for item in matched_pages:
        print(f"  {item['page'] + 1:>4}  │  {item['method']:<12}  │  {item['label']}")

    _separator()
    print("\n  OUTPUT FILES:")
    for sr in split_results:
        pages_str = ", ".join(str(p + 1) for p in sorted(sr["pages"]))
        print(f"  [{sr['label']}]  →  {os.path.basename(sr['output_file'])}  (pages: {pages_str})")
    _separator("═")


# ── Main pipeline ─────────────────────────────────────────────────────────────
def run_pipeline(
    input_paths: list,
    patterns_file: str,
    output_dir: str,
    json_dir: str,
    temp_dir: str,
    merged_pdf: str,
    dpi: int,
    lang: str,
    native_min_chars: int,
):
    start = time.time()
    logger = logging.getLogger("pipeline")

    # ── STAGE 1: Merge ─────────────────────────────────────────────────────
    _separator("═")
    print("  STAGE 1 │ Merging PDFs")
    _separator("═")
    os.makedirs(temp_dir, exist_ok=True)
    merged_path = merge_pdfs(input_paths, merged_pdf)
    total_pages = get_page_count(merged_path)
    print(f"  ✓ Merged {len(input_paths)} PDF(s) → {total_pages} pages total\n")

    # ── STAGE 2: Extract text from each page ───────────────────────────────
    _separator("═")
    print("  STAGE 2 │ Extracting Text")
    _separator("═")
    page_texts = []
    for pg in range(total_pages):
        result = extract_text(
            merged_path, pg,
            dpi=dpi,
            lang=lang,
            native_min_chars=native_min_chars,
        )
        print(f"  Page {pg + 1:>3}/{total_pages} | {result['method']:<16} | {len(result['text'])} chars")
        page_texts.append(result)
    print()

    # ── STAGE 3: Pattern matching ──────────────────────────────────────────
    _separator("═")
    print("  STAGE 3 │ Pattern Matching")
    _separator("═")
    patterns = load_patterns(patterns_file)
    matched_pages = match_all_pages(page_texts, patterns)
    print()

    # ── STAGE 4: Split PDF ─────────────────────────────────────────────────
    _separator("═")
    print("  STAGE 4 │ Splitting PDF and JSON")
    _separator("═")
    page_groups = build_page_groups(matched_pages)
    split_results = split_pdf_by_groups(merged_path, page_groups, output_dir)
    json_results = write_json_by_groups(matched_pages, page_groups, json_dir)
    print()

    # ── Summary ────────────────────────────────────────────────────────────
    _print_summary(matched_pages, split_results)

    elapsed = time.time() - start
    print(f"\n  Completed in {elapsed:.1f}s")
    return split_results


# ── CLI entrypoint ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="PDF Regex Automation Pipeline — merge, OCR, match, split"
    )
    parser.add_argument(
        "--inputs", nargs="+", metavar="PDF",
        help="Input PDF paths (default: all .pdf files in input_pdfs/ folder)"
    )
    parser.add_argument(
        "--patterns", default=PATTERNS_FILE, metavar="JSON",
        help=f"Regex patterns JSON file (default: {PATTERNS_FILE})"
    )
    parser.add_argument(
        "--output", default=OUTPUT_DIR, metavar="DIR",
        help=f"Output directory for split PDFs (default: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--json-output", default=JSON_DIR, metavar="DIR",
        help=f"Output directory for split JSON data (default: {JSON_DIR})"
    )
    parser.add_argument(
        "--dpi", type=int, default=RASTER_DPI,
        help=f"DPI for OCR rasterisation (default: {RASTER_DPI})"
    )
    parser.add_argument(
        "--lang", default=TESSERACT_LANG,
        help=f"Tesseract language(s) e.g. eng, eng+hin (default: {TESSERACT_LANG})"
    )
    parser.add_argument("--log", default=LOG_LEVEL, help="Log level: DEBUG/INFO/WARNING")
    parser.add_argument(
        "--clean-temp", action="store_true",
        help="Delete temp_images/ folder after processing"
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="Clear input_pdfs/ and output_pdfs/ before processing (fresh run)"
    )
    args = parser.parse_args()

    setup_logging(args.log)

    # ── --clean: wipe input and output folders before run ─────────────────────
    if args.clean:
        print("--clean flag detected.")
        confirm = input("  This will DELETE all files in input_pdfs\\, output_pdfs\\ and output_json\\. Continue? (y/n): ").strip().lower()
        if confirm == "y":
            for folder in [INPUT_DIR, OUTPUT_DIR, JSON_DIR]:
                if not os.path.exists(folder):
                    continue
                for fname in os.listdir(folder):
                    fpath = os.path.join(folder, fname)
                    if os.path.isfile(fpath):
                        os.remove(fpath)
            print("  Cleared input_pdfs\\, output_pdfs\\, and output_json\\.")
            print("  Now drop your new PDFs into input_pdfs\\ and re-run WITHOUT --clean.\n")
            sys.exit(0)
        else:
            print("  Clean cancelled. Proceeding with existing files.\n")

    # Resolve input PDFs
    if args.inputs:
        input_paths = [os.path.abspath(p) for p in args.inputs]
    else:
        # Auto-discover from input_pdfs/ folder
        pdfs = sorted(
            f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")
        )
        if not pdfs:
            print(f"ERROR: No PDFs found in '{INPUT_DIR}'. "
                  f"Drop your PDF files there or use --inputs.")
            sys.exit(1)
        input_paths = [os.path.join(INPUT_DIR, p) for p in pdfs]
        print(f"Auto-discovered {len(input_paths)} PDF(s): {[os.path.basename(p) for p in input_paths]}\n")

    split_results = run_pipeline(
        input_paths=input_paths,
        patterns_file=args.patterns,
        output_dir=args.output,
        json_dir=args.json_output,
        temp_dir=TEMP_DIR,
        merged_pdf=MERGED_PDF,
        dpi=args.dpi,
        lang=args.lang,
        native_min_chars=NATIVE_TEXT_MIN_CHARS,
    )

    if args.clean_temp and os.path.isdir(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        print("  Temp images cleaned up.")

    print(f"\n  Output PDFs are in:  {args.output}")
    print(f"  Output JSON is in: {args.json_output}\n")
    return 0 if split_results else 1


if __name__ == "__main__":
    sys.exit(main())
