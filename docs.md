This is solid real-world pipeline code. I’m going to walk you through it like a proper engineering doc—not just “what”, but “why”, so another engineer can maintain it without guessing.

---

# 🔧 1. Imports (Dependencies Layer)

```python
import shutil # helps move files
```

* Used to **move processed PDFs** from landing → archive.
* Think of it as your “file lifecycle manager”.

```python
import pdfplumber # reads from pdf
```

* Core extraction engine.
* Wraps `pdfminer` to **extract text from PDFs reliably**.

```python
import re 
```

* Regular expressions for **pattern matching** (IDs, names, scores, etc.).

```python
import time
```

* Controls delays (`sleep`) for polling the folder.

```python
from datetime import datetime
```

* Used for:

  * Parsing report dates
  * Generating archive timestamps

```python
import logging
```

* Production-grade logging instead of `print`.
* Critical for debugging pipelines.

```python
from pathlib import Path
```

* Modern file path handling (better than `os.path`).
* Cleaner and cross-platform.

```python
import pandas as pd
```

* Converts extracted data → structured table → CSV.

```python
from collections import Counter
```

* Counts occurrences of categories (e.g., how many “T - Teaching”).

---

# 🧾 2. Logging Configuration

```python
logging.basicConfig(
    filename='pipeline_log.txt', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s', 
    datefmt='%H:%M:%S'
)
```

* Writes logs to a **file instead of console**.
* Logs include:

  * Time
  * Severity (INFO, WARNING, ERROR)
  * Message

```python
logging.getLogger("pdfminer").setLevel(logging.ERROR)
```

* Silences noisy warnings from `pdfminer`.
* Only shows **critical failures**.

👉 This is important: without this, your logs become unreadable.

---

# 🗂️ 3. Category Mapping

```python
category_map = {
    'S': 'Setup',
    'A': 'Attitude',
    'P': 'Preparation',
    'C': 'Curriculum',
    'T': 'Teaching',
    'F': 'Feedback'
}
```

* Maps single-letter codes → full category names.
* Used to dynamically generate column names like:

  * `positive_teaching`
  * `negative_feedback`

---

# 🧠 4. Core Extraction Function

```python
def quality_evaluation_pdf(file_path):
```

This is the **main parsing engine** for ONE PDF.

---

## 4.1 Initialize Output Record

```python
evaluation_record = {
```

* A **structured dictionary** representing one row in your dataset.

Key points:

* Default values prevent missing-key errors
* All expected columns are predefined

```python
"source_file": str(file_path.name),
```

* Tracks origin → useful for debugging

```python
"is_outstanding": False,
```

* Derived metric (calculated later)

```python
"positive_setup": 0, ...
"negative_feedback": 0
```

* Pre-initialized counters

---

## 4.2 Open and Read PDF

```python
with pdfplumber.open(file_path) as pdf:
```

* Safely opens file (auto-closes after block)

```python
pdf_text_page_one = pdf.pages[0].extract_text() or ""
```

* Extracts text from each page
* `or ""` prevents crashes if page is empty

---

## 4.3 Extract Tutor ID

```python
pattern = r"tutor id[\s:]+(T-\d+)"
```

* Regex breakdown:

  * `"tutor id"` → anchor text
  * `[\s:]+` → spaces or colons
  * `(T-\d+)` → capture group like `T-1234`

```python
match = re.search(pattern, pdf_text_page_one, re.IGNORECASE)
```

* Case-insensitive search

```python
evaluation_record["tutor_id"] = match.group(1)
```

* Extracts captured value

---

## 4.4 Extract Tutor Name

```python
pattern = r"tutor name[\s:]+(.*)"
```

* Captures everything after “tutor name”

```python
.strip()
```

* Removes trailing spaces/newlines

---

## 4.5 Extract Score

```python
pattern = r"Total Score[\s:\n]+(\d+)"
```

* Handles:

  * spaces
  * colons
  * line breaks

---

## 4.6 Positive Comments Processing

```python
pattern = r"Positive Comment[\s:]+(.*)"
```

```python
re.DOTALL
```

* Makes `.` match **newlines**
* Important for multi-line comments

---

### Cleaning Step

```python
re.sub(r"S-\d+","",positive_comments)
```

* Removes student IDs

```python
re.sub(r"Page\s+\d+\s+of\s+\d+", "", ...)
```

* Removes page numbering

---

### Extract Category Letters

```python
re.findall(r"([A-Z])\s[-–]", positive_comments)
```

* Finds patterns like:

  * `T -`
  * `A –`

---

### Count Occurrences

