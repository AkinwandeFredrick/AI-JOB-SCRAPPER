import os
import json
import urllib.request
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
    """Loads a job, optimization prompts, calls Ollama via standard urllib, updates DB, and outputs DOCX."""
    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return

    # Load configuration layouts
    with open(os.path.join(BASE_DIR, "data", "master_cv.json"), "r") as f:
        master_cv = f.read()
    with open(os.path.join(BASE_DIR, "prompts", "ats_rewrite.txt"), "r") as f:
        prompt_template = f.read()
        
    prompt = prompt_template.format(jd=job["description"], cv=master_cv)
    
    # Structure OpenAI-compatible payload natively
    payload = {
        "model": "qwen2.5:7b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    
    data_bytes = json.dumps(payload).encode("utf-8")
    url = "http://127.0.0"
    
    req = urllib.request.Request(
        url, 
        data=data_bytes, 
        headers={"Content-Type": "application/json"}
    )
    
    try:
        # Bypasses system-level proxy configurations completely
        with urllib.request.urlopen(req, timeout=60) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            
        raw_content = res_json["choices"][0]["message"]["content"]
        clean_json = clean_json_response(raw_content)
        
        # Validate structural payload integrity before saving
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
