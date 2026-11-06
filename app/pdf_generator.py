import os
import json
from docx import Document

def generate_docx_cv(tailored_json_str: str, output_path: str):
    """Generates a clean, modern, ATS-friendly Word document resume from the tailored JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        data = json.loads(tailored_json_str)
    except Exception as e:
        raise ValueError(f"Invalid JSON provided for resume generation: {e}")
        
    doc = Document()
    
    # Professional Summary Section
    doc.add_heading("Professional Summary", level=1)
    doc.add_paragraph(data.get("summary", ""))
    
    # Work Experience Section
    doc.add_heading("Work Experience", level=1)
    for exp in data.get("experience", []):
        p = doc.add_paragraph()
        r1 = p.add_run(f"{exp.get('title', '')} ")
        r1.bold = True
        p.add_run(f"at {exp.get('company', '')} ({exp.get('dates', '')})")
        
        for bullet in exp.get("bullets", []):
            doc.add_paragraph(bullet, style='List Bullet')
            
    # Technical Skills Section
    doc.add_heading("Skills", level=1)
    skills_list = data.get("skills", [])
    doc.add_paragraph(", ".join(skills_list))
    
    doc.save(output_path)
