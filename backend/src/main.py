import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import logging
import re
import json
import uvicorn
import fitz
import asyncio
import time
import numpy as np
import concurrent.futures
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydub import AudioSegment
from faster_whisper import WhisperModel

# ------------------------------------------
# LANGGRAPH IMPORTS 
# ------------------------------------------

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

# ------------------------------------------
# CONFIG & LOGGING
# ------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("CallimacusAPI")

DOCS_DIR = os.getenv("DOCS_DIR", "./docs")
CONTEXT_DIR = os.getenv("CONTEXT_DIR", "./context")

# ------------------------------------------
# GLOBAL ML MODELS
# ------------------------------------------

audio_model = None
ml_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

# ------------------------------------------
# TESTING FUNCTION
# ------------------------------------------

def run_document_sanity_checks():
    """Simulates user actions to verify the unified Document architecture."""
    logger.info("🧪 Running Document Architecture Sanity Checks...")
    
    test_id = "test_sanity_123"
    doc = Document(test_id)
    
    try:
        # TEST 1: Simulate user creating a document with 2 headings
        dummy_ui = [
            {"id": "h1", "type": "heading", "content": [{"text": "Title"}]},
            {"id": "p1", "type": "paragraph", "content": [{"text": "Hello"}]},
            {"id": "h2", "type": "heading", "content": [{"text": "Second"}]},
            {"id": "p2", "type": "paragraph", "content": [{"text": "World"}]}
        ]
        doc.save_ui_document(json.dumps(dummy_ui))
        
        # Trigger the sync (what happens when the user hits 'Process')
        doc.sync_context_from_ui()
        
        assert "h1" in doc.paragraphs, "H1 missing from context!"
        assert "h2" in doc.paragraphs, "H2 missing from context!"
        assert doc.paragraphs["h1"]["notes"] == "Hello", "P1 text didn't map to H1!"
        
        # TEST 2: Simulate user DELETING the second heading (Merging p2 into h1)
        dummy_ui_merged = [
            {"id": "h1", "type": "heading", "content": [{"text": "Title"}]},
            {"id": "p1", "type": "paragraph", "content": [{"text": "Hello"}]},
            {"id": "p2", "type": "paragraph", "content": [{"text": "World"}]}
        ]
        doc.save_ui_document(json.dumps(dummy_ui_merged))
        doc.sync_context_from_ui()
        
        assert "h2" not in doc.paragraphs, "Pruning failed! Deleted heading still in memory."
        assert doc.paragraphs["h1"]["notes"] == "Hello\n\nWorld", "Merge upward failed! Text didn't combine."
        
        # TEST 3: Simulate the AI receiving Audio/OCR
        doc.update_paragraph_metadata("h1", audio="test audio", ocr="test ocr")
        
        assert doc.paragraphs["h1"]["audio"] == "test audio", "Audio failed to save."
        assert doc.paragraphs["h1"]["notes"] == "Hello\n\nWorld", "CRITICAL BUG: Updating AI metadata wiped the user's notes!"
        
        logger.info("✅ All Document Sanity Checks Passed! Architecture is rock solid.")
        
    finally:
        # Cleanup the dummy files so we don't clutter your directories
        if os.path.exists(doc.doc_file_path):
            os.remove(doc.doc_file_path)
        if os.path.exists(doc.context_file_path):
            os.remove(doc.context_file_path)

# ------------------------------------------
# LIFESPAN
# ------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global audio_model
    logger.info("🚀 Starting up Callimacus FastAPI Server...")

    # 0. Run unified architecture tests
    run_document_sanity_checks()

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

# ------------------------------------------
# UTILS
# ------------------------------------------

def safe_doc_path(doc_id: str) -> Path:
    # Prevent path traversal; only allow simple ids like: example-1_test
    safe = re.sub(r"[^a-zA-Z0-9_-]", "", doc_id)
    return DOCS_DIR / f"{safe}.json"

def safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "", value)

