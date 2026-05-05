# transform.py
import re
from datetime import datetime
from collections import Counter
import logging

def transform_raw_text_to_record(pages_text, file_name):
    """Takes raw text strings and parses them into a structured dictionary."""
    page1, page2, page3 = pages_text
    
    category_map = {
    'S': 'Setup',
    'A': 'Attitude',
    'P': 'Preparation',
    'C': 'Curriculum',
    'T': 'Teaching',
    'F': 'Feedback'
}
    
    evaluation_record = {
    "tutor_id": None,
    "tutor_name": None,
    "tutor_score": None,
    "year_number": None,
    "month_number": None,
    "day_number": None,
    "source_file": str(file_name),
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
    
    # ... all your Regex pattern matching goes here ...
                # 1- tutor id pattern: 
            # "tutor id" (anchor)
            # "[\s:]+" (handles any combination of spaces or colons)
            # "(T-\d+)" (captures the numbers into group 1)
    pattern = r"tutor id[\s:]+(T-\d+)"

            # Run the search with case insensitivity
    match = re.search(pattern, page1, re.IGNORECASE)    
    if match: 
                evaluation_record["tutor_id"] = match.group(1)
    else: 
                logging.warning("Failed to extract Tutor ID.")
                
            
            # 2- tutor name: 
    pattern = r"tutor name[\s:]+(.*)"
            

            # Run the search with case insensitivity
    match = re.search(pattern, page1, re.IGNORECASE)    
    if match: 
        evaluation_record["tutor_name"] = match.group(1).strip()
    else: 
        logging.warning("Failed to extract Tutor Name.")
                
                
                
            # 3- score: 
    pattern = r"Total Score[\s:\n]+(\d+)"
    match = re.search(pattern, page1, re.IGNORECASE)    
    if match: 
        evaluation_record["tutor_score"] = match.group(1)
    else: 
        logging.warning("Failed to extract Tutor Score.")
                
            

            
            # 4- positive comments:
    pattern = r"Positive Comment[\s:]+(.*)"
    match = re.search(pattern, page2, re.IGNORECASE | re.DOTALL)
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
    match = re.search(pattern, page3, re.IGNORECASE | re.DOTALL)
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
    date_match = re.search(date_pattern, page1)
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
    