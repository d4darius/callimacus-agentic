from typing import Literal
import os
import json

from langchain.chat_models import init_chat_model

from learning_assistant.tools import get_tools, get_tools_by_name
from learning_assistant.tools.default.learning_tools import write_notes_to_file, generate_section_id
from learning_assistant.tools.default.prompt_templates import STANDARD_TOOLS_PROMPT
from learning_assistant.prompts import triage_system_prompt, triage_user_prompt, content_system_prompt, default_background, default_triage_instructions, triage_instructions, default_content_preferences, default_enhancement_preferences, default_organization_preferences
from learning_assistant.schemas import State, RouterSchema, StateInput
from learning_assistant.utils import parse_content_input, format_current_data, format_content_markdown, format_final_notes, show_graph, append_paragraph
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from dotenv import load_dotenv

load_dotenv(".env")

# Get tools
tools = get_tools()
tools_by_name = get_tools_by_name(tools)

# ROUTER LLM
llm = init_chat_model("openai:gpt-4.1", temperature=0.0)
llm_router = llm.with_structured_output(RouterSchema) 

# AGENT LLM: Initialize the LLM, enforcing tool use (of any available tools) for agent
llm = init_chat_model("openai:gpt-4.1", temperature=0.0)
llm_with_tools = llm.bind_tools(tools, tool_choice="any")

# Document creation: the document is a dictionary with each section_id associated with the final markdown content
final_notes = dict

# --------------------
#  GRAPH NODES SECTION
# --------------------

# Nodes
def llm_call(state: State):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            llm_with_tools.invoke(
                [
                    {"role": "system", "content": content_system_prompt.format(
                        tools_prompt=STANDARD_TOOLS_PROMPT,
                        background=default_background,
                        content_preferences=default_content_preferences, 
                        enhancement_preferences=default_enhancement_preferences,
                        organization_preferences=default_organization_preferences)
                    },
                    
                ]
                + state["messages"]
            )
        ]
    }

def tool_node(state: State):
    """Performs the tool call and handles state updates for WriteContentTool"""
    
    result = []
    
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})
    
    # Return messages and any state updates
    response = {"messages": result}
    return response

# Conditional edge function
def should_continue(state: State) -> Literal["tool_node", "__end__"]:
    """Route to tool_node, or end if done tool called"""
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls: 
            if tool_call["name"] == "done":
                return END
            else:
                return "tool_node"
            
# --------------
# AGENT WORKFLOW
# --------------
agent_builder = StateGraph(State)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        # Name returned by should_continue : Name of next node to visit
        "tool_node": "tool_node",
        END: END,
    },
)
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()

# ---------------
# ROUTER WORKFLOW
# ---------------
def triage_router(state: State) -> Command[Literal["content_agent", "__end__"]]:
    """Analyze sentence data to decide if we should continue, resume, or create a new thread.

    The triage system helps to avoid unnecessary processing:
    - Incomplete audio transcription paragraphs
    - Incomplete slide content
    - Incomplete student notes
    The goal is to reduce the number of llm calls for the final merge
    """
    # Parse the new incoming content
    audio_transcription, documentation, student_notes = parse_content_input(state["content_input"])
    current_paragraph = state["current_paragraph"]

    # Get the document_thread directly from content_input - this contains accumulated paragraph data
    document_thread = state["content_input"].get("document_thread", "")
    
    # Handle missing or empty final_notes
    final_notes = state.get("final_notes", {})
    full_document = format_final_notes(final_notes) if final_notes else ""
    
    system_prompt = triage_system_prompt.format(
        background=default_background,
        triage_instructions=default_triage_instructions
    )

    current_data = format_current_data(current_paragraph)

    user_prompt = triage_user_prompt.format(
        audio_transcription=audio_transcription,
        slide_text=documentation,
        student_notes=student_notes,
        current_data=current_data,
        full_document=full_document
    )

    # Run the router LLM
    result = llm_router.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    # Decision
    classification = result.classification

    if classification == "continue":
        print("➡️ Classification: CONTINUE - This text needs to be appended to the current paragraph data")
        # Use the function to update current_paragraph
        updated_paragraph = append_paragraph(
            current_paragraph,
            audio_transcription=audio_transcription,
            documentation=documentation,
            student_notes=student_notes
        )

        update = {
            "classification_decision": result.classification,
            "current_paragraph": updated_paragraph,
        }
        goto = END
    elif result.classification == "ignore":
        print("🚫 Classification: IGNORE - We have to ignore the current data")
        update =  {
            "classification_decision": result.classification,
        }
        goto = END
    elif result.classification == "new":
        print("⚡️ Classification: NEW - We have to create a new paragraph in the document thread")
        goto = "content_agent"
        
        # Format the current paragraph data to markdown for the content agent
        paragraph_data = format_content_markdown(current_paragraph, full_document)
        
        update = {
            "classification_decision": result.classification,
            "messages": [{"role": "user",
                            "content": f"Create a new paragraph from the following paragraph data: {paragraph_data} with id {result.paragraph_id}."
                        }],
            # Initialize current_paragraph with the new incoming content for next accumulation cycle
            "current_paragraph": {
                "audio_transcription": audio_transcription,
                "documentation": documentation,
                "student_notes": student_notes
            }
        }
    else:
        raise ValueError(f"Invalid classification: {result.classification}")
    return Command(goto=goto, update=update)

# ----------------
# OVERALL WORKFLOW
# ----------------

# Rebuild the workflow to ensure updated functions are used
overall_workflow = (
    StateGraph(State, input=StateInput)
    .add_node("triage_router", triage_router)  # Explicitly pass the updated function
    .add_node("content_agent", agent)
    .add_edge(START, "triage_router")
)

learning_assistant = overall_workflow.compile()
print("✓ Learning assistant workflow recompiled with updated triage router")