import os
import json
import uuid
import re
from typing import Any, List, Dict
from dotenv import load_dotenv

load_dotenv()

# Centralized Directory Management from .env
DOCS_DIR = os.getenv("DOCS_DIR", "./docs")
CONTEXT_DIR = os.getenv("CONTEXT_DIR", "./context")

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(CONTEXT_DIR, exist_ok=True)

# --- DOCUMENT CLASS ---
class Document():
    def __init__(self, document_name):
        self.doc_name = document_name
        self._update_paths()
        self.paragraphs: Dict[str, Dict[str, Any]] = {} 
        # Automatically load existing paragraphs when the document is instantiated
        self._load_context()

    def _update_paths(self):
        """Updates internal file paths based on the current doc_name."""
        self.doc_file_path = os.path.join(DOCS_DIR, f"{self.doc_name}.json")
        self.context_file_path = os.path.join(CONTEXT_DIR, f"{self.doc_name}_cx.json")

    # --- 1. CORE I/O METHODS ---

    def _load_context(self):
        """Loads AI context from disk into memory."""
        if os.path.exists(self.context_file_path):
            try:
                with open(self.context_file_path, "r", encoding="utf-8") as f:
                    self.paragraphs = json.load(f)
            except Exception:
                self.paragraphs = {}
        else:
            self.paragraphs = {}

    def _save_context(self):
        """Saves the AI context to the context directory."""
        try:
            with open(self.context_file_path, "w", encoding="utf-8") as f:
                json.dump(self.paragraphs, f, indent=4)
        except Exception as e:
            print(f"Error saving context for {self.doc_name}: {e}")
    
    # --- PUBLIC METHODS ---

    @staticmethod
    def get_all_documents() -> List[Dict[str, str]]:
        """Static helper to list all available documents in the directory."""
        docs = []
        for file_name in os.listdir(DOCS_DIR):
            if file_name.endswith(".json"):
                stem = file_name[:-5]
                docs.append({
                    "id": stem,
                    "name": stem.replace("_", " ").replace("-", " ").title()
                })
        return docs
    
    def save_ui_document(self, content: str):
        """Saves the raw JSON string from the React frontend to disk."""
        with open(self.doc_file_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    def get_ui_document(self) -> str:
        """Reads the raw JSON string of the UI document from disk."""
        if not os.path.exists(self.doc_file_path):
            return "[]"
        with open(self.doc_file_path, "r", encoding="utf-8") as f:
            return f.read()
        
    def rename(self, new_name: str) -> bool:
        """Safely renames both the UI document and the Context document."""
        new_doc_path = os.path.join(DOCS_DIR, f"{new_name}.json")
        new_ctx_path = os.path.join(CONTEXT_DIR, f"{new_name}_cx.json")

        if os.path.exists(new_doc_path):
            return False # Target name already exists

        # Rename UI doc
        if os.path.exists(self.doc_file_path):
            os.rename(self.doc_file_path, new_doc_path)
        
        # Rename Context doc
        if os.path.exists(self.context_file_path):
            os.rename(self.context_file_path, new_ctx_path)

        self.doc_name = new_name
        self._update_paths()
        return True
    
    def update_paragraph_metadata(self, par_id: str, audio: str, ocr: str):
        """Updates just the AI inputs for a specific paragraph."""
        if par_id not in self.paragraphs:
            self.paragraphs[par_id] = {"audio": "", "ocr": "", "notes": "", "additional_notes": ""}
        self.paragraphs[par_id]["audio"] = audio
        self.paragraphs[par_id]["ocr"] = ocr
        self._save_context()

    def get_paragraph(self, par_id: str) -> Dict:
        par_dict = self.paragraphs.get(par_id, {})
        if par_dict:
            return {
                "success": True, 
                "audio": par_dict.get("audio", ""), 
                "ocr": par_dict.get("ocr", ""), 
                "notes": par_dict.get("notes", ""), 
                "additional": par_dict.get("additional_notes", "")
            }
        return {"success": False, "error": f"Paragraph {par_id} not found"}

    def replace_paragraph(self, par_id: str, content: str):
        """Updates the context memory AND the synchronized UI Document."""
        if par_id not in self.paragraphs:
            self.paragraphs[par_id] = {}
        
        self.paragraphs[par_id]["notes"] = content
        
        # 1. Save the backend context
        self._save_context()
        
        return {"success": True, "message": "Paragraph updated in both Context and UI Document."}

    def add_image(self, par_id: str, image_desc: str, image_url: str):
        if par_id not in self.paragraphs:
            self.paragraphs[par_id] = {}
        
        self.paragraphs[par_id]["image"] = {"description": image_desc, "url": image_url}
        self._save_document()
        return {"success": True}
    
    def add_additional_note(self, par_id: str, note: str):
        if par_id not in self.paragraphs:
            return {"success": False, "error": f"Paragraph {par_id} not found"}
            
        existing = self.paragraphs[par_id].get("additional_notes", "")
        self.paragraphs[par_id]["additional_notes"] = existing + "\n" + note if existing else note
        
        self._save_context()
        return {"success": True, "message": f"Note added to {par_id}"}
    
    # --- 2. RECONCILIATION & AI MEMORY ---

    def sync_context_from_ui(self):
        """
        Reads the latest UI JSON from disk and rebuilds the AI context.
        This flawlessly handles MERGING paragraphs and PRUNING deleted ones.
        """
        ui_content = self.get_ui_document()
        if not ui_content or ui_content == "[]":
            return
            
        try:
            ui_blocks = json.loads(ui_content)
        except Exception:
            return

        new_context = {}
        current_owner_id = "doc-start"
        accumulated_text = []

        # Initialize the starting bucket, preserving existing AI metadata but wiping old notes
        old_start = self.paragraphs.get("doc-start", {})
        new_context["doc-start"] = {
            "heading": "Document Start", 
            "audio": old_start.get("audio", ""),
            "ocr": old_start.get("ocr", ""),
            "additional_notes": old_start.get("additional_notes", ""),
            "notes": ""
        }

        for block in ui_blocks:
            if block.get("type") == "heading":
                # Flush text to previous owner
                new_context[current_owner_id]["notes"] = "\n\n".join(accumulated_text)
                
                # Setup new owner
                current_owner_id = block["id"]
                accumulated_text = []

                heading_text = "".join([p.get("text", "") for p in block.get("content", []) if isinstance(p, dict)]).strip()
                
                old_meta = self.paragraphs.get(current_owner_id, {})
                new_context[current_owner_id] = {
                    "heading": heading_text,
                    "audio": old_meta.get("audio", ""),
                    "ocr": old_meta.get("ocr", ""),
                    "additional_notes": old_meta.get("additional_notes", ""),
                    "notes": ""
                }
            elif block.get("content"):
                text = "".join([p.get("text", "") for p in block["content"] if isinstance(p, dict)])
                if text.strip(): 
                    accumulated_text.append(text)

        # Final flush
        new_context[current_owner_id]["notes"] = "\n\n".join(accumulated_text)

        # Atomic swap and save
        self.paragraphs = new_context
        self._save_context()

        