import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db import get_db_connection

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

app = FastAPI(title="Job AI Assistant Dashboard")

# Ensure critical resource folders exist prior to directory mapping step
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
def index(request: Request, status: str = "all"):
    conn = get_db_connection()
    if status == "all":
        jobs = conn.execute("SELECT * FROM jobs ORDER BY scraped_at DESC").fetchall()
    else:
        jobs = conn.execute("SELECT * FROM jobs WHERE status = ? ORDER BY scraped_at DESC", (status,)).fetchall()
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs, "current_filter": status})

@app.get("/job/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        conn.close()
        raise HTTPException(status_code=404, detail="Job record context variant not found")
        
    tailored = conn.execute("SELECT * FROM tailored_cvs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job, "tailored": tailored})

@app.post("/job/{job_id}/status")
def update_status(job_id: int, status: str = Form(...)):
    if status not in ["approved", "rejected", "new", "processed"]:
        raise HTTPException(status_code=400, detail="Provided pipeline status selection state is invalid")
    conn = get_db_connection()
    conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/job/{job_id}", status_code=303)

@app.get("/download/{job_id}")
def download_cv(job_id: int):
    conn = get_db_connection()
    tailored = conn.execute("SELECT pdf_path FROM tailored_cvs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    
    if not tailored or not tailored["pdf_path"]:
        raise HTTPException(status_code=404, detail="No optimization document associated with this tracking entry ID")
        
    full_path = os.path.join(BASE_DIR, tailored["pdf_path"])
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="The targeted generated docx asset file is missing from local disk storage")
        
    return FileResponse(
        path=full_path, 
        filename=os.path.basename(full_path), 
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
