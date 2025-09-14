#!/usr/bin/env python

import os
import uuid
import importlib
import sys
import pytest
from typing import Dict, List, Any, Tuple
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model

from langsmith import testing as t

from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command

from learning_assistant.utils import extract_tool_calls, format_messages_string
from learning_assistant.eval.prompts import RESPONSE_CRITERIA_SYSTEM_PROMPT

from dotenv import load_dotenv
load_dotenv(".env", override=True)

# Force reload the learning_dataset module to ensure we get the latest version
if "learning_assistant.eval.learning_dataset" in sys.modules:
    importlib.reload(sys.modules["learning_assistant.eval.learning_dataset"])
from learning_assistant.eval.learning_dataset import content_inputs, content_names, write_criteria_list, triage_outputs_list, expected_tool_calls
    
class CriteriaGrade(BaseModel):
    """Score the response against specific criteria."""
    grade: bool = Field(description="Does the response meet the provided criteria?")
    justification: str = Field(description="The justification for the grade and score, including specific examples from the response.")

# Create a global LLM for evaluation to avoid recreating it for each test
criteria_eval_llm = init_chat_model("openai:gpt-4o")
criteria_eval_structured_llm = criteria_eval_llm.with_structured_output(CriteriaGrade)

# Global variables for module name and imported module
AGENT_MODULE = os.environ.get("AGENT_MODULE", "learning_assistant")
agent_module = importlib.import_module(f"learning_assistant.{AGENT_MODULE}")

def setup_assistant() -> Tuple[Any, Dict[str, Any], InMemoryStore]:
    """
    Setup the learning assistant and create thread configuration.
    Returns the assistant, thread config, and store.
    """
    # Set up checkpointer and store
    checkpointer = MemorySaver()
    store = InMemoryStore()
    
    # Create a thread ID and config
    thread_id = uuid.uuid4()
    thread_config = {"configurable": {"thread_id": thread_id}}
    
    # Compile the graph based on module type
    if AGENT_MODULE == "learning_assistant_hitl_memory":
        # Memory implementation needs a store and a checkpointer
        learning_assistant = agent_module.overall_workflow.compile(checkpointer=checkpointer, store=store)
    elif AGENT_MODULE in ["learning_assistant_hitl"]:
        # Just use a checkpointer for HITL version
        learning_assistant = agent_module.overall_workflow.compile(checkpointer=checkpointer)
    else:
        # Just use a checkpointer for other versions
        learning_assistant = agent_module.overall_workflow.compile(checkpointer=checkpointer)
        store = None

    return learning_assistant, thread_config, store

def extract_values(state: Any) -> Dict[str, Any]:
    """Extract values from state object regardless of type."""
    if hasattr(state, "values"):
        return state.values
    else:
        return state

def run_initial_stream(learning_assistant: Any, content_input: Dict, thread_config: Dict) -> List[Dict]:
    """Run the initial stream and return collected messages."""
    messages = []
    for chunk in learning_assistant.stream({"content_input": content_input}, config=thread_config):
            messages.append(chunk)
    return messages

def run_stream_with_command(learning_assistant: Any, command: Command, thread_config: Dict) -> List[Dict]:
    """Run stream with a command and return collected messages."""
    messages = []
    for chunk in learning_assistant.stream(command, config=thread_config):
            messages.append(chunk)
    return messages

def is_module_compatible(required_modules: List[str]) -> bool:
    """Check if current module is compatible with test.
    
    Returns:
        bool: True if module is compatible, False otherwise
    """
    return AGENT_MODULE in required_modules

def create_response_test_cases():
    """Create test cases for parametrized criteria evaluation with LangSmith.
    Only includes input data that require creating a new paragraph (triage_output == "new").
    These are more relevant / interesting for testing tool calling / response quality. 
    """

    # Create tuples of (content_input, content_name, criteria) for parametrization
    # Only include emails that require a response (triage_output == "respond")
    test_cases = []
    for i, (content_input, content_name, criteria, triage_output, expected_calls) in enumerate(zip(
        content_inputs, content_names, write_criteria_list, triage_outputs_list, expected_tool_calls
    )):
        if triage_output == "new":
            # No need to include triage_output since we're filtering for "new" only
            # Each test case is (content_input, content_name, criteria, expected_calls)
            test_cases.append((content_input, content_name, criteria, expected_calls))

    print(f"Created {len(test_cases)} test cases for content requiring new paragraphs")
    return test_cases