```python
positive_counts = Counter(...)
```

---

### Map to Columns

```python
full_category_name = category_map[letter]
column_name = f"positive_{full_category_name.lower()}"
evaluation_record[column_name] = count
```

👉 This is **dynamic schema mapping** — very clean design.

---

## 4.7 Negative Comments (Same Logic)

* Same steps as positive:

  * Extract
  * Clean
  * Find categories
  * Count
  * Map to columns

---

## 4.8 Outstanding Logic

```python
total_negatives = (...)
total_positives = (...)
```

```python
if total_negatives == 0 and total_positives > 0:
    evaluation_record["is_outstanding"] = True
```

👉 Business rule:

* No negatives
* At least one positive

---

## 4.9 Extract Date

```python
date_pattern = r"([a-zA-Z]+\s+\d+,[\s\n]+\d+)"
```

* Matches:

  * `"July 21, 2025"`
  * `"July 21,\n2025"`

---

### Normalize + Parse

```python
report_date = date_match.group(1).replace("\n", " ")
```

```python
parsed_date = datetime.strptime(report_date, "%B %d, %Y")
```

* Converts string → datetime object

---

### Store Components

```python
evaluation_record["year_number"] = parsed_date.year
```

👉 Good for SQL partitioning later.

---

## 4.10 Error Handling

```python
except Exception as e:
```

* Catches:

  * Corrupted PDFs
  * Missing pages
  * Unexpected formats

```python
return None
```

👉 Important: prevents pipeline crash.

---

# 🔄 5. Pipeline Orchestration

```python
def start_always_on_pipeline():
```

This is your **automation loop**.

---

## 5.1 Define Zones

```python
landing_zone = Path("./test_quality_reports/")
archive_zone = Path("./archive_quality_reports/")
```

* Landing → incoming files
* Archive → processed files

---

## 5.2 Ensure Folders Exist

```python
mkdir(parents=True, exist_ok=True)
```

* Creates directories if missing
* Prevents runtime errors

---

## 5.3 Infinite Monitoring Loop

```python
while True:
```

👉 This is a **daemon-style pipeline**.

---

## 5.4 Detect Files

```python
pdf_files = list(landing_zone.rglob("*.pdf"))
```

* Recursively finds all PDFs

---

## 5.5 Idle Behavior

```python
if len(pdf_files) == 0:
    time.sleep(10)
    continue
```

👉 Poll every 10 seconds if empty.

---

## 5.6 Transfer Stability Check (Smart Part)

```python
previous_count = -1
```

```python
while True:
```

* Waits until file count stops changing

```python
if current_count == previous_count and previous_count != 0:
    break
```

👉 Prevents:

* Reading half-uploaded files
* Corrupted reads

This is actually a **very good engineering decision**.

---

## 5.7 Process Files

```python
for pdf_path in pdf_files:
```

```python
record = quality_evaluation_pdf(pdf_path)
```

```python
if record:
    all_extracted_data.append(record)
```

---

## 5.8 Convert to DataFrame

```python
df = pd.DataFrame(all_extracted_data)
```

---

## 5.9 Append to CSV

```python
file_already_exists = output_file.is_file()
```

```python
header=not file_already_exists
```

👉 Ensures:

* Header written only once
* Data appended afterward

---

## 5.10 Archive Processed Files

```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
```

```python
new_filename = f"{pdf_path.stem}_{timestamp}{pdf_path.suffix}"
```

👉 Prevents filename collisions.

```python
shutil.move(...)
```

* Moves file → archive

---

# 🚀 6. Entry Point

```python
if __name__ == "__main__":
    start_always_on_pipeline()
```

* Ensures script runs only when executed directly
* Not when imported

---

# 🧠 Big Picture (What This Pipeline Is)

This is a **batch ingestion pipeline with near-real-time monitoring**:

### Flow:

1. Watch folder (landing zone)
2. Wait for stable upload
3. Extract structured data from PDFs
4. Append to dataset (CSV)
5. Archive processed files
6. Repeat forever

---

# ⚠️ Honest Engineering Feedback

You did a lot right here. But if you want this to be production-grade:

### 1. You’re reading pages by index blindly

```python
pdf.pages[2]
```

* Will crash if PDF has fewer pages
  👉 Add safeguards

---

### 2. No schema validation

* If regex fails → silent bad data
  👉 Consider validation layer

---

### 3. CSV is not scalable

* Fine now, but:
  👉 Move to:
* SQL (PostgreSQL)
* Or data warehouse

---

### 4. No parallel processing

* All PDFs processed sequentially
  👉 Can be slow with large batches

