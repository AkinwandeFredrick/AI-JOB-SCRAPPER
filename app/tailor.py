import os
import json
import socket
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
    """Loads a job, optimization prompts, calls Ollama via a raw TCP socket, updates DB, and outputs DOCX."""
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
    
    json_payload = json.dumps(payload)
    payload_bytes = json_payload.encode("utf-8")
    
    # Construct a raw, proxy-immune HTTP request raw text block
    http_request = (
        f"POST /v1/chat/completions HTTP/1.1\r\n"
        f"Host: 127.0.0.1:11434\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(payload_bytes)}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode("utf-8") + payload_bytes

    try:
        # Open a low-level, direct TCP socket channel
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(60)
        s.connect(("127.0.0.1", 11434))
        
        # Send raw data bytes across the open network socket pipeline
        s.sendall(http_request)
        
        # Receive the raw server text response buffer streams
        response_bytes = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response_bytes += chunk
        s.close()
        
        # Parse the raw HTTP response headers away from the target JSON body content
        response_text = response_bytes.decode("utf-8")
        header_split = response_text.split("\r\n\r\n", 1)
        if len(header_split) < 2:
            raise ValueError("Invalid HTTP response layout received from service socket.")
            
        json_body = header_split[1] # Exact array index extraction target fix
        res_json = json.loads(json_body)
        
        raw_content = res_json["choices"]["message"]["content"]
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
