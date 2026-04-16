import pdfplumber
import re
from datetime import datetime
import logging
import pandas as pd

# setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
# Mute the underlying pdfminer library so it only reports fatal errors, not warnings
logging.getLogger("pdfminer").setLevel(logging.ERROR)

file_path = "./quality reports/August_2025/T-1004.pdf"

evaluation_record = {
    "tutor_id": None,
    "tutor_name": None,
    "tutor_score": None,
    "positive_comments": None,
    "negative_comments": None,
    "year_number": None,
    "month_number": None,
    "day_number": None
}
try:
    with pdfplumber.open(file_path) as pdf:
        # Extract text, defaulting to an empty string if the page is completely blank
        pdf_text_page_one = pdf.pages[0].extract_text() or ""
        pdf_text_page_two = pdf.pages[1].extract_text() or ""
        pdf_text_page_three = pdf.pages[2].extract_text() or ""
        
        # 1- tutor id pattern: 
        # "tutor id" (anchor)
        # "[\s:]+" (handles any combination of spaces or colons)
        # "(T-\d+)" (captures the numbers into group 1)
        pattern = r"tutor id[\s:]+(T-\d+)"

        # Run the search with case insensitivity
        match = re.search(pattern, pdf_text_page_one, re.IGNORECASE)    
        if match: 
            evaluation_record["tutor_id"] = match.group(1)
        else: 
            logging.warning("Failed to extract Tutor ID.")
            
        
        # 2- tutor name: 
        pattern = r"tutor name[\s:]+(.*)"

        # Run the search with case insensitivity
        match = re.search(pattern, pdf_text_page_one, re.IGNORECASE)    
        if match: 
            evaluation_record["tutor_name"] = match.group(1).strip()
        else: 
            logging.warning("Failed to extract Tutor Name.")
            
            
            
        # 3- score: 
        pattern = r"Total Score[\s:\n]+(\d+)"
        match = re.search(pattern, pdf_text_page_one, re.IGNORECASE)    
        if match: 
            evaluation_record["tutor_score"] = match.group(1)
        else: 
            logging.warning("Failed to extract Tutor Score.")
            
        

        
        # 4- positive comments:
        pattern = r"Positive Comment[\s:]+(.*)"
        match = re.search(pattern, pdf_text_page_two, re.IGNORECASE | re.DOTALL)
        if match:
            positive_comments = match.group(1).strip()
            
            # remove irrelevant info 
            # remove student ID (S-xxxx)
            positive_comments = re.sub(r"S-\d+","",positive_comments)
            # remove page number (page 2 of 4)
            # Remove the page numbers
            positive_comments = re.sub(r"Page\s+\d+\s+of\s+\d+", "", positive_comments, flags=re.IGNORECASE)
            evaluation_record["positive_comments"] = positive_comments.strip()
        else:
                logging.warning("Failed to extract Positive Comments.")
                
            
        # 4- negative comments:
        pattern = r"Need to Improve[\s:]+(.*)"
        match = re.search(pattern, pdf_text_page_three, re.IGNORECASE | re.DOTALL)
        if match:
            negative_comments = match.group(1).strip()
            negative_comments = re.sub(r"S-\d+","",negative_comments)
            negative_comments = re.sub(r"Page\s+\d+\s+of\s+\d+", "", negative_comments, flags=re.IGNORECASE)
            evaluation_record["negative_comments"] = negative_comments.strip()
        else:
            logging.warning("Failed to extract Negative Comments.")
            
        
        # 5- date
        date_pattern = r"([a-zA-Z]+\s+\d+,[\s\n]+\d+)"
        date_match = re.search(date_pattern, pdf_text_page_one)
        if date_match:
            try:
                # Replace the newline with a space to clean up "July 21,\n2025" into "July 21, 2025"
                report_date = date_match.group(1).replace("\n", " ")
                # Convert the string into a mathematical datetime object
                parsed_date = datetime.strptime(report_date, "%B %d, %Y")
                evaluation_record["year_number"] = parsed_date.year
                evaluation_record["month_number"] = parsed_date.month
                evaluation_record["day_number"] = parsed_date.day
            except ValueError as e:
                    logging.error(f"Date found but failed to parse: {report_date}. Error: {e}")
        else:
            logging.warning("Failed to extract Date.")

# Catch catastrophic file or reading errors
except FileNotFoundError:
    logging.error(f"CRITICAL: Could not locate the file at {file_path}")
except Exception as e:
    logging.error(f"CRITICAL: An unexpected error occurred while processing the PDF: {e}")
    
# The dictionary is now perfectly formatted to be appended to a Pandas DataFrame or SQL insert
print("\nFinal Extracted Record:")
print(evaluation_record)