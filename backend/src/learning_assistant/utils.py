import os
import json
import logging
from langgraph.store.base import BaseStore
from learning_assistant.prompts import default_content_preferences

logging.basicConfig(
    level=logging.INFO, # Change to logging.DEBUG to see the raw LLM messages later
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("LearningAssistantAgent")

# Define where the global memory lives (we can put it in the context folder)
MEMORY_FILE_PATH = os.path.join(os.path.dirname(__file__), "../context", "global_memory.json")

def load_global_memory(store: BaseStore):
    """Loads memory from disk, or creates it using defaults if it doesn't exist."""
    if os.path.exists(MEMORY_FILE_PATH):
        try:
            with open(MEMORY_FILE_PATH, "r", encoding="utf-8") as f:
                saved_profiles = json.load(f)
                if "agent_profile" in saved_profiles:
                    store.put(("learning_assistant", "agent_profile"), "user_preferences", saved_profiles["agent_profile"])
                if "compiler_profile" in saved_profiles:
                    store.put(("learning_assistant", "compiler_profile"), "user_preferences", saved_profiles["compiler_profile"])
            logger.info("🧠 [SYSTEM] Global memory successfully loaded from disk into RAM.")
        except Exception as e:
            logger.error(f"❌ [SYSTEM] Error loading global memory: {e}")
    else:
        # SEED THE DEFAULTS!
        logger.info("🌱 [SYSTEM] No global memory file found. Seeding initial defaults.")
        store.put(("learning_assistant", "agent_profile"), "user_preferences", "- Reference previously covered topics.\n- Use ask_question for clarification.")
        store.put(("learning_assistant", "compiler_profile"), "user_preferences", default_content_preferences)
        save_global_memory(store) 

def save_global_memory(store: BaseStore):
    """Flushes the current RAM state to the JSON file."""
    agent_item = store.get(("learning_assistant", "agent_profile"), "user_preferences")
    compiler_item = store.get(("learning_assistant", "compiler_profile"), "user_preferences")
    
    memory_data = {
        "agent_profile": agent_item.value if agent_item else "",
        "compiler_profile": compiler_item.value if compiler_item else ""
    }
    
    try:
        with open(MEMORY_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, indent=4)
        logger.info("💾 [SYSTEM] Global memory successfully flushed to disk.")
    except Exception as e:
        logger.error(f"❌ [SYSTEM] Error saving global memory to disk: {e}")