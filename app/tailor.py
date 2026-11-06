import os
import json
from openai import OpenAI
from app.db import get_db_connection
from app.pdf_generator import generate_docx_cv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def clean_json_response(text: str) -> str:
    """Removes common local LLM markdown block formatting wrappers safely."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def tailor_job(job_id: int):
    """Loads a job, optimization prompts, calls Ollama LLM, updates DB, and outputs DOCX asset."""
    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return

    # Load configurations
    with open(os.path.join(BASE_DIR, "data", "master_cv.json"), "r") as f:
        master_cv = f.read()
    with open(os.path.join(BASE_DIR, "prompts", "ats_rewrite.txt"), "r") as f:
        prompt_template = f.read()
        
    prompt = prompt_template.format(jd=job["description"], cv=master_cv)
    
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    
    try:
        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        raw_content = response.choices.message.content
        clean_json = clean_json_response(raw_content)
        
        # Verify it's structurally valid JSON before committing
        json.loads(clean_json)
        
        doc_filename = f"tailored_cv_{job_id}.docx"
        doc_relative_path = os.path.join("data", "output", doc_filename)
        doc_absolute_path = os.path.join(BASE_DIR, doc_relative_path)
        
        generate_docx_cv(clean_json, doc_absolute_path)
        
        # Save modifications to database instance
        conn.execute(
            "INSERT INTO tailored_cvs (job_id, tailored_json, pdf_path) VALUES (?, ?, ?)",
            (job_id, clean_json, doc_relative_path)
        )
        conn.execute("UPDATE jobs SET status = 'processed' WHERE id = ?", (job_id,))
        conn.commit()
        print(f"Successfully processed and generated CV for Job ID: {job_id}")
        
    except Exception as e:
        print(f"Error compiling tailored CV for Job ID {job_id}: {e}")
    finally:
        conn.close()
