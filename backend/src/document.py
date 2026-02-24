import os
from typing import Any, Optional, List, Dict

class Document():
    def __init__(self, document_name):
        self.doc_name = document_name
        self.paragraphs: Dict[str, Dict[str, Any]] = {} 

        # Automatically load existing paragraphs when the document is instantiated
        self._load_document()

    def _load_document(self):
        """
        Loads existing paragraphs from the database/storage into memory.
        """
        # TODO: Implement actual database/file reading logic here.
        # This function should query your storage using self.doc_name and populate self.paragraphs.
        
        # Example of what the populated state should look like:
        # self.paragraphs["doc-start"] = {
        #     "notes": "This is the text currently in the document.",
        #     "audio": "",
        #     "ocr": "",
        #     "additional_notes": ""
        # }
        pass

    def get_paragraph(self, par_id: str) -> Dict:
        par_dict = self.paragraphs.get(par_id, {})
        if par_dict:
            audio = par_dict.get("audio", "")
            ocr = par_dict.get("ocr", "")
            notes = par_dict.get("notes", "")
            additional = par_dict.get("additional_notes", "")
            # TODO log warning in case any of these three are missing
            return {"success": True, "audio": audio, "ocr": ocr, "notes": notes, "additional": additional}
        else:
            return {"success": False, "error": f"Paragraph {par_id} not found"}

    def replace_paragraph(self, par_id: str, content: str):
        """Updates the paragraph by overwriting the 'notes' with the finalized LLM content."""
        if par_id not in self.paragraphs:
            self.paragraphs[par_id] = {}
        
        # Overwrite 'notes' directly instead of creating 'final_content'
        self.paragraphs[par_id]["notes"] = content
        
        # TODO: Trigger a save operation here to persist this change back to your database
        
        return {"success": True, "message": "Paragraph notes updated."}

    def add_image(self, par_id: str, image_desc: str, image_url: str):
        if par_id not in self.paragraphs:
            self.paragraphs[par_id] = {}
        
        self.paragraphs[par_id]["image"] = {"description": image_desc, "url": image_url}
        return {"success": True}
    
    def add_additional_note(self, par_id:str, note: str):
        if not self.paragraphs[par_id]:
            return {"success": False, "error": f"Paragraph {par_id} not found and unable to add additional note"}
        additional_notes = self.paragraphs[par_id].get("additional_notes", "")

        if additional_notes:
            self.paragraphs[par_id]["additional_notes"] = additional_notes + "\n" + note
        else:
            self.paragraphs[par_id]["additional_notes"] = note

        return {"success": True, "message": f"Note: {note} added to paragraph {par_id}"}

        