def get_document(doc_id: str) -> Document:
    """Ensures a single instance of a document exists in memory."""
    if doc_id not in DOCUMENT_STORAGE:
        DOCUMENT_STORAGE[doc_id] = Document(doc_id)
    return DOCUMENT_STORAGE[doc_id]

# ------------------------------------------
# FILE SYSTEM & DOCUMENT ENDPOINTS
# ------------------------------------------

# --- SIDEBAR ENDPOINTS ---
class RenameUpdate(BaseModel):
    new_id: str   # e.g., "history_exam_v2"
    new_name: str # e.g., "History Exam V2"

@app.post("/api/docs/{doc_id}/rename")
def rename_doc(doc_id: str, payload: RenameUpdate):
    doc = get_document(doc_id)
    
    success = doc.rename(payload.new_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot rename. Target exists or original missing.")
    
    # Update global storage dictionary key
    DOCUMENT_STORAGE[payload.new_id] = DOCUMENT_STORAGE.pop(doc_id)
    return {"ok": True, "oldId": doc_id, "newId": payload.new_id, "newName": payload.new_name}

class DocUpdate(BaseModel):
    content: str

# --- DOCUMENT ENDPOINTS ---
@app.get("/api/docs")
def list_docs():
    return Document.get_all_documents()

@app.get("/api/docs/{doc_id}")
def get_doc(doc_id: str):
    doc = get_document(doc_id)
    content = doc.get_ui_document()
    if not content or content == "[]":
        # Create it if it's completely empty
        doc.save_ui_document("[]")
    return {"docId": doc_id, "content": content}

@app.put("/api/docs/{doc_id}")
def put_doc(doc_id: str, payload: DocUpdate):
    doc = get_document(doc_id)
    doc.save_ui_document(payload.content)
    return {"ok": True, "docId": doc_id}

# --- MEDIA ENDPOINTS ---
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
    doc = get_document(payload.doc_id)
    
    # 2. Update the AI Context safely
    doc.update_paragraph_metadata(payload.par_id, payload.audio, payload.ocr)

    # 3. Setup LangGraph Thread
    thread_id = f"{payload.doc_id}_{payload.par_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Fetch perfectly reconciled notes
    par_data = doc.get_paragraph(payload.par_id)
    current_notes = par_data.get("notes", "")
    
    agent_prompt = agent_user_prompt.format(
        doc_id = payload.doc_id,
        par_id = payload.par_id,
        audio = payload.audio,
        ocr = payload.ocr,
        notes = current_notes
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
    instruction: str

@app.post("/api/llm/request")
async def request_rewrite(payload: RequestPayload):
    """Updates the Compiler's global memory and forces a paragraph rewrite."""
    doc = get_document(payload.doc_id)

    # 1. Trigger the atomic sync here too!
    doc.sync_context_from_ui()
    
    # 2. Learn from the request! Target the Compiler Profile so it learns stylistic choices.
    update_memory(
        in_memory_store, 
        ("learning_assistant", "compiler_profile"), 
        [{"role": "user", "content": f"User requested a formatting/style change: {payload.instruction}"}]
    )
    
    # 2. Tell the graph to regenerate the paragraph
    thread_id = f"{payload.doc_id}_{payload.par_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Fetch perfectly reconciled notes
    par_data = doc.get_paragraph(payload.par_id)
    current_notes = par_data.get("notes", "")
    
    rewrite_prompt = f"The user requested a rewrite: '{payload.instruction}'. Use these notes: {current_notes}. Please invoke 'create_paragraph'."

    await agent.ainvoke({"messages": [HumanMessage(content=rewrite_prompt)]}, config)
    return {"status": "completed", "message": "Memory updated and paragraph rewritten."}

# ------------------------------------------
# REAL-TIME AUDIO WEBSOCKET
# ------------------------------------------

@app.websocket("/api/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("🎤 Client connected to Audio WebSocket")
    
    # 💡 THE FIX: 3 Dedicated Queues to enforce strict single-file processing
    audio_queue = asyncio.Queue()  # Holds raw binary chunks from frontend
    ml_queue = asyncio.Queue()     # Holds completed sentences waiting for the AI
    msg_queue = asyncio.Queue()    # Holds text waiting to be sent back to React

    # --- STAGE 1: THE RECEIVER (FastAPI -> audio_queue) ---
    async def receiver():
        try:
            while True:
                chunk = await websocket.receive_bytes()
                await audio_queue.put(chunk)
        except WebSocketDisconnect:
            logger.info("🎤 Client disconnected normally.")
        except Exception as e:
            logger.error(f"❌ WebSocket Receiver Error: {e}")

    # --- STAGE 2: THE ENERGY GATE (audio_queue -> ml_queue) ---
    async def energy_gate():
        audio_buffer = bytearray()
        silence_chunks = 0
        is_recording = False
        
        while True:
            chunk = await audio_queue.get()
            if len(chunk) == 0: 
                continue
                
            pcm_array = np.frombuffer(chunk, dtype=np.int16)
            rms_volume = np.sqrt(np.mean(pcm_array.astype(np.float32)**2))
            
            if rms_volume > 200:
                is_recording = True
                silence_chunks = 0
                audio_buffer.extend(chunk)
                
                # HARD CUTOFF: 10 seconds. (Failsafe if they literally scream for 10s straight)
                if len(audio_buffer) > 320000:
                    await ml_queue.put(bytes(audio_buffer))
                    is_recording = False
                    audio_buffer = bytearray()
            else:
                if is_recording:
                    silence_chunks += 1
                    audio_buffer.extend(chunk) 
                    
                    # SMART BREATH DETECTION
                    # 1. Normal breath: ~0.5 seconds (2 chunks)
                    # 2. Aggressive cutoff: If the buffer is over 5 seconds long, cut on a micro-pause (1 chunk)
                    is_long_sentence = len(audio_buffer) > 160000
                    
                    if (is_long_sentence and silence_chunks >= 1) or (silence_chunks >= 2):
                        await ml_queue.put(bytes(audio_buffer))
                        is_recording = False
                        audio_buffer = bytearray()
                        silence_chunks = 0

    # --- STAGE 3: THE STRICT ML WORKER (ml_queue -> msg_queue) ---
    def run_transcription(buffer_bytes):
        """This function is now safely isolated."""
        try:
            pcm_array = np.frombuffer(buffer_bytes, dtype=np.int16)
            samples = pcm_array.astype(np.float32) / 32768.0
            
            # CTranslate2 is completely safe here because we only process one at a time!
            segments, _ = audio_model.transcribe(
                samples, beam_size=5, language="en", condition_on_previous_text=False
            )
            return " ".join([s.text for s in segments]).strip()
        except Exception as e:
            logger.error(f"❌ Transcription Error: {e}")
            return ""

    async def ml_worker():
        loop = asyncio.get_running_loop()
        while True:
            # Wait for a sentence to be ready
            buffer_bytes = await ml_queue.get() 
            
            # 💡 THE FIX: Force the math into the immortal thread!
            # Because it's always the exact same OS thread, the C++ memory never corrupts.
            transcript = await loop.run_in_executor(
                ml_executor, run_transcription, buffer_bytes
            )
            
            if transcript:
                logger.debug(f"🗣️ Transcribed: {transcript}")
                await msg_queue.put({"text": f" {transcript} "})

    # --- STAGE 4: THE SENDER (msg_queue -> FastAPI) ---
    async def sender():
        try:
            while True:
                msg = await msg_queue.get()
                await websocket.send_json(msg)
        except Exception as e:
            logger.error(f"❌ Sender Error: {e}")

    # Boot up the background workers
    gate_task = asyncio.create_task(energy_gate())
    ml_task = asyncio.create_task(ml_worker())
    send_task = asyncio.create_task(sender())
    
    # The endpoint locks onto the receiver. If the browser disconnects, clean up.
    try:
        await receiver()
    finally:
        gate_task.cancel()
        ml_task.cancel()
        send_task.cancel()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)