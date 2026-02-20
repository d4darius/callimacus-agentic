from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import re

app = FastAPI()

# Allow your frontend dev server to call this API (tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOCS_DIR = Path(__file__).resolve().parent / "docs"
MEDIA_DIR = Path(__file__).resolve().parent / "media"

def safe_doc_path(doc_id: str) -> Path:
    # Prevent path traversal; only allow simple ids like: example-1_test
    safe = re.sub(r"[^a-zA-Z0-9_-]", "", doc_id)
    return DOCS_DIR / f"{safe}.json"

def safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "", value)

# --- SIDEBAR ENDPOINTS ---
class RenameUpdate(BaseModel):
    new_id: str   # e.g., "history_exam_v2"
    new_name: str # e.g., "History Exam V2"

@app.post("/api/docs/{doc_id}/rename")
def rename_doc(doc_id: str, payload: RenameUpdate):
    old_path = safe_doc_path(doc_id)
    new_path = safe_doc_path(payload.new_id)

    # 1. Check if the file we want to rename actually exists
    if not old_path.exists() or not old_path.is_file():
        raise HTTPException(status_code=404, detail="Original document not found")

    # 2. Prevent accidentally overwriting another file that already has the new name
    if new_path.exists():
        raise HTTPException(status_code=400, detail="A document with this name already exists")

    # 3. Physically rename the file on the hard drive
    old_path.rename(new_path)

    return {"ok": True, "oldId": doc_id, "newId": payload.new_id, "newName": payload.new_name}

class DocUpdate(BaseModel):
    content: str

# --- DOCUMENT ENDPOINTS ---
@app.get("/api/docs")
def list_docs():
    # 1. Create the directory if it doesn't exist yet
    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        
    docs = []
    for file_path in DOCS_DIR.glob("*.json"):
        docs.append({
            "id": file_path.stem, 
            "name": file_path.stem.replace("_", " ").replace("-", " ").title() 
        })
        
    return docs

@app.get("/api/docs/{doc_id}")
def get_doc(doc_id: str):
    path = safe_doc_path(doc_id)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Document not found")

    content = path.read_text(encoding="utf-8")
    return {"docId": doc_id, "content": content}

@app.put("/api/docs/{doc_id}")
def put_doc(doc_id: str, payload: DocUpdate):
    path = safe_doc_path(doc_id)
    
    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir(parents=True, exist_ok=True)

    path.write_text(payload.content, encoding="utf-8")
    
    return {"ok": True, "docId": doc_id}

# --- MEDIA ENDPOINTS ---
@app.get("/api/media/pdf/{pdf_id}")
def get_pdf(pdf_id: str):
    safe = safe_id(pdf_id)
    path = MEDIA_DIR / f"{safe}.pdf"
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="PDF not found")

    # Inline display in browser
    return FileResponse(path, media_type="application/pdf", filename=f"{safe}.pdf", content_disposition_type="inline")