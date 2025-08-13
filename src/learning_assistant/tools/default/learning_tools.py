"""Learning assistant tools for processing educational content."""

import os
import json
from typing import Optional, List, Dict, Any
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


def write_notes_to_file(final_notes: Dict[str, str], file_path: str = "notes.md") -> None:
    """Write the final_notes dictionary to a markdown file.
    
    Args:
        final_notes: Dictionary with section_id as keys and content as values
        file_path: Path to the markdown file to write
    """
    try:
        content = ""
        for section_id in sorted(final_notes.keys()):
            #content += f"# Section {section_id}\n\n"
            content += final_notes[section_id]
            content += "\n\n"#---\n\n"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
            
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")


def generate_section_id(final_notes: Dict[str, str]) -> str:
    """Generate a new section ID based on existing sections.
    
    Args:
        final_notes: Dictionary with existing section IDs
        
    Returns:
        New section ID as string
    """
    if not final_notes:
        return "1"
    
    # Find highest numeric section ID and increment
    max_id = 0
    for section_id in final_notes.keys():
        try:
            id_num = int(section_id)
            max_id = max(max_id, id_num)
        except ValueError:
            # Non-numeric section ID, skip
            continue
    
    return str(max_id + 1)


class WriteContentInput(BaseModel):
    """Input for write content tool."""
    integrated_content: str = Field(description="The integrated content combining audio, slides, and notes")
    section_id: Optional[str] = Field(default=None, description="ID of the section to write to. If None, creates new section")
    position: str = Field(default="append", description="Where to place content: 'append', 'prepend', or 'replace'")


class EnhanceContentInput(BaseModel):
    """Input for enhance content tool."""
    section_id: str = Field(description="ID of the section to enhance")
    enhancement_type: str = Field(description="Type of enhancement: 'image', 'diagram', 'code', 'schema'")
    description: str = Field(description="Description of what enhancement is needed")


class QuestionInput(BaseModel):
    """Input for question tool."""
    question: str = Field(description="Question to ask the user for clarification")
    conflicting_sources: Optional[List[str]] = Field(default=None, description="Which sources have conflicting information (audio/slides/notes)")
    context: Optional[str] = Field(default=None, description="Context about why the question is being asked")


class DoneInput(BaseModel):
    """Input for done tool."""
    summary: Optional[str] = Field(default=None, description="Summary of how the three sources were integrated")
    sources_used: Optional[List[str]] = Field(default=None, description="Which sources contributed to the final content")


class WriteContentTool(BaseTool):
    """Tool to write integrated content from multiple sources to the document."""
    
    name: str = "write_content"
    description: str = """Write integrated content that combines information from audio transcription, 
    slide text, and student notes into a coherent section of the document. Returns information for 
    updating both the state and the notes file."""
    args_schema: type[WriteContentInput] = WriteContentInput
    
    def _run(self, integrated_content: str, section_id: Optional[str] = None, position: str = "append") -> str:
        """Write integrated content to the document.
        
        Returns a JSON string with the state update information that the workflow can use
        to update both final_notes dict and write to notes.md file.
        """
        # Since tools can't directly access state, we return instructions for the workflow
        result = {
            "action": "write_content",
            "section_id": section_id,
            "content": integrated_content,
            "position": position,
            "instructions": "Update final_notes dict and write to notes.md file"
        }
        
        # Return a structured response that the workflow can parse
        return json.dumps(result, indent=2)


class EnhanceContentTool(BaseTool):
    """Tool to enhance content with images, diagrams, code, or schemas."""
    
    name: str = "enhance_content"
    description: str = """Add visual enhancements to content such as images, diagrams, code examples, or schemas 
    to help illustrate and clarify the learning material."""
    args_schema: type[EnhanceContentInput] = EnhanceContentInput
    
    def _run(self, section_id: str, enhancement_type: str, description: str) -> str:
        """Add enhancements to content."""
        # This is a placeholder implementation
        # In a real implementation, this would generate or add the requested enhancement
        
        return f"Added {enhancement_type} enhancement to section '{section_id}': {description}"


class QuestionTool(BaseTool):
    """Tool to ask the user questions when sources conflict or information is unclear."""
    
    name: str = "question"
    description: str = """Ask the user questions when there are conflicts between audio transcription, 
    slide text, and student notes, or when information is unclear or ambiguous."""
    args_schema: type[QuestionInput] = QuestionInput
    
    def _run(self, question: str, conflicting_sources: Optional[List[str]] = None, context: Optional[str] = None) -> str:
        """Ask user a question about conflicting or unclear information."""
        # This is a placeholder implementation
        # In a real implementation, this would interface with the user interaction system
        
        result = f"QUESTION: {question}"
        
        if conflicting_sources:
            result += f"\nCONFLICTING SOURCES: {', '.join(conflicting_sources)}"
        
        if context:
            result += f"\nCONTEXT: {context}"
        
        return result


class DoneTool(BaseTool):
    """Tool to indicate that integration of three sources is complete."""
    
    name: str = "done"
    description: str = """Indicate that the current set of three inputs (audio transcription, slide text, 
    and student notes) has been successfully integrated into the document."""
    args_schema: type[DoneInput] = DoneInput
    
    def _run(self, summary: Optional[str] = None, sources_used: Optional[List[str]] = None) -> str:
        """Mark current three-source integration as done."""
        result = "DONE: Three-source integration completed successfully."
        
        if summary:
            result += f"\nSUMMARY: {summary}"
        
        if sources_used:
            result += f"\nSOURCES INTEGRATED: {', '.join(sources_used)}"
        
        return result


# Tool instances
write_content = WriteContentTool()
enhance_content = EnhanceContentTool()
question = QuestionTool()
done = DoneTool()
