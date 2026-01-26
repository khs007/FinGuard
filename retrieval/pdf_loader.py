import os
import requests
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

LOCAL_PDF_PATH = "MSME_Schemes_English_0.pdf"
COLLECTION_NAME = "schemes"

KG_INITIALIZED = False
chunks = None


def download_pdf_if_needed():
    """Download PDF if not exists locally"""
    pdf_url = os.getenv("PDF_URL")
    
    if not pdf_url:
        print("[PDF] ⚠️ PDF_URL not set - skipping download")
        return False
    
    if os.path.exists(LOCAL_PDF_PATH):
        print(f"[PDF] ✅ PDF already exists: {LOCAL_PDF_PATH}")
        return True
    
    try:
        print(f"[PDF] 📥 Downloading from {pdf_url}...")
        r = requests.get(pdf_url, timeout=60)
        r.raise_for_status()
        
        with open(LOCAL_PDF_PATH, "wb") as f:
            f.write(r.content)
        
        print(f"[PDF] ✅ Downloaded successfully ({len(r.content)} bytes)")
        return True
        
    except Exception as e:
        print(f"[PDF] ❌ Download failed: {e}")
        return False


def load_pdf_chunks():
    """Load and split PDF into chunks"""
    global chunks
    
    if chunks is not None:
        return chunks  # Already loaded
    
    # Ensure PDF exists
    if not download_pdf_if_needed():
        print("[PDF] ❌ Cannot proceed without PDF")
        return None
    
    try:
        # Load PDF
        loader = PyPDFLoader(LOCAL_PDF_PATH)
        pages = loader.load()
        print(f"[PDF] ✅ Loaded {len(pages)} pages")
        
        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150
        )
        chunks = splitter.split_documents(pages)
        print(f"[PDF] ✅ Created {len(chunks)} chunks")
        
        return chunks
        
    except Exception as e:
        print(f"[PDF] ❌ Loading failed: {e}")
        return None


def init_if_available():
    """
    Initialize KG if PDF is available
    
    ⚠️ WARNING: This is BLOCKING and should only be called:
    - In a background task
    - On first query (lazy)
    - NOT during app startup
    """
    global KG_INITIALIZED
    
    if KG_INITIALIZED:
        return True
    
    if os.getenv("ENABLED", "true").lower() != "true":
        print("[PDF] Disabled via ENABLED=false")
        return False
    
    # Load chunks
    chunks = load_pdf_chunks()
    if not chunks:
        return False
    
    # Initialize KG (BLOCKING - takes 30+ seconds)
    try:
        _initialize_kg(chunks)
        KG_INITIALIZED = True
        print("[PDF] ✅ Knowledge Graph initialized")
        return True
        
    except Exception as e:
        print(f"[PDF] ❌ KG initialization failed: {e}")
        KG_INITIALIZED = False
        return False


def _initialize_kg(chunks):
    """
    Initialize Knowledge Graph with PDF data
    
    ⚠️ EXPENSIVE OPERATION - takes 30+ seconds
    """
    from langchain_neo4j import Neo4jGraph
    from langchain_experimental.graph_transformers import LLMGraphTransformer
    from langchain_groq import ChatGroq
    
    print("[KG Init] Connecting to Neo4j...")
    kg_conn = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
    )
    
    print("[KG Init] Transforming documents (this takes time)...")
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    llm_transformer = LLMGraphTransformer(llm=llm)
    
    # Only process first 3 chunks for demo (adjust as needed)
    graph_documents = llm_transformer.convert_to_graph_documents(chunks[:3])
    
    print("[KG Init] Adding to graph database...")
    kg_conn.add_graph_documents(
        graph_documents,
        baseEntityLabel=True,
        include_source=True
    )
    
    print("[KG Init] ✅ Complete")


def is_kg_ready() -> bool:
    """Check if KG is initialized"""
    return KG_INITIALIZED