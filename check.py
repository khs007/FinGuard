from dotenv import load_dotenv
import os
from langchain_neo4j import Neo4jGraph

load_dotenv()

kg = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE"),
)
print(
    os.getenv("NEO4J_URI"),
    os.getenv("NEO4J_USERNAME"),
    "PWD_SET" if os.getenv("NEO4J_PASSWORD") else "PWD_MISSING"
)

print("✅ Connected to Neo4j Aura successfully")
