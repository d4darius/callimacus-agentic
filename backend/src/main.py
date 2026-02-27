import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import logging
import re
import json
import uvicorn
import fitz
import io
import torch
import numpy as np
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydub import AudioSegment
from faster_whisper import WhisperModel

# --- LANGGRAPH IMPORTS ---
from langchain.messages import HumanMessage
from langgraph.types import Command
from document import Document
from learning_assistant.learning_assistant import (
    agent, 
    DOCUMENT_STORAGE, 
    in_memory_store,
    update_memory
)
from learning_assistant.utils import (
    load_global_memory, 
    save_global_memory
)
from learning_assistant.prompts import agent_user_prompt

# --- CONFIG & LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("CallimacusAPI")

DOCS_DIR = Path(__file__).resolve().parent / "docs"
MEDIA_DIR = Path(__file__).resolve().parent / "media"
CONTEXT_DIR = Path(__file__).resolve().parent / "context"

# --- GLOBAL ML MODELS ---
audio_model = None
vad_model = None
get_speech_timestamps = None

# --- LIFESPAN (MEMORY PERSISTENCE) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global audio_model, vad_model, get_speech_timestamps
    logger.info("🚀 Starting up Callimacus FastAPI Server...")

    # 1. Load LangGraph Memory
    load_global_memory(in_memory_store)
    
    # 2. Boot up Faster-Whisper (Using the 'base' or 'small' model for real-time speed)
    logger.info("🧠 Loading Faster-Whisper model...")
    cache_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-base/snapshots/")
    
    # Find the specific snapshot folder string inside
    try:
        snapshot_folder = os.listdir(cache_path)[0]
        local_model_path = os.path.join(cache_path, snapshot_folder)
        
        # Load directly from the hard drive, bypassing network requests completely!
        audio_model = WhisperModel(
            local_model_path, 
            device="cpu", 
            compute_type="default", 
            local_files_only=True,
            cpu_threads=2  
        )
        
    except FileNotFoundError:
        logger.error("❌ Faster-Whisper cache not found! Did you run setup_models.py?")
        raise
    
    # 3. Boot up Silero VAD
    logger.info("🧠 Loading Silero VAD model from local cache...")
    
    # 💡 THE FIX: Point directly to the PyTorch Hub cache folder!
    silero_cache_path = os.path.expanduser("~/.cache/torch/hub/snakers4_silero-vad_master")
    
    try:
        # Pass source='local' to skip GitHub completely!
        vad_model, utils = torch.hub.load(
            repo_or_dir=silero_cache_path, 
            source='local',
            model='silero_vad', 
            force_reload=False,
            trust_repo=True
        )
        (get_speech_timestamps, _, read_audio, _, _) = utils
        
    except FileNotFoundError:
        logger.error("❌ Silero VAD cache not found! Did you run setup_models.py?")
        raise

    logger.info("✅ Server startup complete.")
    
    yield # Server is running...
    
    logger.info("🛑 Shutting down server. Flushing RAM memory to disk...")
    # Save cross-thread preferences from RAM to JSON
    save_global_memory(in_memory_store)
    logger.info("✅ Server shutdown complete. Memory safely persisted.")

app = FastAPI(title="Callimacus Agent API", lifespan=lifespan)

# Allow your frontend dev server to call this API (tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- UTILS ---
def safe_doc_path(doc_id: str) -> Path:
    # Prevent path traversal; only allow simple ids like: example-1_test
    safe = re.sub(r"[^a-zA-Z0-9_-]", "", doc_id)
    return DOCS_DIR / f"{safe}.json"

def safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "", value)

# ------------------------------------------
# FILE SYSTEM & DOCUMENT ENDPOINTS
# ------------------------------------------

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

