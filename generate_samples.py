"""
generate_samples.py - Creates 2 realistic 10-page sample PDFs for testing.
Run: venv\Scripts\python generate_samples.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_pdfs")
os.makedirs(OUTPUT, exist_ok=True)

# ── Document 1: 10 pages ──────────────────────────────────────────────────────
DOC1_PAGES = [
    ("INVOICE NO. 1001\n\n"
     "Date: 01-March-2024\n"
     "Vendor: Mphasis Supplies Pvt Ltd\n"
     "Bill To: ABC Technologies Ltd\n\n"
     "Description        Qty   Rate     Amount\n"
     "Software Licenses   10   5000    50,000\n"
     "Annual Support       1  10000    10,000\n\n"
     "Total Amount: INR 60,000\n"
     "Payment Due: 31-March-2024"),

    ("INVOICE NO. 1002\n\n"
     "Date: 02-March-2024\n"
     "Vendor: Mphasis Supplies Pvt Ltd\n"
     "Bill To: XYZ Enterprises\n\n"
     "Description        Qty   Rate     Amount\n"
     "Consulting Hours    40   2500   1,00,000\n"
     "Travel Expenses      1   5000     5,000\n\n"
     "Total Amount: INR 1,05,000\n"
     "Payment Due: 15-April-2024"),

    ("PURCHASE ORDER No. 5001\n\n"
     "Date: 05-March-2024\n"
     "PO Raised By: ABC Technologies Ltd\n"
     "Vendor: Mphasis Supplies Pvt Ltd\n\n"
     "Item Description       Qty   Unit Price   Total\n"
     "Office Laptops          10       45,000   4,50,000\n"
     "Wireless Mouse          10          800       8,000\n\n"
     "Total PO Value: INR 4,58,000\n"
     "Delivery Date: 20-March-2024"),

    ("PURCHASE ORDER No. 5002\n\n"
     "Date: 06-March-2024\n"
     "PO Raised By: ABC Technologies Ltd\n"
     "Vendor: Office World\n\n"
     "Item Description       Qty   Unit Price   Total\n"
     "Office Chairs           20        3500    70,000\n"
     "Office Desks            10        8000    80,000\n\n"
     "Total PO Value: INR 1,50,000\n"
     "Delivery Date: 25-March-2024"),

    ("SERVICE AGREEMENT\n\n"
     "This Agreement is entered into on 01-March-2024\n"
     "Between: Mphasis Limited (Service Provider)\n"
     "And: ABC Technologies Ltd (Client)\n\n"
     "Scope of Work:\n"
     "The Service Provider agrees to provide IT consulting\n"
     "and software development services for a period of\n"
     "12 months from the date of signing.\n\n"
     "Contract Value: INR 50,00,000\n"
     "Payment Terms: Monthly - INR 4,16,667"),

    ("RECEIPT\n\n"
     "Receipt No. R-2024-001\n"
     "Date: 10-March-2024\n\n"
     "Payment Received From: ABC Technologies Ltd\n"
     "Amount: INR 60,000\n"
     "Against Invoice No.: 1001\n"
     "Mode of Payment: NEFT\n"
     "Transaction Ref: NEFT20240310001\n\n"
     "Amount Received by: Mphasis Finance Dept.\n"
     "Status: PAID IN FULL"),

    ("INVOICE NO. 1003\n\n"
     "Date: 12-March-2024\n"
     "Vendor: Mphasis Supplies Pvt Ltd\n"
     "Bill To: Delta Corp\n\n"
     "Description        Qty   Rate     Amount\n"
     "Cloud Storage (GB) 500     20    10,000\n"
     "Setup Fee            1   5000     5,000\n\n"
     "Total Amount: INR 15,000\n"
     "Payment Due: 30-March-2024"),

    ("QUARTERLY REPORT - Q4 2023\n\n"
     "Period: October 2023 - December 2023\n"
     "Prepared By: Mphasis Analytics Team\n\n"
     "Summary of Findings:\n"
     "Total Revenue:    INR 12,50,00,000\n"
     "Total Expenses:   INR  9,80,00,000\n"
     "Net Profit:       INR  2,70,00,000\n\n"
     "Key Analysis:\n"
     "- Revenue grew 18% compared to Q3\n"
     "- Operating costs reduced by 5%\n"
     "- New client acquisitions: 12"),

    ("PURCHASE ORDER #5003\n\n"
     "Date: 14-March-2024\n"
     "PO Raised By: Delta Corp\n"
     "Vendor: Tech Parts Ltd\n\n"
     "Item Description         Qty   Unit Price   Total\n"
     "Server RAM (32GB)          8       12,000    96,000\n"
     "SSD 1TB                    8        6,500    52,000\n\n"
     "Total PO Value: INR 1,48,000\n"
     "Delivery Date: 22-March-2024"),

    ("GENERAL CORRESPONDENCE\n\n"
     "Date: 15-March-2024\n"
     "To: HR Department\n"
     "From: Administration\n\n"
     "Subject: Office Relocation Notice\n\n"
     "This is to inform all employees that our office\n"
     "will be relocating to the new premises at\n"
     "Tower B, Mindspace Business Park, Hyderabad\n"
     "from 01-April-2024.\n\n"
     "Kindly plan your commute accordingly."),
]

# ── Document 2: 10 pages ──────────────────────────────────────────────────────
DOC2_PAGES = [
    ("INVOICE NO. 2001\n\n"
     "Date: 16-March-2024\n"
     "Vendor: CloudNet Solutions\n"
     "Bill To: Mphasis Limited\n\n"
     "Description             Qty   Rate      Amount\n"
     "Cloud Hosting (monthly)   1  25,000    25,000\n"
     "Data Backup Service       1   8,000     8,000\n\n"
     "Total Amount: INR 33,000\n"
     "Payment Due: 31-March-2024"),

    ("CONTRACT AGREEMENT\n\n"
     "This Contract is made on 17-March-2024\n"
     "Between: Mphasis Limited\n"
     "And: CloudNet Solutions\n\n"
     "Terms and Conditions:\n"
     "1. Services will be provided for 24 months\n"
     "2. SLA uptime guarantee: 99.9%\n"
     "3. Payment: Quarterly in advance\n\n"
     "Total Contract Value: INR 7,92,000\n"
     "Effective Date: 01-April-2024"),

    ("RECEIPT\n\n"
     "Receipt No. R-2024-002\n"
     "Date: 18-March-2024\n\n"
     "Payment Received From: Mphasis Limited\n"
     "Amount: INR 1,05,000\n"
     "Against Invoice No.: 1002\n"
     "Mode of Payment: RTGS\n"
     "Transaction Ref: RTGS20240318047\n\n"
     "Authorized by: Accounts Department\n"
     "Status: PAYMENT RECEIVED IN FULL"),

    ("ANNUAL REPORT - FY 2023-24\n\n"
     "Company: Mphasis Limited\n"
     "Financial Year: April 2023 - March 2024\n\n"
     "Summary of Findings:\n"
     "Gross Revenue:    INR 52,00,00,000\n"
     "EBITDA:           INR 11,44,00,000\n"
     "PAT:              INR  8,32,00,000\n"
     "EPS:              INR 44.5\n\n"
     "Analysis: Strong growth across all segments.\n"
     "Cloud and digital services up 32% YoY."),

    ("PURCHASE ORDER No. 6001\n\n"
     "Date: 19-March-2024\n"
     "PO Raised By: Mphasis Limited\n"
     "Vendor: Stationery World\n\n"
     "Item Description    Qty   Unit Price   Total\n"
     "A4 Paper Reams      100          350    35,000\n"
     "Pens (Box)           50          120     6,000\n"
     "Notebooks           100          80      8,000\n\n"
     "Total PO Value: INR 49,000\n"
     "Delivery Date: 26-March-2024"),

    ("INVOICE NO. 2002\n\n"
     "Date: 20-March-2024\n"
     "Vendor: Print & Pack Ltd\n"
     "Bill To: Mphasis Limited\n\n"
     "Description          Qty   Rate      Amount\n"
     "Annual Report Print  500    150     75,000\n"
     "Binding & Packing    500     30     15,000\n\n"
     "Total Amount: INR 90,000\n"
     "Payment Due: 05-April-2024"),

    ("SERVICE AGREEMENT\n\n"
     "This Agreement is entered into on 20-March-2024\n"
     "Between: SecureIT Pvt Ltd (Service Provider)\n"
     "And: Mphasis Limited (Client)\n\n"
     "Scope: Cybersecurity audit and penetration testing\n"
     "for all internal systems and web applications.\n\n"
     "Terms and conditions of this contract require\n"
     "strict confidentiality from both parties.\n\n"
     "Contract Value: INR 12,00,000\n"
     "Duration: 6 months"),

    ("RECEIPT\n\n"
     "Receipt No. R-2024-003\n"
     "Date: 22-March-2024\n\n"
     "Payment Received From: Delta Corp\n"
     "Amount: INR 15,000\n"
     "Against Invoice No.: 1003\n"
     "Mode of Payment: UPI\n"
     "Transaction Ref: UPI20240322112\n\n"
     "Received by: Mphasis Accounts\n"
     "Status: PAYMENT RECEIVED"),

    ("INVOICE NO. 2003\n\n"
     "Date: 25-March-2024\n"
     "Vendor: Mphasis Supplies Pvt Ltd\n"
     "Bill To: GreenTech Industries\n\n"
     "Description          Qty   Rate      Amount\n"
     "IT Support (hours)   80    1500    1,20,000\n"
     "Hardware Maintenance  1   25000      25,000\n\n"
     "Total Amount: INR 1,45,000\n"
     "Payment Due: 30-April-2024"),

    ("INTERNAL MEMO\n\n"
     "Date: 28-March-2024\n"
     "To: All Department Heads\n"
     "From: Finance Controller\n\n"
     "Subject: FY 2023-24 Book Closure\n\n"
     "Please ensure all vendor invoices for FY 2023-24\n"
     "are submitted to accounts by 31-March-2024.\n"
     "Any invoices received after this date will be\n"
     "processed in the next financial year.\n\n"
     "Compliance is mandatory for audit purposes."),
]


def make_pdf(pages, filename):
    path = os.path.join(OUTPUT, filename)
    doc = fitz.open()
    for text in pages:
        page = doc.new_page(width=595, height=842)  # A4
        # Header bar
        page.draw_rect(fitz.Rect(0, 0, 595, 60), color=(0.1, 0.3, 0.6), fill=(0.1, 0.3, 0.6))
        page.insert_text((20, 38), "MPHASIS LIMITED  |  INTERNAL DOCUMENT", fontsize=11, color=(1, 1, 1))
        # Body text
        page.insert_text((40, 90), text, fontsize=11)
        # Footer
        page.draw_line(fitz.Point(30, 810), fitz.Point(565, 810), color=(0.5, 0.5, 0.5))
        page.insert_text((40, 825), "CONFIDENTIAL  |  Mphasis Limited  |  FY 2023-24", fontsize=8, color=(0.5, 0.5, 0.5))
    doc.save(path)
    doc.close()
    print(f"  Created: {path}  ({len(pages)} pages)")


print("\nGenerating sample PDFs...\n")
make_pdf(DOC1_PAGES, "sample_doc1_march2024.pdf")
make_pdf(DOC2_PAGES, "sample_doc2_march2024.pdf")
print("\nDone! Both PDFs are in input_pdfs/")
print("Now run:  venv\\Scripts\\python src\\pipeline.py\n")
