# load.py
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import logging
from sqlalchemy.dialects.postgresql import insert

load_dotenv()


def insert_on_conflict_nothing(table, conn, keys, data_iter):
    """
    Custom insert function that intercepts Pandas data and applies 
    PostgreSQL's 'ON CONFLICT DO NOTHING' rule.
    """
    # Convert the Pandas dataframe rows into a list of dictionaries
    data = [dict(zip(keys, row)) for row in data_iter]
    
    # Build the standard PostgreSQL insert statement
    stmt = insert(table.table).values(data)
    
    # Attach the silent ignore logic targeting your specific constraint columns
    on_conflict_stmt = stmt.on_conflict_do_nothing(
        index_elements=['tutor_id', 'year_number', 'month_number']
    )
    
    # Execute the modified command
    conn.execute(on_conflict_stmt)

def push_to_supabase(df):
    db_url = os.getenv("SUPABASE_URL")
    
    try:
        # 1. Create the engine (the bridge to your database)
        engine = create_engine(db_url)
        
        # 2. Push the dataframe to a table named 'tutor_evaluations'
        df.to_sql(
            name='tutor_evaluations', 
            con=engine, 
            if_exists='append', 
            index=False,
            method=insert_on_conflict_nothing
        )
        
        logging.info(f"Successfully loaded {len(df)} rows to Supabase.")
        return True
        
    except Exception as e:
        logging.error(f"Failed to load data to database: {e}")
        return False