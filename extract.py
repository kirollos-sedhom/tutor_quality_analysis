# extract.py
import pdfplumber
import logging

def extract_text_from_pdf(file_path):
    """Opens a PDF and returns a list of strings (one per page)."""
    try:
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) < 3:
                logging.warning(f"Skipping {file_path.name}: Expected 3+ pages.")
                return None
                
            page1 = pdf.pages[0].extract_text() or ""
            page2 = pdf.pages[1].extract_text() or ""
            page3 = pdf.pages[2].extract_text() or ""
            
        return [page1, page2, page3]
    except Exception as e:
        logging.error(f"Failed to read {file_path.name}: {e}")
        return None