@app.post("/api/media/extract")
async def extract_pdf_text(file: UploadFile = File(...)):
    try:
        content = await file.read()
        # Open the PDF directly from the uploaded bytes
        doc = fitz.open(stream=content, filetype="pdf")
        
        pages_text = {}
        for i in range(len(doc)):
            # Extract text and replace heavy line-breaks with spaces for the LLM
            raw_text = doc[i].get_text("text").replace('\n', ' ')
            pages_text[str(i + 1)] = raw_text
            
        return {
            "status": "completed",
            "total_pages": len(doc),
            "pages": pages_text
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ------------------------------------------
# AI AGENT ENDPOINTS (LANGGRAPH)
# ------------------------------------------

class ProcessPayload(BaseModel):
    doc_id: str
    par_id: str
    audio: str = ""
    ocr: str = ""
    notes: str = ""

@app.post("/api/llm/process")
async def process_paragraph(payload: ProcessPayload):
    """Triggers the LangGraph agent to analyze sources and either compile or pause for HITL."""
    
    # 1. Ensure document is loaded in storage
    if payload.doc_id not in DOCUMENT_STORAGE:
        DOCUMENT_STORAGE[payload.doc_id] = Document(payload.doc_id)
    doc = DOCUMENT_STORAGE[payload.doc_id]
    
    # 2. Update the AI Context safely
    if payload.par_id not in doc.paragraphs:
        doc.paragraphs[payload.par_id] = {}
        
    doc.paragraphs[payload.par_id]["audio"] = payload.audio
    doc.paragraphs[payload.par_id]["ocr"] = payload.ocr
    doc.paragraphs[payload.par_id]["notes"] = payload.notes
    doc._save_context()

    # 3. Setup LangGraph Thread
    thread_id = f"{payload.doc_id}_{payload.par_id}"
    config = {"configurable": {"thread_id": thread_id}}
    
    agent_prompt = agent_user_prompt.format(
        doc_id = payload.doc_id,
        par_id = payload.par_id,
        audio = payload.audio,
        ocr = payload.ocr,
        notes = payload.notes
    )

    initial_state = {
        "messages": [HumanMessage(content=agent_prompt)],
        "doc_id": payload.doc_id,
        "par_id": payload.par_id
    }

    # 4. Run the Agent
    await agent.ainvoke(initial_state, config)

    # 5. Check if Agent Paused (HITL)
    state = agent.get_state(config)
    if state.tasks and state.tasks[0].interrupts:
        interrupt_payload = state.tasks[0].interrupts[0].value
        return {"status": "paused", "interrupt": interrupt_payload}

    return {"status": "completed", "message": "Paragraph successfully generated and synced."}


class ResumePayload(BaseModel):
    doc_id: str
    par_id: str
    answer: str

@app.post("/api/llm/resume")
async def resume_agent(payload: ResumePayload):
    """Resumes a paused graph after the user answers the clarification question."""
    
    thread_id = f"{payload.doc_id}_{payload.par_id}"
    config = {"configurable": {"thread_id": thread_id}}
    
    user_response = {
        "type": "response",
        "args": payload.answer
    }
    
    # Resume the graph execution
    await agent.ainvoke(Command(resume=user_response), config)
    
    # Check state just in case it asked another question
    state = agent.get_state(config)
    if state.tasks and state.tasks[0].interrupts:
        interrupt_payload = state.tasks[0].interrupts[0].value
        return {"status": "paused", "interrupt": interrupt_payload}
        
    return {"status": "completed", "message": "Conflict resolved and paragraph updated."}


class RequestPayload(BaseModel):
    doc_id: str
    par_id: str
    instruction: str # e.g., "Rewrite this to be bullet points"

@app.post("/api/llm/request")
async def request_rewrite(payload: RequestPayload):
    """Updates the Compiler's global memory and forces a paragraph rewrite."""
    
    # 1. Learn from the request! Target the Compiler Profile so it learns stylistic choices.
    update_memory(
        in_memory_store, 
        ("learning_assistant", "compiler_profile"), 
        [{"role": "user", "content": f"User requested a formatting/style change: {payload.instruction}"}]
    )
    
    # 2. Tell the graph to regenerate the paragraph
    thread_id = f"{payload.doc_id}_{payload.par_id}"
    config = {"configurable": {"thread_id": thread_id}}
    
    rewrite_prompt = f"The user requested a rewrite for this paragraph with these specific instructions: '{payload.instruction}'. Please invoke 'create_paragraph' immediately to regenerate and apply these changes."
    
    await agent.ainvoke({"messages": [HumanMessage(content=rewrite_prompt)]}, config)
    
    return {"status": "completed", "message": "Memory updated and paragraph rewritten."}

# ------------------------------------------
# REAL-TIME AUDIO WEBSOCKET
# ------------------------------------------
@app.websocket("/api/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("🎤 Client connected to Audio WebSocket")
    
    audio_buffer = bytearray()
    
    try:
        while True:
            # 1. Catch the RAW PCM audio bytes from React
            chunk = await websocket.receive_bytes()
            audio_buffer.extend(chunk)
            
            # We process every ~3 seconds (16kHz * 2 bytes * 3s = ~96000 bytes)
            if len(audio_buffer) >= 96000: 
                try:
                    # 2. Convert Raw Int16 Bytes directly to PyTorch Float32 Tensor
                    pcm_array = np.frombuffer(audio_buffer, dtype=np.int16)
                    samples = pcm_array.astype(np.float32) / 32768.0
                    audio_tensor = torch.from_numpy(samples)
                    
                    # 3. Run Silero VAD to detect speech
                    speech_timestamps = get_speech_timestamps(audio_tensor, vad_model, sampling_rate=16000)
                    
                    if speech_timestamps:
                        # 4. If speech is detected, run Faster-Whisper!
                        segments, info = audio_model.transcribe(samples, beam_size=5, language="en")
                        
                        transcript = " ".join([segment.text for segment in segments]).strip()
                        
                        if transcript:
                            logger.debug(f"🗣️ Transcribed: {transcript}")
                            await websocket.send_json({"text": f" {transcript} "})
                    
                    audio_buffer = bytearray()
                    
                except Exception as e:
                    logger.error(f"Audio Processing Error: {e}")
                    audio_buffer = bytearray()
            
    except WebSocketDisconnect:
        logger.info("🎤 Client disconnected from Audio WebSocket")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)