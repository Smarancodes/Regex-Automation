"""
download_real_pdfs.py - Downloads 2 real multi-page PDFs from the internet
and places them in input_pdfs/ for testing.

Run: venv\Scripts\python download_real_pdfs.py
"""
import urllib.request
import os
import sys

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_pdfs")
os.makedirs(OUTPUT, exist_ok=True)

PDFS = [
    {
        "url": "https://www.w3.org/WAI/WCAG21/Techniques/pdf/pdf-notes.pdf",
        "filename": "real_doc1_w3c.pdf",
        "desc": "W3C PDF Accessibility Guide (multi-page real document)"
    },
    {
        "url": "https://www.africau.edu/images/default/sample.pdf",
        "filename": "real_doc2_sample.pdf",
        "desc": "Standard multi-page sample PDF"
    },
]

print("\nDownloading real PDFs...\n")

headers = {"User-Agent": "Mozilla/5.0"}

for pdf in PDFS:
    dest = os.path.join(OUTPUT, pdf["filename"])
    print(f"  Downloading: {pdf['desc']}")
    print(f"  From: {pdf['url']}")
    try:
        req = urllib.request.Request(pdf["url"], headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        size_kb = os.path.getsize(dest) // 1024
        print(f"  Saved to: {dest}  ({size_kb} KB)\n")
    except Exception as e:
        print(f"  FAILED: {e}\n")
        print(f"  --> Manually download any PDF and place it in input_pdfs\\")

print("Done! Now run:  venv\\Scripts\\python src\\pipeline.py\n")
