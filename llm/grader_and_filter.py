from agent.class_agent import AgentState
from  pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import  ChatPromptTemplate,MessagesPlaceholder


grader_llm=ChatGroq(model="llama-3.1-8b-instant", temperature=0)

class RelevanceScore(BaseModel):
    """Binary score for context relevance."""
    vector_score: float = Field(description="Is the context_text relevant scale down on scale of 0.0–1.0")
    graph_score:  float = Field(description="Is the graph_data relevant scale down on scale of 0.0–1.0")


grader_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a strict relevance evaluator."),
    ("human", """
Question:
{question}

Vector DB Context:
{vector_docs}

Knowledge Graph Context:
{graph_docs}

Return relevance scores between 0 and 1.
""")
])
grader = grader_prompt|grader_llm.with_structured_output(RelevanceScore)
def grade_and_filter(state: AgentState)->str:
    """
    Decides the next route in the graph.
    MUST return only one of the routing keys.

    """
    try:

        question = state.get("question") or state["messages"][-1].content
        vector_data = state.get("unstructured_context", "")
        graph_data = state.get("structured_context", "")

    # One LLM call to grade both sources
        score = grader.invoke({
            "question": question,
            "vector_docs": vector_data,
            "graph_docs": graph_data
        })
        
    
        rewrite_count = state.get("rewrite_count", 0)
        
         #if neither kg nor vector_db weightage is relevant
        if (
            score.vector_score < 0.4
            and score.graph_score < 0.4
            and rewrite_count < 2
        ):
            state["rewrite_count"] = rewrite_count + 1
            return "rewrite_query" 
        #if kg weightage is more relevant
        if score.graph_score >= 0.7 and score.graph_score > score.vector_score:
            state["unstructured_context"] = ""
            return "generate"
        #if vector_db weightage is more relevant
        if score.vector_score >= 0.6 and score.vector_score > score.graph_score:
            state["structured_context"] = ""
            return "generate"
       
        return "generate"
    except Exception as e:
        print(f"Error in grading & filter . Error: {e}")
        return "generate" 

