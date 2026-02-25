import os
import json
from typing import Any, Optional, List, Dict

# Define a directory to store the JSON files (document and context)
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "context")

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(CONTEXT_DIR, exist_ok=True)

class Document():
    def __init__(self, document_name):
        self.doc_name = document_name
        self.doc_file_path = os.path.join(DOCS_DIR, f"{self.doc_name}.json")
        self.context_file_path = os.path.join(CONTEXT_DIR, f"{self.doc_name}.json")
        self.paragraphs: Dict[str, Dict[str, Any]] = {} 

        # Automatically load existing paragraphs when the document is instantiated
        self._load_document()

    def _load_document(self):
        """
        Loads existing paragraphs from the database/storage into memory.
        """
        if os.path.exists(self.context_file_path):
            try:
                with open(self.context_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.paragraphs = data
                    else:
                        self.paragraphs = {}
            except Exception as e:
                print(f"Error loading context for {self.doc_name}: {e}")
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
    
    def _update_ui_document(self, par_id: str, content: str):
        """Safely edits the BlockNote UI document to insert the finalized text."""
        ui_blocks = []
        
        # 1. Load the existing BlockNote UI array
        if os.path.exists(self.doc_file_path):
            try:
                with open(self.doc_file_path, "r", encoding="utf-8") as f:
                    ui_blocks = json.load(f)
                    if not isinstance(ui_blocks, list):
                        ui_blocks = [] # Reset if corrupted
            except Exception:
                pass

        # 2. Find the target block and update its content safely
        block_found = False
        for block in ui_blocks:
            if block.get("id") == par_id:
                # BlockNote expects text inside a content array
                block["content"] = [{"type": "text", "text": content, "styles": {}}]
                block_found = True
                break
        
        # 3. If the block doesn't exist yet, append it
        if not block_found:
            ui_blocks.append({
                "id": par_id,
                "type": "paragraph",
                "content": [{"type": "text", "text": content, "styles": {}}]
            })

        # 4. Save the UI array back to the docs directory
        try:
            with open(self.doc_file_path, "w", encoding="utf-8") as f:
                json.dump(ui_blocks, f, indent=4)
        except Exception as e:
            print(f"Error saving UI Document {self.doc_name}: {e}")
    
    # --- PUBLIC METHODS ---

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
        
        # 2. Safely push the text to the React document!
        self._update_ui_document(par_id, content)
        
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

        