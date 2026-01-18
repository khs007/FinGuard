from typing  import TypedDict,Annotated,Sequence
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages:Annotated[Sequence[BaseMessage],add_messages]
    chat_memory: str
    unstructured_context:str
    structured_context:str
    question: str
    rewrite_count: int
    user_profile: dict 
    target_profile: dict    
    target_scope: str
