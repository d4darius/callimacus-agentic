from typing import List, Any, Dict, Optional
import json
import re

def smart_append(existing_text: str, new_text: str) -> str:
    """
    Intelligently append only the new parts of text that aren't already present.
    
    This handles cases where:
    - Slides reveal additional content (append only new parts)
    - Audio transcription continues (append only new sentences)
    - Student notes add new insights (append only new content)
    
    Args:
        existing_text: The current accumulated text
        new_text: The new text that might contain both old and new content
    
    Returns:
        The existing text with only the truly new content appended
    """
    if not existing_text.strip():
        return new_text
    
    if not new_text.strip():
        return existing_text
    
    # Clean and normalize both texts for comparison
    existing_clean = existing_text.strip()
    new_clean = new_text.strip()
    
    # If new text is completely contained in existing, no update needed
    if new_clean in existing_clean:
        return existing_text
    
    # If existing text is completely contained in new, replace with new
    if existing_clean in new_clean:
        return new_text
    
    # Find the longest common suffix of existing with prefix of new
    # This handles cases where new text starts with some overlap
    best_overlap = 0
    best_new_part = new_clean
    
    # Check for overlaps by comparing suffixes of existing with prefixes of new
    for i in range(1, min(len(existing_clean), len(new_clean)) + 1):
        existing_suffix = existing_clean[-i:]
        new_prefix = new_clean[:i]
        
        if existing_suffix.lower() == new_prefix.lower():
            best_overlap = i
            best_new_part = new_clean[i:]
    
    # If we found overlap, append only the non-overlapping part
    if best_overlap > 0 and best_new_part.strip():
        # Add space if needed
        separator = " " if not existing_text.endswith(" ") and not best_new_part.startswith(" ") else ""
        return existing_text + separator + best_new_part
    elif best_overlap > 0:
        # Pure overlap case, no new content
        return existing_text
    else:
        # No overlap found, append with proper spacing
        separator = " " if not existing_text.endswith(" ") and not new_text.startswith(" ") else ""
        return existing_text + separator + new_text
    
def format_current_data(current_paragraph: dict) -> str:
    """Format the current paragraph data into a readable string to input in the triage assistant.
    
    Args:
        current_paragraph: Dictionary containing content fields:
            - audio_transcription: The audio transcription text
            - documentation: The documentation slide content
            - student_notes: The student notes content
    """
    return f"""
    ---------Current Audio Transcription Data---------
    {current_paragraph["audio_transcription"]}

    ---------Current Documentation---------
    {current_paragraph["documentation"]}

    ---------Current Student Notes---------
    {current_paragraph["student_notes"]}

"""

def format_content_markdown(current_paragraph: dict, full_document: str) -> str:
    """Format educational content into a nicely formatted markdown string for display
    
    Args:
        current_paragraph: Dictionary containing content fields:
            - audio_transcription: The audio transcription text
            - slide_text: The slide content text
            - student_notes: The student notes text
        full_document: The document thread text
    """
    return f"""
    ---------- Audio Transcription ----------
    {current_paragraph["audio_transcription"]}

    ---------- Documentation ----------
    {current_paragraph["documentation"]}

    ---------- Student Notes ----------
    {current_paragraph["student_notes"]}

{full_document}

---
"""

def format_paragraph_input(audio_transcription: str, documentation: str, student_notes: str, final_document: str) -> str:
    """Format individual content inputs into a single string.
    
    Args:
        audio_transcription: The audio transcription text
        documentation: The documentation slide content
        student_notes: The student notes content
        final_document: The current state of the full document
        
    Returns:
        A formatted string representing the paragraph content
    """
    return f"""

    **Audio Transcription**
    {audio_transcription}

    **Documentation**
    {documentation}

    **Student Notes**
    {student_notes}

    **Full Document**
    {final_document}

---
"""

