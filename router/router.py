from agent.class_agent import AgentState
from  pydantic import BaseModel, Field
from typing  import Literal
from langchain_groq import ChatGroq


### ROUTER CLASS MEMORY ROUTER ###
class MemoryRoute(BaseModel):
    """Routing decision for memory system."""
    
    route: Literal[ "vector_db", "knowledge_graph", "generate"] = Field(
        ...,
        description="Which path to take based on the user's query"
    )
    
    reasoning: str = Field(
        ...,
        description="Brief explanation of why this route was chosen"
    )


tier_1=ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=0)
backup_model = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

router_llm = (
    tier_1
    .with_structured_output(MemoryRoute)
    .with_fallbacks([backup_model.with_structured_output(MemoryRoute)])
)

### FALL_BACK FUNCTION PREVENT FROM FAILURE ###
def memory_router(state:AgentState) -> str:
    """
    Memory Router for FinGuard - Government Schemes Feature.

    Purpose:
    Determines the SINGLE appropriate data source required to answer
    a government-scheme-related user query safely and correctly.

    Routing Principles:
    1. Deterministic routing - exactly one route per query.
    2. Grounding-first - financial, eligibility, or policy queries
       must use retrieved or structured data.
    3. Pattern-first execution - fast, low-latency classification
       before any generative reasoning.
    4. Fail-safe defaults –-when uncertain, prefer retrieval over generation.

    Returns:
    A string route identifier: one of
    ["vector_db", "knowledge_graph", "generate"].
   
    """

    messages = state["messages"]
    user_input = messages[-1].content
   
    q = user_input.lower()
    try:
        # High-risk / factual government scheme signals → vector DB
        if any(kw in q for kw in [
            "scheme", "yojana", "loan", "subsidy", "benefit",
            "eligibility", "eligible", "documents", "apply",
            "application", "procedure", "guidelines",
            "interest", "repayment", "government"
        ]): 
            print("ROUTING DECISION: vector_db")
            return "vector_db"

        # Relationship / eligibility-matching logic → knowledge graph
        if any(kw in q for kw in [
            "am i eligible", "which scheme", "best scheme",
            "for me", "based on", "depends on","for ",
            "related to", "under which"
        ]):
            print("ROUTING DECISION: knowledge_graph ")
            return "knowledge_graph"

        # Low-risk conversational or clarification queries
        if any(kw in q for kw in [
            "hi", "hello", "hey", "thanks", "ok", "yes", "no"
        ]):
            print("ROUTING DECISION: generate ")
            return "generate"
        else :
            print("KEYWORD ROUTING FAILED → USING LLM FALLBACK ---\n")
            return _fallback_routing(q)
        
    except Exception as e:
        print(f" Routing failed, using fallback. Error: {e}")
        return _fallback_routing(q)

    

### MEMORY ROUTER FUNCTION RETURN STR ###
def _fallback_routing (query:str) -> str:
    """
    Deterministic fallback router for FinGuard Government Schemes feature.

    Used ONLY when keyword search routing fails.
    Follows conservative, grounding-first principles.
    """
    
    
    # Initialize parser and LLM
    router_prompt="""
You are a deterministic routing component for FinGuard's Government Schemes feature.
Your task:
Choose the SINGLE most appropriate route to answer the user's query
about government schemes safely and correctly.

Available routes:

1. vector_db
   Use when the query requires retrieving information from documents or text sources,
   including:
   - Scheme details, benefits, eligibility criteria
   - Required documents, application steps, deadlines
   - Government policies, rules, notifications, guidelines
   - Any information that must be grounded in official or indexed sources

2. knowledge_graph
   Use when the query requires structured relationships such as:
   - Matching user profile attributes (age, sector, income, state) to schemes
   - Understanding dependencies between schemes, benefits, and conditions
   - Multi-step eligibility reasoning across connected entities

3. generate
   Use ONLY when the query is:
   - Conversational or clarificatory (e.g., greetings, confirmations)
   - Asking for high-level explanations about schemes without factual lookup
   - Asking follow-up questions that do NOT introduce new factual requirements

Rules:
- Choose exactly ONE route.
- Provide a brief justification (max 10 words).
- If the query involves eligibility, money, documents, or applications, do NOT choose generate.
- If uncertain, choose vector_db.

Query: {query}

Reason: (max 10 words)"""

    try:
      
        decision = router_llm.invoke(router_prompt.format(query=query))
        model_used = getattr(decision, "response_metadata", {}).get("model_name")
        print(model_used)
        print(f"\n--- ROUTING DECISION: {decision.route} | Reasoning: {decision.reasoning} ---\n")
        return decision.route
        
    except Exception as e:
            print(f"LLM routing failed: {e}")
            return "vector_db"
    
        


