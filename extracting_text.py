import shutil # helps move files
import pdfplumber # reads from pdf
import re 
import time
from datetime import datetime
import logging
from pathlib import Path
import pandas as pd
from collections import Counter
# todo:
    # make sure all data is clean. no bad data should enter ✅
    # use airflow to automate this
    # consider migrating to sql, not csv
    # consider separating your project into more files. extract.py transform.py  load.py main.py
    # consider adding testing regex tests, edge cases, category extraction
    # use powerBI to answer business questions. examples:
        # Which tutors are consistently underperforming?
        # Which category has the most negative feedback?
        # Trend of performance over time
    
# setup logging
# Added 'filename' so it writes to a log file instead of the invisible screen
logging.basicConfig(
    filename='pipeline_log.txt', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s', 
    datefmt='%H:%M:%S'
)
# Mute the underlying pdfminer library so it only reports fatal errors, not warnings
logging.getLogger("pdfminer").setLevel(logging.ERROR)

category_map = {
    'S': 'Setup',
    'A': 'Attitude',
    'P': 'Preparation',
    'C': 'Curriculum',
    'T': 'Teaching',
    'F': 'Feedback'
}

def quality_evaluation_pdf(file_path):
    evaluation_record = {
    "tutor_id": None,
    "tutor_name": None,
    "tutor_score": None,
    # "positive_comments": None,
    # "negative_comments": None,
    "year_number": None,
    "month_number": None,
    "day_number": None,
    "source_file": str(file_path.name),
    "is_outstanding": False,
    "positive_setup": 0, 
    "positive_attitude": 0, 
    "positive_preparation": 0,
    "positive_curriculum": 0, 
    "positive_teaching": 0, 
    "positive_feedback": 0,
    "negative_setup": 0, 
    "negative_attitude": 0, 
    "negative_preparation": 0,
    "negative_curriculum": 0, 
    "negative_teaching": 0, 
    "negative_feedback": 0
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
                # evaluation_record["positive_comments"] = positive_comments.strip() i don't need it now
                positive_comments_occurences = re.findall(r"([A-Z])\s[-–]",positive_comments)
                positive_counts = Counter(positive_comments_occurences)
                for letter, count in positive_counts.items():
                    # Look up the full word (e.g., 'T' becomes 'Teaching')
                    full_category_name = category_map[letter]
                    
                    # Format the new column name (e.g., 'negative_teaching')
                    column_name = f"positive_{full_category_name.lower()}"
                    
                    # Add it to our master dictionary
                    evaluation_record[column_name] = count
            else:
                    logging.warning("Failed to extract Positive Comments.")
                    
                
            # 4- negative comments:
            pattern = r"Need to Improve[\s:]+(.*)"
            match = re.search(pattern, pdf_text_page_three, re.IGNORECASE | re.DOTALL)
            if match:
                negative_comments = match.group(1).strip()
                negative_comments = re.sub(r"S-\d+","",negative_comments)
                negative_comments = re.sub(r"Page\s+\d+\s+of\s+\d+", "", negative_comments, flags=re.IGNORECASE)
                # evaluation_record["negative_comments"] = negative_comments.strip() i don't need it now
                negative_comments_occurences = re.findall(r"([A-Z])\s[-–]",negative_comments)
                negative_counts = Counter(negative_comments_occurences)
                for letter, count in negative_counts.items():
                    full_category_name = category_map[letter]
                    # Format the new column name (e.g., 'negative_teaching')
                    column_name = f"negative_{full_category_name.lower()}"
                    evaluation_record[column_name] = count
            else:
                logging.warning("Failed to extract Negative Comments.")
                
            # check if outstanding
            total_negatives = (
                evaluation_record["negative_setup"] +
                evaluation_record["negative_attitude"] +
                evaluation_record["negative_preparation"] +
                evaluation_record["negative_curriculum"] +
                evaluation_record["negative_teaching"] +
                evaluation_record["negative_feedback"]
            )
            total_positives = (
                evaluation_record["positive_setup"] +
                evaluation_record["positive_attitude"] +
                evaluation_record["positive_preparation"] +
                evaluation_record["positive_curriculum"] +
                evaluation_record["positive_teaching"] +
                evaluation_record["positive_feedback"]
            )
            if total_negatives == 0 and total_positives > 0:
                evaluation_record["is_outstanding"] = True
            
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
        return evaluation_record
    # Catch catastrophic file or reading errors
    except Exception as e:
        logging.error(f"Failed to process {file_path.name}: {e}")
        return None
        

def start_always_on_pipeline():
    
    # Point this to the MAIN folder containing all the month/year sub-folders
    landing_zone = Path("./test_quality_reports/") 
    archive_zone = Path("./archive_quality_reports/")
    
    # Ensure the folders actually exist before we try to move things
    landing_zone.mkdir(parents=True, exist_ok=True)
    archive_zone.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Starting batch extraction on '{landing_zone}'...")
    
      
        
        
        # rglob("*.pdf") recursively searches ALL sub-folders for pdfs
    pdf_files = list(landing_zone.rglob("*.pdf"))
        
        # If no files, sleep for 10 seconds and check again
    if len(pdf_files) == 0:
        logging.info("Landing zone is empty. Exiting batch job.")
        return # This immediately ends the script
        
    logging.info(f"Found {len(pdf_files)} files. Beginning extraction.")
        
        
            

    valid_pdf_paths = []
    all_extracted_data = []
    for pdf_path in pdf_files:
            
            
            logging.info(f"Processing: {pdf_path.name}")
            # Run our engine
            record = quality_evaluation_pdf(pdf_path)
            
            # If the file was processed successfully AND has no errors, add it to our master list
            if record:
                is_valid, errors = validate_record(record)
                
                if is_valid:
                    all_extracted_data.append(record)
                    valid_pdf_paths.append(pdf_path)
                else:
                    logging.warning(f"Invalid record from {pdf_path.name}: {errors}")
                    move_to_failed(pdf_path)

        # 4. The Output Layer (Preparing for SQL/Excel)
    if all_extracted_data:
            # Convert our list of dictionaries into a Pandas DataFrame
            df = pd.DataFrame(all_extracted_data)
            # Export straight to CSV
            output_file = Path("all_tutor_evaluations.csv")

            # This will be True if the file is there, False if it is brand new
            file_already_exists = output_file.is_file()

            # We set header to the OPPOSITE of file_already_exists using 'not'
            df.to_csv(
                output_file, 
                mode='a', 
                index=False, 
                header=not file_already_exists, 
                encoding='utf-8-sig'
            )
            logging.info(f"Successfully appended {len(df)} records to {output_file}")
            
            for pdf_path in valid_pdf_paths:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_filename = f"{pdf_path.stem}_{timestamp}{pdf_path.suffix}"
                    destination = archive_zone / new_filename
                    
                    shutil.move(str(pdf_path), str(destination))
                    
                except Exception as e:
                    logging.error(f"Failed to move {pdf_path.name}: {e}")
            
            logging.info("All processed files moved to the archive.")    
        
    else:
            logging.warning("Pipeline finished, but no data was extracted.")
        
def validate_record(record):
    errors = []
    
    # Required fields
    if not record["tutor_id"]:
        errors.append("Missing tutor_id")
        
    if not record["tutor_name"]:
        errors.append("Missing tutor_name")
    
    # Type checks
    try:
        score = int(record["tutor_score"])
        if score < 0 or score > 100:
            errors.append("Invalid score range")
    except:
        errors.append("Invalid tutor_score type")
    
    # Date checks
    if not all([
        record["year_number"],
        record["month_number"],
        record["day_number"]
    ]):
        errors.append("Incomplete date")
    
    # Logical checks
    total_feedback = (
        
                record["negative_setup"] +
                record["negative_attitude"] +
                record["negative_preparation"] +
                record["negative_curriculum"] +
                record["negative_teaching"] +
                record["negative_feedback"]+
                record["positive_setup"] +
                record["positive_attitude"] +
                record["positive_preparation"] +
                record["positive_curriculum"] +
                record["positive_teaching"] +
                record["positive_feedback"]
    )
    
    if total_feedback == 0:
        errors.append("No feedback detected")
    
    return len(errors) == 0, errors



def move_to_failed(pdf_path):
    failed_dir = Path("./failed_quality_reports/")
    failed_dir.mkdir(exist_ok=True)
    
    destination = failed_dir / pdf_path.name
    shutil.move(str(pdf_path), str(destination))
    
    
# Execute the script
if __name__ == "__main__":
    start_always_on_pipeline()
    