def format_document_section(section_id: str, title: str, content: str, level: int = 1) -> str:
    """Format a document section with proper markdown hierarchy
    
    Args:
        section_id: Unique identifier for the section
        title: Section title
        content: Section content
        level: Heading level (1-6)
    """
    heading_prefix = "#" * min(level, 6)
    return f"""
{heading_prefix} {title}

{content}

---
"""

def format_for_display(tool_call: Dict[str, Any]) -> str:
    """Format content for display in Learning Assistant interface
    
    Args:
        tool_call: The tool call to format
    """
    display = ""

    if tool_call["name"] == "write_content":
        section_info = f"**Section**: {tool_call['args']['section_id']}\n"
        
        display += f"""# Content Integration

{section_info}**Position**: {tool_call["args"].get("position", "append")}

**Content**:
{tool_call["args"].get("content")}
"""
    elif tool_call["name"] == "enhance_content":
        display += f"""# Content Enhancement

**Section**: {tool_call["args"].get("section_id")}
**Enhancement Type**: {tool_call["args"].get("enhancement_type")}
**Description**: {tool_call["args"].get("description")}

Adding visual enhancement to improve understanding...
"""
    elif tool_call["name"] == "question":
        context_info = ""
        if tool_call["args"].get("context"):
            context_info = f"\n**Context**: {tool_call['args']['context']}\n"
        
        display += f"""# Question for User

{tool_call["args"].get("question")}{context_info}
"""
    elif tool_call["name"] in ["done", "Done"]:
        summary_info = ""
        if tool_call["args"] and tool_call["args"].get("summary"):
            summary_info = f"\n\n**Summary**: {tool_call['args']['summary']}"
        
        display += f"""# Task Complete

Current input has been successfully processed and integrated.{summary_info}
"""
    else:
        # Generic format for other tools
        display += f"""# Tool Call: {tool_call["name"]}

Arguments:"""
        
        if isinstance(tool_call["args"], dict):
            display += f"\n{json.dumps(tool_call['args'], indent=2)}\n"
        else:
            display += f"\n{tool_call['args']}\n"
    
    return display

def parse_content_input(content_input: dict) -> tuple[str, str, str, dict]:
    """Parse a content input dictionary.

    Args:
        content_input (dict): Dictionary containing content fields:
            - audio_transcription: The audio transcription text
            - documentation: The documentation slide content
            - student_notes: The student notes content
            - document_thread: current paragraph data (not used here, managed by state)

    Returns:
        tuple[str, str, str]: Tuple containing:
            - audio_transcription: The audio transcription text
            - documentation: The documentation slide content
            - student_notes: The student notes content
    """
    return (
        content_input["audio_transcription"],
        content_input["documentation"],
        content_input["student_notes"],
        content_input["current_paragraph"],
        content_input["document_thread"]
    )

def format_final_notes(notes: dict) -> dict:
    """Format the final notes for each section."""
    formatted_text = ""
    for section_id in sorted(notes.keys()):
        formatted_text += f"Section {section_id}:\n\n{notes[section_id]}\n"
    return formatted_text

def extract_key_concepts(content: str) -> List[str]:
    """Extract key concepts and terms from educational content.
    
    Args:
        content: The educational content to analyze
        
    Returns:
        List of identified key concepts
    """
    # Simple keyword extraction - in practice, this could use NLP
    # Look for capitalized terms, technical terms, etc.
    key_concepts = []
    
    # Find words that are likely concepts (capitalized, technical terms)
    concept_patterns = [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized phrases
        r'\b\w+(?:ology|ism|tion|ment|ness)\b',  # Technical suffixes
        r'\b(?:algorithm|method|process|system|framework|model|theory)\b'  # Common academic terms
    ]
    
    for pattern in concept_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        key_concepts.extend(matches)
    
    # Remove duplicates and return
    return list(set(key_concepts))

def create_content_summary(content: str, max_length: int = 200) -> str:
    """Create a summary of content for indexing and search.
    
    Args:
        content: The content to summarize
        max_length: Maximum length of the summary
        
    Returns:
        A summary of the content
    """
    # Simple summarization - truncate to key sentences
    sentences = content.split('.')
    summary = ""
    
    for sentence in sentences:
        if len(summary + sentence) <= max_length:
            summary += sentence + "."
        else:
            break
    
    return summary.strip()

