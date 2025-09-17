"""Tool prompt templates for the learning assistant."""

# Standard tool descriptions for insertion into prompts
STANDARD_TOOLS_PROMPT = """
1. write_content(integrated_content, section_id, position) - Write integrated content combining all three sources into the document
2. enhance_content(section_id, enhancement_type, description) - Add visual enhancements like images, diagrams, code, or schemas
3. done(summary, sources_used) - Mark current three-source integration as successfully completed
"""

# Tool descriptions for HITL workflow
HITL_TOOLS_PROMPT = """
1. write_content(integrated_content, section_id, position) - Write integrated content combining all three sources into the document
2. enhance_content(section_id, enhancement_type, description) - Add visual enhancements like images, diagrams, code, or schemas
3. question(question, conflicting_sources, context) - Ask the user questions when sources conflict or information is unclear
4. done(summary, sources_used) - Mark current three-source integration as successfully completed
"""

# Tool descriptions for HITL with memory workflow
HITL_MEMORY_TOOLS_PROMPT = """
1. write_content(integrated_content, section_id, position) - Write integrated content combining all three sources into the document
2. enhance_content(section_id, enhancement_type, description) - Add visual enhancements like images, diagrams, code, or schemas
3. question(question, conflicting_sources, context) - Ask the user questions when sources conflict or information is unclear
4. done(summary, sources_used) - Mark current three-source integration as successfully completed
"""