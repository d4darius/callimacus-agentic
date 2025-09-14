from langsmith import Client

from learning_assistant.eval.learning_dataset import examples_triage
from learning_assistant.learning_assistant import learning_assistant

# Initialize LangSmith client
client = Client()

# ------------------------
# DATASET CREATION
# ------------------------

# Dataset name
dataset_name = "Current Paragraph Triage Evaluation"

# Create dataset if it doesn't exist
if not client.has_dataset(dataset_name=dataset_name):
    dataset = client.create_dataset(
        dataset_name=dataset_name, 
        description="A dataset of paragraphs and their triage decisions."
    )
    # Add examples to the dataset
    client.create_examples(dataset_id=dataset.id, examples=examples_triage)

# ------------------------
# EVALUATION FUNCTIONS
# ------------------------

def target_learning_assistant(inputs: dict) -> dict:
    """Process a paragraph through the workflow-based learning assistant."""
    response = learning_assistant.nodes['triage_router'].invoke({
        "content_input": inputs["content_input"],
        "current_paragraph": inputs["content_input"].get("current_paragraph", {
            "audio_transcription": "",
            "documentation": "",
            "student_notes": ""
        }),
        "final_notes": {}
    })
    return {"classification_decision": response.update['classification_decision']}

def classification_evaluator(outputs: dict, reference_outputs: dict) -> bool:
    """Check if the answer exactly matches the expected answer."""
    return outputs["classification_decision"].lower() == reference_outputs["classification"].lower()

# ------------------------
# RUNNING EVALUATOR
# ------------------------

# Set to true if you want to kick off evaluation
run_expt = True
if run_expt:
    experiment_results_workflow = client.evaluate(
        # Run agent 
        target_learning_assistant,
        # Dataset name   
        data=dataset_name,
        # Evaluator
        evaluators=[classification_evaluator],
        # Name of the experiment
        experiment_prefix="Learning assistant workflow", 
        # Number of concurrent evaluations
        max_concurrency=2, 
    )