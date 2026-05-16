# keep_alive.py
import os
from sqlalchemy import create_engine
import logging

# Set up basic logging to see the output in GitHub Actions
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

def ping_database():
    # Notice we use os.environ.get instead of load_dotenv() here. 
    # GitHub Actions injects variables directly into the operating system environment.
    db_url = os.environ.get("SUPABASE_URL")
    
    if not db_url:
        logging.error("No SUPABASE_URL found in the environment.")
        return False
        
    try:
        engine = create_engine(db_url)
        # Using a context manager (with) ensures the connection closes immediately
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1;")
            
        logging.info("Database pinged successfully. Supabase 7-day timer reset.")
        return True
        
    except Exception as e:
        logging.error(f"Failed to ping database: {e}")
        return False

if __name__ == "__main__":
    ping_database()