# Reference output key
@pytest.mark.langsmith(output_keys=["expected_calls"])
# Variable names and a list of tuples with the test cases
@pytest.mark.parametrize("content_input,content_name,criteria,expected_calls",create_response_test_cases())
def test_email_dataset_tool_calls(content_input, content_name, criteria, expected_calls):
    """Test if input data processing contains expected tool calls."""
    # Log minimal inputs for LangSmith
    t.log_inputs({"module": AGENT_MODULE, "test": "test_learning_dataset_tool_calls"})

    print(f"Processing {content_name}...")

    # Set up the assistant
    learning_assistant, thread_config, _ = setup_assistant()
    
    # Run the agent        
    if AGENT_MODULE == "learning_assistant":
        # Workflow agent takes content_input directly
        result = learning_assistant.invoke({
            "content_input": content_input,
            "current_paragraph": content_input.get("current_paragraph", {
                "audio_transcription": "",
                "documentation": "",
                "student_notes": ""
            }),
            }, config=thread_config)
    else:
        raise ValueError(f"Unsupported agent module: {AGENT_MODULE}. Only 'learning_assistant' is supported in automated testing.")

    # Get the final state
    state = learning_assistant.get_state(thread_config)
    values = extract_values(state)
        
    # Extract tool calls from messages
    extracted_tool_calls = extract_tool_calls(values["messages"])
            
    # Check if all expected tool calls are in the extracted ones
    missing_calls = [call for call in expected_calls if call.lower() not in extracted_tool_calls]
    # Extra calls are allowed (we only fail if expected calls are missing)
    extra_calls = [call for call in extracted_tool_calls if call.lower() not in [c.lower() for c in expected_calls]]
   
    # Log 
    all_messages_str = format_messages_string(values["messages"])
    t.log_outputs({
                "extracted_tool_calls": extracted_tool_calls,
                "missing_calls": missing_calls,
                "extra_calls": extra_calls,
                "response": all_messages_str
            })

    # Pass feedback key
    assert len(missing_calls) == 0
            
# Reference output key
@pytest.mark.langsmith(output_keys=["criteria"])
# Variable names and a list of tuples with the test cases
# Each test case is (content_input, content_name, criteria, expected_calls)
@pytest.mark.parametrize("content_input,content_name,criteria,expected_calls",create_response_test_cases())
def test_response_criteria_evaluation(content_input, content_name, criteria, expected_calls):
    """Test if a response meets the specified criteria.
    Only runs on content data that require a response.
    """
    # Log minimal inputs for LangSmith
    t.log_inputs({"module": AGENT_MODULE, "test": "test_writing_criteria_evaluation"})

    print(f"Processing {content_name}...")
    
    # Set up the assistant
    learning_assistant, thread_config, _ = setup_assistant()

    # Run the agent
    if AGENT_MODULE == "learning_assistant":
        # Workflow agent takes content_input directly
        result = learning_assistant.invoke({
            "content_input": content_input,
            "current_paragraph": content_input.get("current_paragraph", {
                "audio_transcription": "",
                "documentation": "",
                "student_notes": ""
            }),
            }, config=thread_config)
    else:
        raise ValueError(f"Unsupported agent module: {AGENT_MODULE}. Only 'learning_assistant' is supported in automated testing.")
        
    # Get the final state
    state = learning_assistant.get_state(thread_config)
    values = extract_values(state)
    
    # Generate message output string for evaluation
    all_messages_str = format_messages_string(values['messages'])
    
    # Evaluate against criteria
    eval_result = criteria_eval_structured_llm.invoke([
        {"role": "system",
            "content": RESPONSE_CRITERIA_SYSTEM_PROMPT},
        {"role": "user",
            "content": f"""\n\n Response criteria: {criteria} \n\n Assistant's response: \n\n {all_messages_str} \n\n Evaluate whether the assistant's response meets the criteria and provide justification for your evaluation."""}
    ])

    # Log feedback response
    t.log_outputs({
        "justification": eval_result.justification,
        "response": all_messages_str,
    })
        
    # Pass feedback key
    assert eval_result.grade
 
