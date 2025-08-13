"""Tool prompt templates for the learning assistant."""

# Standard tool descriptions for insertion into prompts
STANDARD_TOOLS_PROMPT = """
1. search_document(audio_transcription, slide_text, student_notes) - Search the document for the best location to integrate content from three sources
2. write_content(integrated_content, section_id, position) - Write integrated content combining all three sources into the document
3. enhance_content(section_id, enhancement_type, description) - Add visual enhancements like images, diagrams, code, or schemas
4. question(question, conflicting_sources, context) - Ask the user questions when sources conflict or information is unclear
5. done(summary, sources_used) - Mark current three-source integration as successfully completed
"""

# Tool descriptions for HITL workflow
HITL_TOOLS_PROMPT = """
1. search_document(audio_transcription, slide_text, student_notes) - Search the document for the best location to integrate content from three sources
2. write_content(integrated_content, section_id, position) - Write integrated content combining all three sources into the document
3. enhance_content(section_id, enhancement_type, description) - Add visual enhancements like images, diagrams, code, or schemas
4. question(question, conflicting_sources, context) - Ask the user questions when sources conflict or information is unclear
5. done(summary, sources_used) - Mark current three-source integration as successfully completed
"""

# Tool descriptions for HITL with memory workflow
HITL_MEMORY_TOOLS_PROMPT = """
1. search_document(audio_transcription, slide_text, student_notes) - Search the document for the best location to integrate content from three sources
2. write_content(integrated_content, section_id, position) - Write integrated content combining all three sources into the document
3. enhance_content(section_id, enhancement_type, description) - Add visual enhancements like images, diagrams, code, or schemas
4. question(question, conflicting_sources, context) - Ask the user questions when sources conflict or information is unclear
5. done(summary, sources_used) - Mark current three-source integration as successfully completed
"""

# Tool descriptions for agent workflow
AGENT_TOOLS_PROMPT = """
1. search_document(audio_transcription, slide_text, student_notes) - Search the document for the best location to integrate content from three sources
2. write_content(integrated_content, section_id, position) - Write integrated content combining all three sources into the document
3. enhance_content(section_id, enhancement_type, description) - Add visual enhancements like images, diagrams, code, or schemas
4. done(summary, sources_used) - Mark current three-source integration as successfully completed
"""

# Detailed tool descriptions for complex workflows
DETAILED_TOOLS_PROMPT = """
Available Tools for Learning Assistant (Three-Source Integration):

1. search_document(audio_transcription, slide_text, student_notes):
   - Purpose: Analyze three simultaneous inputs and find the best document location
   - Parameters:
     * audio_transcription: Audio content from the lesson
     * slide_text: Text extracted from presentation slides  
     * student_notes: Student notes (handwritten or digital)
   - Use when: You have received all three sources and need to determine placement

2. write_content(integrated_content, section_id=None, position="append"):
   - Purpose: Write content that intelligently combines information from all three sources
   - Parameters:
     * integrated_content: The synthesized content combining audio, slides, and notes
     * section_id: ID of the section to write to (None creates new section)
     * position: Where to place content ("append", "prepend", or "replace")
   - Use when: You're ready to add integrated content to the document

3. enhance_content(section_id, enhancement_type, description):
   - Purpose: Add visual enhancements based on information from any of the three sources
   - Parameters:
     * section_id: ID of the section to enhance
     * enhancement_type: Type of enhancement ("image", "diagram", "code", "schema")
     * description: Description of what enhancement is needed
   - Use when: Any source suggests visual aids would improve understanding

4. question(question, conflicting_sources=None, context=None):
   - Purpose: Ask the user when sources conflict or information is unclear
   - Parameters:
     * question: Question to ask the user
     * conflicting_sources: Which sources have conflicting info (["audio", "slides", "notes"])
     * context: Optional context about why the question is being asked
   - Use when: Audio, slides, and notes contradict each other or information is ambiguous

5. done(summary=None, sources_used=None):
   - Purpose: Indicate that integration of all three sources is complete
   - Parameters:
     * summary: Optional summary of how sources were integrated
     * sources_used: Which sources contributed to final content (["audio", "slides", "notes"])
   - Use when: All three sources have been successfully integrated into the document
"""