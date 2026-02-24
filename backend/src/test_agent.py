import asyncio
import uuid
from langchain.messages import HumanMessage
from langgraph.types import Command

# Import your agent, document storage, and Document class
from learning_assistant.learning_assistant import agent, DOCUMENT_STORAGE
from document import Document

async def run_test():
    print("\n" + "="*50)
    print("🚀 STARTING LANGGRAPH AGENT TEST")
    print("="*50 + "\n")

    # 1. Setup Mock Document Storage
    doc_id = "test_doc_001"
    par_id = "test_par_001"
    
    # Initialize the document in our global dictionary
    DOCUMENT_STORAGE[doc_id] = Document("Test Physics Notes")
    
    # Inject conflicting data to force the LLM to use 'ask_question'
    DOCUMENT_STORAGE[doc_id].paragraphs[par_id] = {
        "audio": "we must divide the mass by the volume to get density.",
        "ocr": "Formula on slide: Density = Mass * Volume",
        "notes": "Density is defined as the ratio between volume and mass of an object",
        "additional_notes": ""
    }

    # 2. Setup Thread Config (Required for MemorySaver to work)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # 3. Define the Initial State
    paragraph_data = DOCUMENT_STORAGE[doc_id].paragraphs[par_id]
    
    agent_prompt = f"""
    Please process the following educational inputs. 
    If there is a conflict, use ask_question. If they are coherent, use create_paragraph.
    
    [META DATA]
    doc_id: {doc_id}
    par_id: {par_id}
    
    [SOURCES]
    Audio: {paragraph_data['audio']}
    OCR: {paragraph_data['ocr']}
    Notes: {paragraph_data['notes']}
    """

    initial_state = {
        "messages": [
            HumanMessage(content=agent_prompt)
        ],
        "doc_id": doc_id,
        "par_id": par_id
    }

    print("⏳ Running agent (Waiting for LLM to detect the conflict...)")
    
    # 4. First Run: The agent will run until it hits the interrupt()
    await agent.ainvoke(initial_state, config)

    # 5. Check the Graph State to see if it paused
    state = agent.get_state(config)
    
    # LangGraph v0.2 stores pending interrupts in the state's tasks list
    if state.tasks and state.tasks[0].interrupts:
        print("\n" + "="*50)
        print("🛑 GRAPH PAUSED SUCCESSFULLY")
        print("="*50)
        
        interrupt_payload = state.tasks[0].interrupts[0].value
        print(f"\n[INTERRUPT PAYLOAD FROM AGENT]:\n{interrupt_payload}")
        
        # 6. Simulate the User's Answer from the UI
        print("\n" + "="*50)
        print("▶️ RESUMING GRAPH WITH MOCK USER ANSWER")
        print("="*50 + "\n")
        
        mock_ui_response = {
            "type": "response",
            "args": "The OCR is a typo. The audio is correct, we must divide."
        }
        
        # Resume the graph by passing the Command(resume=...) directly to ainvoke
        await agent.ainvoke(Command(resume=mock_ui_response), config)
    else:
        print("\n⚠️ Graph finished without pausing. (The LLM didn't think it needed to ask a question).")

    # 7. Verify the Final Output
    print("\n" + "="*50)
    print("✅ TEST COMPLETE - CHECKING DOCUMENT STATE")
    print("="*50)
    
    final_paragraph = DOCUMENT_STORAGE[doc_id].get_paragraph(par_id)
    
    print("\n--- Additional Notes (Should contain our injected resolution) ---")
    print(final_paragraph.get("additional"))
    
    print("\n--- Final Generated Notes (Should reflect the division formula) ---")
    print(final_paragraph.get("notes"))


if __name__ == "__main__":
    # Run the async test loop
    asyncio.run(run_test())