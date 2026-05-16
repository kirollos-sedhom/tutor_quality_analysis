# main.py
from pathlib import Path
import logging
import pandas as pd
from datetime import datetime
import shutil # helps move files

# We import the specific functions from your new files
from extract import extract_text_from_pdf
from transform import transform_raw_text_to_record 
from load import push_to_supabase

def run_batch_pipeline():
    landing_zone = Path("./test_quality_reports/") 
    archive_zone = Path("./archive_quality_reports/")

    pdf_files = list(landing_zone.rglob("*.pdf"))
    
    if not pdf_files:
        return
        
    valid_pdf_paths = []
    all_extracted_data = []
    
    for pdf_path in pdf_files:
        # Step 1: Extract (Get the raw text)
        logging.info(f"Processing: {pdf_path.name}")
        raw_text_pages = extract_text_from_pdf(pdf_path)
        
        if raw_text_pages:
            # Step 2: Transform (Pass the text variable into the Brain)
            record = transform_raw_text_to_record(raw_text_pages, pdf_path.name)
            
            # Step 3: Validate and prepare for Load
            if record:
                # ... run validation, append to master list ...
                is_valid, errors = validate_record(record)
                
                if is_valid:
                    all_extracted_data.append(record)
                    valid_pdf_paths.append(pdf_path)
                
                else:
                    logging.warning(f"Invalid record from {pdf_path.name}: {errors}")
                    move_to_failed(pdf_path)
            else:
                logging.error(f"Transformation failed. No record generated for {pdf_path.name}.")
                move_to_failed(pdf_path)
                
        else:
            logging.error(f"Extraction failed. Could not read text from {pdf_path.name}.")
            move_to_failed(pdf_path)
         # 4. The Output Layer (Preparing for SQL/Excel)
    if all_extracted_data:
            # Convert our list of dictionaries into a Pandas DataFrame
            df = pd.DataFrame(all_extracted_data)
            # Export straight to CSV
            output_file = Path("all_tutor_evaluations_v2.csv")

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
            push_to_supabase(df)
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
    
    
    
# --- ADD THIS TO THE VERY BOTTOM ---
if __name__ == "__main__":
    # Setup logging so you can see what is happening in the terminal
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s: %(message)s', 
        datefmt='%H:%M:%S'
    )
    
    # Actually trigger the pipeline
    run_batch_pipeline()