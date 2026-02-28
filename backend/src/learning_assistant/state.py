from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add] 
    llm_calls: int
    
    # Context for the current execution
    doc_id: str
    par_id: str
    
    # Long-term Memory Profile
    user_memory: str