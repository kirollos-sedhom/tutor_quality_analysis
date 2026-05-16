# load.py
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import logging


load_dotenv()


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
            index=False
        )
        
        logging.info(f"Successfully loaded {len(df)} rows to Supabase.")
        return True
        
    except Exception as e:
        logging.error(f"Failed to load data to database: {e}")
        return False