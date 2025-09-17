from typing import Literal
import os
import json

from langchain.chat_models import init_chat_model

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command

from learning_assistant.tools import get_tools, get_tools_by_name
from learning_assistant.tools.default.learning_tools import write_notes_to_file, generate_section_id
from learning_assistant.tools.default.prompt_templates import HITL_TOOLS_PROMPT
from learning_assistant.tools.default.learning_tools import write_notes_to_file, generate_section_id
from learning_assistant.prompts import triage_system_prompt, triage_user_prompt, content_system_prompt, default_background, default_triage_instructions, triage_instructions, default_content_preferences, default_enhancement_preferences, default_organization_preferences
from learning_assistant.schemas import State, RouterSchema, StateInput
from learning_assistant.utils import parse_content_input, format_current_data, format_content_markdown, format_final_notes, format_paragraph_input, format_for_display, append_paragraph
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
                        tools_prompt=HITL_TOOLS_PROMPT,
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

def interrupt_handler(state: State) -> Command[Literal["llm_call", "__end__"]]:
    """Creates an interrupt for human review of tool calls"""
    
    # Store messages
    result = []

    # Go to the LLM call node next
    goto = "llm_call"

    # Iterate over the tool calls in the last message
    for tool_call in state["messages"][-1].tool_calls:
        
        # Allowed tools for HITL
        hitl_tools = ["write_content", "question"]
        
        # If tool is not in our HITL list, execute it directly without interruption
        if tool_call["name"] not in hitl_tools:

            # Execute tool without interruption
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"], final_notes=state.get("final_notes", {}))
            result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})
            continue
            
        # Get original content from content_input in state
        content_input = state["content_input"]
        current_notes = state.get("final_notes", {})
        audio_transcription, documentation, student_notes = parse_content_input(content_input)
        final_document = format_final_notes(current_notes) if current_notes else ""
        input_data_markdown = format_paragraph_input(audio_transcription, documentation, student_notes, final_document)

        # Format tool call for display and prepend the original email
        tool_display = format_for_display(tool_call)
        description = input_data_markdown + tool_display

        # Configure what actions are allowed in Agent Inbox
        if tool_call["name"] == "write_content":
            config = {
                "allow_ignore": True,
                "allow_respond": True,
                "allow_edit": True,
                "allow_accept": True,
            }
        elif tool_call["name"] == "question":
            config = {
                "allow_ignore": True,
                "allow_respond": True,
                "allow_edit": False,
                "allow_accept": False,
            }
        else:
            raise ValueError(f"Invalid tool call: {tool_call['name']}")

        # Create the interrupt request
        request = {
            "action_request": {
                "action": tool_call["name"],
                "args": tool_call["args"]
            },
            "config": config,
            "description": description,
        }

        # Send to Agent Inbox and wait for response
        response = interrupt([request])[0]

        # Handle the responses 
        if response["type"] == "accept":

            # Execute the tool with original args
            tool = tools_by_name[tool_call["name"]]
            args = tool_call["args"].copy()
            args["final_notes"] = state.get("final_notes", {})
            observation = tool.invoke(args)
            # Update the final notes in state if returned by the tool
            try:
                obs_data = json.loads(observation)
                if "final_notes" in obs_data:
                    state["final_notes"] = obs_data["final_notes"]
            except Exception:
                pass
            result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})
                        
        elif response["type"] == "edit":

            # Tool selection 
            tool = tools_by_name[tool_call["name"]]
            
            # Get edited args from Agent Inbox
            edited_args = response["args"]["args"]

            # Update the AI message's tool call with edited content (reference to the message in the state)
            ai_message = state["messages"][-1] # Get the most recent message from the state
            current_id = tool_call["id"] # Store the ID of the tool call being edited
            
            # Create a new list of tool calls by filtering out the one being edited and adding the updated version
            # This avoids modifying the original list directly (immutable approach)
            updated_tool_calls = [tc for tc in ai_message.tool_calls if tc["id"] != current_id] + [
                {"type": "tool_call", "name": tool_call["name"], "args": edited_args, "id": current_id}
            ]
            
            # Create a new copy of the message with updated tool calls rather than modifying the original
            # This ensures state immutability and prevents side effects in other parts of the code
            # When we update the messages state key ("messages": result), the add_messages reducer will
            # overwrite existing messages by id and we take advantage of this here to update the tool calls.
            result.append(ai_message.model_copy(update={"tool_calls": updated_tool_calls}))

            # Update the write_content tool call with the edited content from Agent Inbox
            if tool_call["name"] == "write_content":

                # Execute the tool with edited args
                edited_args["final_notes"] = state.get("final_notes", {})
                observation = tool.invoke(edited_args)
                # Update the final notes in state if returned by the tool
                try:
                    obs_data = json.loads(observation)
                    if "final_notes" in obs_data:
                        state["final_notes"] = obs_data["final_notes"]
                except Exception:
                    pass

                # Add only the tool response message
                result.append({"role": "tool", "content": observation, "tool_call_id": current_id})
            
            # Catch all other tool calls
            else:
                raise ValueError(f"Invalid tool call: {tool_call['name']}")

        elif response["type"] == "ignore":
            if tool_call["name"] == "write_content":
                # Don't execute the tool, and tell the agent how to proceed
                result.append({"role": "tool", "content": "User ignored this content draft. Delete this content and end the workflow.", "tool_call_id": tool_call["id"]})
                # Go to END
                goto = END
            elif tool_call["name"] == "question":
                # Don't execute the tool, and tell the agent how to proceed
                result.append({"role": "tool", "content": "User ignored this question. Delete this content and end the workflow.", "tool_call_id": tool_call["id"]})
                # Go to END
                goto = END
            else:
                raise ValueError(f"Invalid tool call: {tool_call['name']}")
            
        elif response["type"] == "response":
            # User provided feedback
            user_feedback = response["args"]
            if tool_call["name"] == "write_content":
                # Don't execute the tool, and add a message with the user feedback to incorporate into the content
                result.append({"role": "tool", "content": f"User gave feedback, which can we incorporate into the content. Feedback: {user_feedback}", "tool_call_id": tool_call["id"]})
            elif tool_call["name"] == "question":
                # Don't execute the tool, and add a message with the user feedback to incorporate into the email
                result.append({"role": "tool", "content": f"User answered the question, which can we can use for any follow up actions. Feedback: {user_feedback}", "tool_call_id": tool_call["id"]})
            else:
                raise ValueError(f"Invalid tool call: {tool_call['name']}")

        # Catch all other responses
        else:
            raise ValueError(f"Invalid response: {response}")  
    # Update the state 
    update = {
        "messages": result,
    }

    return Command(goto=goto, update=update)


# Conditional edge function
def should_continue(state: State) -> Literal["interrupt_handler", "__end__"]:
    """Route to the handler, or end if done tool called"""
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls: 
            if tool_call["name"] == "done":
                return END
            else:
                return "interrupt_handler"
            
# --------------
# AGENT WORKFLOW
# --------------
agent_builder = StateGraph(State)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("interrupt_handler", interrupt_handler)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        # Name returned by should_continue : Name of next node to visit
        "interrupt_handler": "interrupt_handler",
        END: END,
    },
)
# The arc connecting llm_call to __end__ passes through interrupt_handler

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
    .add_node("triage_router", triage_router)
    .add_node("content_agent", agent)
    .add_edge(START, "triage_router")
)

learning_assistant = overall_workflow.compile()
print("✓ Learning assistant workflow recompiled with human-in-the-loop feature")