import os
import json
import logging
from pydantic import BaseModel, Field
from typing import Literal, Dict, Annotated, Any
from langchain.tools import tool, InjectedToolArg
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, ToolMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langgraph.types import interrupt, Command 

from learning_assistant.prompts import content_system_prompt, agent_system_prompt, default_background, default_content_preferences, content_user_prompt, content_user_additional_prompt, tools_prompt, MEMORY_UPDATE_INSTRUCTIONS
from learning_assistant.state import MessagesState
from document import Document
from dotenv import load_dotenv

#-----------------------
# SETUP AND LOGGING
#-----------------------

logging.basicConfig(
    level=logging.DEBUG, # Change to logging.DEBUG to see the raw LLM messages later
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("LearningAssistantAgent")

load_dotenv(".env")

#-----------------------
# STRUCTURING
#-----------------------

class UserPreferences(BaseModel):
    """Updated user preferences based on user's feedback."""
    chain_of_thought: str = Field(description="Reasoning about which user preferences need to add / update if required")
    user_preferences: str = Field(description="Updated user preferences")

#-----------------------
# MODEL INSTANTIATION
#-----------------------

agent_model_name = os.getenv("AGENT_MODEL_NAME", "openai:gpt-4.1")
compiling_model_name = os.getenv("COMPILING_MODEL", "openai:gpt-4.1")
memory_model_name = os.getenv("MEMORY_MODEL", "openai:gpt-4.1")

agent_model = init_chat_model(
    agent_model_name,
    temperature=0.0
)

compiling_model = init_chat_model(
    compiling_model_name,
    temperature=0.0
)

memory_model = init_chat_model(
    compiling_model_name,
    temperature=0.0
)

#-----------------------
# DOCUMENT REGISTER
#-----------------------
DOCUMENT_STORAGE: Dict[str, Document] = {}

#-----------------------
# TOOL DEFINITION
#-----------------------

@tool
async def ask_question(question: str):
    """ This tool asks a question to the user about the content of the paragraph just submitted.

    # WHEN TO USE:
    - The sources do not agree or are in contrast on a concept (i.e. the notes say the variables are correlated but the OCR says that they are not)
    - The sources present incomplete or missing data (i.e. the notes data says that "the solution to the problem is" and we cannot find the completion in the OCR or in the audio transcription)

    # DO NOT USE:
    - If the notes are empty (use the data from OCR and audio)
    - If the solution to the conflict can be found in one of the other sources

    # ARGS:
        question: the question to ask the user

    # RETURNS:
        A dict with the success status and the response of the user
    """

    pass # Logic handled in the interrupt

@tool
async def create_paragraph(doc_id: str, par_id: str, store: Annotated[BaseStore, InjectedToolArg]):
    """
    This tool combines the audio, OCR and user notes payload into a final polished paragraph

    # WHEN TO USE:
    - If the content of the payload is already coherent and doesn't require clarifications

    # ARGS:
    - par_id: the paragraph id of the paragraph to process.

    # RETURNS:
    A dict with the status of the operation and the finalized paragraph
    """
    doc_ref = DOCUMENT_STORAGE.get(doc_id)
    if not doc_ref:
        return {"success": False, "error": f"Document {doc_id} not found"}
    
    par_ref = doc_ref.get_paragraph(par_id)
    if not par_ref.get("success", False):
        return {"success": False, "error": f"Paragraph {par_id} not found"}
    
    # 1. Fetch the Compiler's specific memory profile
    existing_item = store.get(("learning_assistant", "compiler_profile"), "user_preferences")
    compiler_memory = existing_item.value if existing_item else default_content_preferences

    # 2. Construct the System Message for the Compiler
    system_msg = SystemMessage(
        content=content_system_prompt.format(
            background=default_background,
            content_preferences=compiler_memory
        )
    )
    
    # 3. Construct the User Message (using your existing logic)
    if par_ref.get("additional"):
        user_msg = HumanMessage(content=content_user_additional_prompt.format(
            audio_transcription=par_ref.get("audio", ""),
            ocr_text=par_ref.get("ocr", ""),
            student_notes=par_ref.get("notes", ""),
            additional_notes=par_ref.get("additional")
        ))
    else:
        user_msg = HumanMessage(content=content_user_prompt.format(
            audio_transcription=par_ref.get("audio", ""),
            ocr_text=par_ref.get("ocr", ""),
            student_notes=par_ref.get("notes", "")
        ))

    # 4. Invoke the compiling model with BOTH messages!
    produced_output = await compiling_model.ainvoke([system_msg, user_msg])

    if not produced_output:
        return {"success": False, "content": "Failed execution of compiling model"}

    # Save the finalized text to the Document storage
    doc_ref.replace_paragraph(par_id, produced_output.content)

    logger.info(f"Compiling Model: Successfully generated and saved paragraph {par_id} for doc {doc_id}.")
    logger.debug(f"Generated text: {produced_output.content}")
    
    return {"success": True, "content": produced_output.content}

@tool
async def extract_image(doc_id: str, par_id: str, image: Any):
    """
    This tool extracts an image from a screenshot of the current media being read alongside the notes and inserts it into
    the par_id

    # WHEN TO USE:
    - When a paragraph is complex and its understainding could be helped with the insertion of an image
    - When the media actually contains an image

    # ARGS:
    - par_id: the id of the paragraph where to insert the image
    - image: the screenshot of the OCR that we want to process

    # RETURNS:
    A dict containing the status of the output and a description of the image just inserted
    """

# Augment the LLM with tools
tools = [ask_question, create_paragraph] # add extract_image
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = agent_model.bind_tools(tools)

#-----------------------
# MEMORY UPDATE
#-----------------------

def update_memory(store: BaseStore, namespace: tuple, messages: list):
    """Update memory profile in the store."""

    logger.info(f"Updating memory profile for {namespace}...")
    
    # 1. Get the existing memory from the store
    existing_item = store.get(namespace, "user_preferences")
    # Handle the case where the profile doesn't exist yet
    current_profile = existing_item.value if existing_item else "No preferences yet."

    # 2. Use the dedicated memory model to parse the update
    llm = memory_model.with_structured_output(UserPreferences)
    
    # 3. Invoke the LLM with the specific memory instructions
    result = llm.invoke(
        [
            {"role": "system", "content": MEMORY_UPDATE_INSTRUCTIONS.format(current_profile=current_profile)},
        ] + messages
    )
    
    # 4. Save the updated memory back to the store
    store.put(namespace, "user_preferences", result.user_preferences)
    logger.info(f"Memory successfully updated: {result.user_preferences}")

#-----------------------
# LLM INVOKE
#-----------------------

def llm_call(state: MessagesState, store: BaseStore):
    """LLM decides whether to call a tool or not"""
    logger.info("Agent Model: Evaluating current state...")
    
    # 1. Fetch the Agent's specific memory profile
    existing_item = store.get(("learning_assistant", "agent_profile"), "user_preferences")
    
    # Fallback to a default if it's the very first run
    agent_memory = existing_item.value if existing_item else "- Reference and build upon previously covered topics from all sources.\n- Use ask_question for clarification."

    logger.debug(f"Loaded Agent Memory: {agent_memory}")

    # 2. Inject it into the System Prompt
    system_msg = SystemMessage(
        content=agent_system_prompt.format(
            tools_prompt=tools_prompt,
            agent_memory=agent_memory
        )
    )
    
    response = model_with_tools.invoke([system_msg] + state["messages"])

    if response.tool_calls:
        tool_names = [tc['name'] for tc in response.tool_calls]
        logger.info(f"Agent Model requested tools: {tool_names}")
    else:
        logger.info("Agent Model finished execution. No tools requested.")
    
    return {
        "messages": [response],
        "llm_calls": state.get('llm_calls', 0) + 1
    }

#-----------------------
# INTERRUPT HANDLER
#-----------------------

async def interrupt_handler(state: MessagesState, store: BaseStore) -> Command[Literal["llm_call", "__end__"]]:
    """Dynamically suspends execution ONLY for human clarification questions."""
    result = []
    goto = "llm_call"

    ai_message = state["messages"][-1]

    for tool_call in ai_message.tool_calls:
        
        # 1. AUTO-EXECUTE NON-HITL TOOLS
        if tool_call["name"] in ["extract_image", "create_paragraph"]:
            logger.info(f"Auto-executing tool: {tool_call['name']}")
            tool = tools_by_name[tool_call["name"]]
            
            # Safely inject the 'store' argument if the tool needs it
            args = tool_call["args"].copy()
            if tool_call["name"] == "create_paragraph":
                args["store"] = store 
            
            observation = await tool.ainvoke(args) 
            result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
            continue
            
        # 2. THE HITL TOOL (ask_question)
        if tool_call["name"] == "ask_question":
            question_asked = tool_call["args"].get("question")
            logger.warning(f"HITL TRIGGERED: Pausing graph to ask user: '{question_asked}'")
            request = {
                "action": "ask_question",
                "question": tool_call["args"].get("question"),
                "doc_id": state.get("doc_id"),
                "par_id": state.get("par_id")
            }

            # PAUSE EXECUTION: Send question to FastAPI/React and wait!
            response = interrupt(request)
            logger.info(f"HITL RESUMED: Received action type '{response.get('type')}' from UI.")

            # 3. HANDLE THE USER'S ANSWER
            if response["type"] == "response":
                user_answer = response["args"]
                # Create the exact dictionary you requested for debugging
                debug_return_dict = {
                    "success": True, 
                    "response": user_answer
                }
                
                # Feed the JSON dictionary back to the LLM as the tool's output
                result.append(ToolMessage(
                    content=json.dumps(debug_return_dict), 
                    tool_call_id=tool_call["id"]
                ))
                
                # Trigger the Memory Update!
                memory_context = f"The agent asked: '{question_asked}'. The user answered: '{user_answer}'"
                
                update_memory(
                    store, 
                    ("learning_assistant", "agent_profile"),
                    [{"role": "user", "content": memory_context}]
                )

                # --- INJECT INTO THE DOCUMENT PAYLOAD ---
                doc_id = state.get("doc_id")
                par_id = state.get("par_id")
                
                if doc_id and par_id:
                    doc_ref = DOCUMENT_STORAGE.get(doc_id)
                    if doc_ref and par_id in doc_ref.paragraphs:
                        # Format the resolution cleanly for the compiling model
                        resolution_note = f"Important context from user: regarding '{question_asked}', the answer is '{user_answer}'."

                        res = doc_ref.add_additional_note(par_id, resolution_note)
                        if not res.get("success", False):
                            logger.error(f"❌ Failed to add resolution note to paragraph {par_id}: {res.get('error', 'Unknown error')}")
                        else:
                            logger.info(f"✅ User resolution injected into Document {doc_id}, Paragraph {par_id}.")
                
            elif response["type"] == "ignore":
                logger.warning("User ignored the question. Instructing agent to proceed blindly.")
                msg = "User ignored the question. Do your best to proceed without this information."
                result.append(ToolMessage(content=msg, tool_call_id=tool_call["id"]))

    return Command(goto=goto, update={"messages": result})

#-----------------------
# SHOULD CONTINUE
#-----------------------

def should_continue(state: MessagesState) -> Literal["interrupt_handler", "__end__"]:
    """Route to the handler if tools are called, otherwise end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "interrupt_handler"
    return END

#-----------------------
# COMPILE AGENT + ADD HITL
#-----------------------
# We add a checkpointer to save the state between API calls
memory_saver = MemorySaver() # Single thread memory
in_memory_store = InMemoryStore() #Cross-thread memory
# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("interrupt_handler", interrupt_handler)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {"interrupt_handler": "interrupt_handler", END: END}
)
agent_builder.add_edge("interrupt_handler", "llm_call")

# Compile the agent
agent = agent_builder.compile(
    checkpointer=memory_saver, 
    store=in_memory_store
) 

# Save graph image to disk instead of IPython display
with open("../../img/agent_graph.png", "wb") as f:
    f.write(agent.get_graph(xray=True).draw_mermaid_png())
logger.info("Agent graph visualization saved to 'agent_graph.png'.")