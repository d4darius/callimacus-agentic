import os
import json
import uuid
import re
from typing import Any, Optional, List, Dict

# Define a directory to store the JSON files (document and context)
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "context")

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(CONTEXT_DIR, exist_ok=True)

# --- HELPERS ---
def parse_inline_markdown(text: str) -> list:
    """
    Parses basic Markdown inline styles into BlockNote JSON text arrays.
    Handles **bold**, *italic*, _italic_, and `code`.
    """
    # Regex to match **bold**, `code`, *italic*, or _italic_
    pattern = re.compile(r'(\*\*.*?\*\*|`.*?`|\*[^*]+\*|_[^_]+_)')
    
    parts = []
    last_end = 0
    
    for match in pattern.finditer(text):
        # 1. Add any preceding plain text
        if match.start() > last_end:
            parts.append({
                "type": "text", 
                "text": text[last_end:match.start()], 
                "styles": {}
            })
            
        # 2. Add the styled text
        token = match.group(0)
        if token.startswith('**') and token.endswith('**'):
            parts.append({"type": "text", "text": token[2:-2], "styles": {"bold": True}})
        elif token.startswith('`') and token.endswith('`'):
            parts.append({"type": "text", "text": token[1:-1], "styles": {"code": True, "textColor": "red"}})
        elif token.startswith('*') and token.endswith('*'):
            parts.append({"type": "text", "text": token[1:-1], "styles": {"italic": True}})
        elif token.startswith('_') and token.endswith('_'):
            parts.append({"type": "text", "text": token[1:-1], "styles": {"italic": True}})
            
        last_end = match.end()
        
    # 3. Add any remaining plain text at the end of the string
    if last_end < len(text):
        parts.append({
            "type": "text", 
            "text": text[last_end:], 
            "styles": {}
        })
        
    # 4. Filter out empty text chunks and return
    return [p for p in parts if p["text"]]

# --- DOCUMENT CLASS ---
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
        """Safely edits the BlockNote UI document to replace a section of blocks."""
        ui_blocks = []
        
        if os.path.exists(self.doc_file_path):
            try:
                with open(self.doc_file_path, "r", encoding="utf-8") as f:
                    ui_blocks = json.load(f)
                    if not isinstance(ui_blocks, list):
                        ui_blocks = []
            except Exception:
                pass

        if not ui_blocks:
            return

        # 1. Find the target Heading block
        start_idx = -1
        for i, block in enumerate(ui_blocks):
            if block.get("id") == par_id:
                start_idx = i
                break
                
        if start_idx == -1:
            print(f"Heading block {par_id} not found in UI document.")
            return
            
        # 2. Find the end of the section (the next heading, or end of document)
        end_idx = start_idx + 1
        while end_idx < len(ui_blocks):
            if ui_blocks[end_idx].get("type") == "heading":
                break
            end_idx += 1
            
        # 3. Delete the old blocks in this section
        del ui_blocks[start_idx + 1 : end_idx]
        
        # 4. Parse the LLM Markdown into BlockNote Blocks
        new_blocks = []
        
        # Split the markdown by double newlines to separate paragraphs/lists
        chunks = content.strip().split("\n\n")
        
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk: 
                continue

            if chunk.startswith("#"):
                # Count the number of hashes to determine heading level (1, 2, or 3)
                level = len(chunk) - len(chunk.lstrip("#"))
                heading_text = chunk.lstrip("#").strip()
                
                # If this is the very first chunk, update the existing section title!
                if len(new_blocks) == 0:
                    ui_blocks[start_idx]["content"] = parse_inline_markdown(heading_text)
                    continue # Skip appending a new block, move to the next chunk
                else:
                    # If it's a subheading later in the text, create a proper BlockNote heading
                    new_blocks.append({
                        "id": str(uuid.uuid4()),
                        "type": "heading",
                        "props": {
                            "backgroundColor": "default",
                            "textColor": "default",
                            "textAlignment": "left",
                            "level": min(max(level, 1), 3), # BlockNote supports levels 1-3
                            "isToggleable": False
                        },
                        "content": parse_inline_markdown(heading_text),
                        "children": []
                    })
                    continue
                
            block_type = "paragraph"
            text_val = chunk
            
            # Detect bullet points
            if chunk.startswith("- ") or chunk.startswith("* "):
                block_type = "bulletListItem"
                text_val = chunk[2:]
            # Detect numbered lists
            elif len(chunk) > 2 and chunk[0].isdigit() and chunk[1:3] in [". ", ") "]:
                block_type = "numberedListItem"
                text_val = chunk[3:]

            # Detect quotes and strip
            elif chunk.startswith(">"):
                block_type = "quote"
                # Remove the leading '>' and any extra whitespace
                text_val = chunk[1:].strip()
                # Use regex to dynamically strip leading bold labels like "**Note:** " or "**Warning:** "
                text_val = re.sub(r'^\*\*.*?\*\*\s*', '', text_val)
                
            # Create the BlockNote compliant JSON object
            new_blocks.append({
                "id": str(uuid.uuid4()), # Generate a fresh ID for the UI
                "type": block_type,
                "props": {
                    "backgroundColor": "default",
                    "textColor": "default",
                    "textAlignment": "left"
                },
                "content": parse_inline_markdown(text_val),
                "children": []
            })
            
        # 5. Insert the new blocks directly after the heading
        ui_blocks[start_idx + 1 : start_idx + 1] = new_blocks
        
        # 6. Save the UI array back to disk
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

        