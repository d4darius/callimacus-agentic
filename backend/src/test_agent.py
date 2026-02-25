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
    # Changing doc_id to "test" so it generates "test.json"
    doc_id = "test" 
    par_id = "test_par_001"
    
    # Initialize the document in our global dictionary
    test_doc = Document(doc_id)
    DOCUMENT_STORAGE[doc_id] = test_doc
    
    # Inject conflicting data to force the LLM to use 'ask_question'
    test_doc.paragraphs[par_id] = {
        "audio": "we must divide the mass by the volume to get density.",
        "ocr": "Formula on slide: Density = Mass * Volume",
        "notes": "Density is defined as the ratio between volume and mass of an object",
        "additional_notes": ""
    }
    
    # Force a manual save of the initial state to the JSON file
    test_doc._save_context()

    # Simulate React's initial save to the UI Document
    test_doc._update_ui_document(par_id, "Density is defined as the ratio between volume and mass of an object")
    print(f"📄 Mocked React UI Document created at {test_doc.doc_file_path}")

    # 2. Setup Thread Config (Required for MemorySaver to work)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # 3. Define the Initial State
    paragraph_data = test_doc.paragraphs[par_id]
    
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
        
        # Resume the graph
        await agent.ainvoke(Command(resume=mock_ui_response), config)
    else:
        print("\n⚠️ Graph finished without pausing. (The LLM didn't think it needed to ask a question).")

    # 7. Verify the Memory State
    print("\n" + "="*50)
    print("✅ TEST COMPLETE - CHECKING IN-MEMORY STATE")
    print("="*50)
    
    final_paragraph = DOCUMENT_STORAGE[doc_id].get_paragraph(par_id)
    print("\n--- Additional Notes (In-Memory) ---")
    print(final_paragraph.get("additional"))
    
    print("\n--- Final Generated Notes (In-Memory) ---")
    print(final_paragraph.get("notes"))

    # 8. Verify the JSON Persistence on Disk!
    print("\n" + "="*50)
    print("💾 VERIFYING JSON PERSISTENCE ON DISK")
    print("="*50)
    
    # We create a brand new Document instance. 
    # If it successfully loads the newly generated text, your JSON logic is perfect.
    disk_verification_doc = Document("test")
    persisted_paragraph = disk_verification_doc.get_paragraph(par_id)
    
    print(f"\nLoading from: {disk_verification_doc.doc_file_path}")
    
    print("\n--- Persisted Additional Notes (From JSON) ---")
    print(persisted_paragraph.get("additional"))
    
    print("\n--- Persisted Final Generated Notes (From JSON) ---")
    print(persisted_paragraph.get("notes"))
    print("\n🎉 If the JSON text matches the In-Memory text, your persistence layer is working perfectly!")


if __name__ == "__main__":
    # Run the async test loop
    asyncio.run(run_test())