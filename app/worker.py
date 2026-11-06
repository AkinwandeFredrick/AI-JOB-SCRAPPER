import os
import sys
import signal
import asyncio
from app.db import get_db_connection, init_db
from app.scraper.conservative import run_scraper
from app.tailor import tailor_job

def timeout_handler(signum, frame):
    print("Worker reached strict 10-minute runtime threshold limit. Terminating execution cleanly.")
    sys.exit(0)

def main():
    # Enforce safe infrastructure runtime caps
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(600) 
    
    init_db()
    
    # Run Asynchronous Scraper Pipeline within synchronous wrapper thread smoothly
    asyncio.run(run_scraper())
    
    # Fetch and process a maximum of 3 unhandled new jobs
    conn = get_db_connection()
    new_jobs = conn.execute("SELECT id FROM jobs WHERE status = 'new' LIMIT 3").fetchall()
    conn.close()
    
    if not new_jobs:
        print("No brand new jobs found to customize in this worker cycle.")
        return
        
    print(f"Processing {len(new_jobs)} raw jobs found in the queue grid...")
    for row in new_jobs:
        tailor_job(row["id"])

if __name__ == "__main__":
    main()
