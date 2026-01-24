import os
import requests
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

LOCAL_PDF_PATH = "MSME_Schemes_English_0.pdf"  # Render-safe
COLLECTION_NAME = "schemes"

KG_INITIALIZED = False
chunks=None
def init_if_available():
    global chunks,KG_INITIALIZED

    if os.getenv("ENABLED", "true").lower() != "true":
        print("disabled")
        return None

    pdf_url = os.getenv("PDF_URL")
    if not pdf_url:
        print("PDF_URL not set")
        return None

    # download if not exists
    if not os.path.exists(LOCAL_PDF_PATH):
        try:
            r = requests.get(pdf_url, timeout=30)
            r.raise_for_status()
            with open(LOCAL_PDF_PATH, "wb") as f:
                f.write(r.content)
            print(" PDF downloaded")
        except Exception as e:
            print("Failed to download  PDF:", e)
            return None

    # load PDF
    try:
        loader = PyPDFLoader(LOCAL_PDF_PATH)
        pages = loader.load()
    except Exception as e:
        print("PDF load failed:", e)
        return None

    # split
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )
    chunks = splitter.split_documents(pages)

    print(f" loaded: {len(chunks)} chunks")
    try:
        _initialize_kg(chunks)  
        KG_INITIALIZED = True  
        print(" Knowledge Graph initialized")
    except Exception as e:
        print(f" KG initialization failed: {e}")
        KG_INITIALIZED = False
    return chunks


def _initialize_kg(chunks):
    from langchain_neo4j import Neo4jGraph
    from langchain_experimental.graph_transformers import LLMGraphTransformer
    from langchain_groq import ChatGroq

    kg_conn = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    )
    
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    llm_transformer=LLMGraphTransformer(llm=llm)
    graph_documents = llm_transformer.convert_to_graph_documents(chunks[:3])
    kg_conn.add_graph_documents(
    graph_documents, 
    baseEntityLabel=True, 
    include_source=True
    
    )



def is_kg_ready() -> bool:
    return KG_INITIALIZED