def detect_content_relationships(new_content: str, existing_sections: List[Dict[str, str]]) -> List[tuple[str, float]]:
    """Detect relationships between new content and existing document sections.
    
    Args:
        new_content: The new content to analyze
        existing_sections: List of existing sections with 'id', 'title', 'content'
        
    Returns:
        List of tuples (section_id, similarity_score) sorted by relevance
    """
    # Simple similarity based on shared keywords
    new_concepts = set(extract_key_concepts(new_content))
    relationships = []
    
    for section in existing_sections:
        section_concepts = set(extract_key_concepts(section.get('content', '')))
        
        # Calculate simple overlap similarity
        if new_concepts and section_concepts:
            overlap = len(new_concepts.intersection(section_concepts))
            similarity = overlap / len(new_concepts.union(section_concepts))
            relationships.append((section.get('id', ''), similarity))
    
    # Sort by similarity score (highest first)
    relationships.sort(key=lambda x: x[1], reverse=True)
    return relationships

def extract_message_content(message) -> str:
    """Extract content from different message types as clean string.
    
    Args:
        message: A message object (HumanMessage, AIMessage, ToolMessage)
        
    Returns:
        str: Extracted content as clean string
    """
    content = message.content
    
    # Check for recursion marker in string
    if isinstance(content, str) and '<Recursion on AIMessage with id=' in content:
        return "[Recursive content]"
    
    # Handle string content
    if isinstance(content, str):
        return content
        
    # Handle list content (AIMessage format)
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and 'text' in item:
                text_parts.append(item['text'])
        return "\n".join(text_parts)
    
    return str(content)

def extract_tool_calls(messages: List[Any]) -> List[str]:
    """Extract tool call names from messages, safely handling messages without tool_calls."""
    tool_call_names = []
    for message in messages:
        # Check if message is a dict and has tool_calls
        if isinstance(message, dict) and message.get("tool_calls"):
            tool_call_names.extend([call["name"].lower() for call in message["tool_calls"]])
        # Check if message is an object with tool_calls attribute
        elif hasattr(message, "tool_calls") and message.tool_calls:
            tool_call_names.extend([call["name"].lower() for call in message.tool_calls])
    
    return tool_call_names

def format_messages_string(messages: List[Any]) -> str:
    """Format messages into a single string for analysis."""
    return '\n'.join(message.pretty_repr() for message in messages)

def show_graph(graph, xray=False):
    """Display a LangGraph mermaid diagram with fallback rendering.
    
    Handles timeout errors from mermaid.ink by falling back to pyppeteer.
    
    Args:
        graph: The LangGraph object that has a get_graph() method
    """
    from IPython.display import Image
    try:
        # Try the default renderer first
        return Image(graph.get_graph(xray=xray).draw_mermaid_png())
    except Exception as e:
        # Fall back to pyppeteer if the default renderer fails
        import nest_asyncio
        nest_asyncio.apply()
        from langchain_core.runnables.graph import MermaidDrawMethod
        return Image(graph.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.PYPPETEER))
    

def append_paragraph(current_paragraph, audio_transcription=None, documentation=None, student_notes=None):
    """
    Intelligently append new content to the current paragraph using smart_append logic.
    Args:
        current_paragraph: Dictionary with existing paragraph content
        audio_transcription: New audio transcription text to append
        documentation: New documentation slide text to append
        student_notes: New student notes text to append
    Returns:
        Updated paragraph dictionary with new content appended
    """
    updated = current_paragraph.copy()
    if audio_transcription:
        updated["audio_transcription"] = smart_append(current_paragraph.get("audio_transcription", ""), audio_transcription)
    if documentation:
        updated["documentation"] = smart_append(current_paragraph.get("documentation", ""), documentation)
    if student_notes:
        updated["student_notes"] = smart_append(current_paragraph.get("student_notes", ""), student_notes)
    return updated