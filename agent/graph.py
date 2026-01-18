from router.router import memory_router
from llm.grader_and_filter import grade_and_filter
from llm.rewriter_query import rewrite_query
from agent.class_agent import AgentState
from retrieval.vector_retrieval import retrieve_scheme_context
from retrieval.kg_retrieval import structured_retriever,extract_user_profile
from llm.answer_generator import call
from langgraph.graph import StateGraph,START,END

### GRAPH CONNECTION ###
agent=StateGraph(AgentState)

agent.add_node("profile_extractor", extract_user_profile)
agent.add_node("Structured_context",structured_retriever)
agent.add_node("Unstructured_context",retrieve_scheme_context)

agent.add_node("mdl_call",call)
agent.add_node("router_node", lambda x: x)
agent.add_node("grader_node",lambda x:x)

agent.add_node("rewrite",rewrite_query)

agent.add_conditional_edges(
    "router_node",
    memory_router,
    {
        
        "vector_db":"Unstructured_context",
        "knowledge_graph":"Structured_context",
        "generate":"mdl_call"
       
    },
)
agent.add_edge(START, "profile_extractor")
agent.add_edge("profile_extractor","router_node")

agent.add_edge("Structured_context","grader_node")
agent.add_edge("Unstructured_context","grader_node")

agent.add_conditional_edges(
    "grader_node",
    grade_and_filter,
    {
        "rewrite_query":"rewrite",
        "generate":"mdl_call"
    }

)
agent.add_edge("rewrite", "Structured_context")
agent.add_edge("rewrite", "Unstructured_context")


agent.add_edge("mdl_call",END)
app=agent.compile()


