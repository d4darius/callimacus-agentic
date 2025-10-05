from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Literal
from langgraph.graph import MessagesState

#TODO: change the schemas

class RouterSchema(BaseModel):
    """Analyze the unread email and route it according to its content."""

    reasoning: str = Field(
        description="Step-by-step reasoning behind the classification."
    )
    classification: Literal["continue", "ignore", "new"] = Field(
        description="The classification for a sentence input: 'continue' for ongoing topics in the paragraph, "
                    "'ignore' for skipping irrelevant points, "
                    "'new' for introducing new topics.",
    )
    paragraph_id: int = Field(
        description="The id of the paragraph to be resumed or the new paragraph's assigned id"
    )

class StateInput(TypedDict):
    # This is the input to the state
    content_input: dict

class State(MessagesState):
    # This state class has the messages key build in
    content_input: dict
    classification_decision: Literal["continue", "ignore", "new"]
    current_paragraph: dict

class LectureData(TypedDict):
    id: str
    thread_id: str
    audio_transcription: str
    documentation_slide: str
    student_notes: str
    document_context: str

class UserPreferences(BaseModel):
    """Updated user preferences based on user's feedback."""
    chain_of_thought: str = Field(description="Reasoning about which user preferences need to add/update if required")
    user_preferences: str = Field(description="Updated user preferences")