"""
verify_accuracy.py - Re-reads every output PDF and verifies that each page
actually contains text matching the label it was assigned to.

Gives a per-label and overall accuracy score.

Run: venv\Scripts\python verify_accuracy.py
"""
import os, sys, json, re
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_pdfs")
INPUT_DIR  = os.path.join(BASE_DIR, "input_pdfs")
PATTERNS_F = os.path.join(BASE_DIR, "config", "patterns.json")

sys.path.insert(0, BASE_DIR)
import fitz

# ── Load patterns ─────────────────────────────────────────────────────────────
with open(PATTERNS_F, encoding="utf-8") as f:
    data = json.load(f)

patterns = []
for p in data["patterns"]:
    patterns.append({"name": p["name"], "compiled": re.compile(p["regex"])})

def match_text(text):
    for p in patterns:
        if p["compiled"].search(text):
            return p["name"]
    return "Unmatched"

# ── Check input_pdfs ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  INPUT PDF SUMMARY")
print("=" * 60)
input_pdfs = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
if not input_pdfs:
    print("  No PDFs in input_pdfs/")
else:
    total_input_pages = 0
    for fname in sorted(input_pdfs):
        path = os.path.join(INPUT_DIR, fname)
        doc  = fitz.open(path)
        pages = doc.page_count
        size  = os.path.getsize(path) // 1024
        total_input_pages += pages
        print(f"  {fname:<40} {pages:>3} pages  ({size} KB)")
        doc.close()
    print(f"\n  Total: {len(input_pdfs)} PDF(s), {total_input_pages} pages")

# ── Check output_pdfs and verify accuracy ────────────────────────────────────
print("\n" + "=" * 60)
print("  OUTPUT ACCURACY VERIFICATION")
print("=" * 60)

output_pdfs = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith(".pdf")]
if not output_pdfs:
    print("  No PDFs in output_pdfs/ — run the pipeline first.")
    sys.exit(1)

total_pages  = 0
correct      = 0
wrong_pages  = []

for fname in sorted(output_pdfs):
    # Extract label from filename: split_Invoice.pdf -> Invoice
    label = fname.replace("split_", "").replace(".pdf", "")
    path  = os.path.join(OUTPUT_DIR, fname)
    doc   = fitz.open(path)
    file_correct = 0
    file_total   = doc.page_count

    for pg_num in range(file_total):
        page = doc[pg_num]
        text = page.get_text("text").strip()
        detected = match_text(text)

        if label == "Unmatched":
            # Unmatched pages should NOT match any pattern
            is_correct = (detected == "Unmatched")
        else:
            is_correct = (detected == label)

        if is_correct:
            file_correct += 1
            correct += 1
        else:
            wrong_pages.append({
                "file": fname,
                "page": pg_num + 1,
                "expected": label,
                "detected": detected,
                "preview": text[:80].replace("\n", " ")
            })
        total_pages += 1

    acc = (file_correct / file_total * 100) if file_total else 0
    status = "PASS" if file_correct == file_total else f"WARN ({file_total - file_correct} mismatch)"
    print(f"  {fname:<38}  {file_correct}/{file_total} pages  {acc:5.1f}%  [{status}]")
    doc.close()

# ── Summary ───────────────────────────────────────────────────────────────────
overall = (correct / total_pages * 100) if total_pages else 0
print("\n" + "=" * 60)
print(f"  OVERALL ACCURACY: {correct}/{total_pages} pages correct  =  {overall:.1f}%")
print("=" * 60)

if wrong_pages:
    print("\n  MISMATCHED PAGES:")
    for w in wrong_pages:
        print(f"    {w['file']}  pg{w['page']}  expected={w['expected']}  detected={w['detected']}")
        print(f"    Text: \"{w['preview']}\"")
else:
    print("\n  All pages match their assigned labels perfectly.")

print()
