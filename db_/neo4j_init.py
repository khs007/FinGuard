from retrieval.kg_retrieval import _kg_conn

def create_indexes():
    _kg_conn.query("""
    CREATE FULLTEXT INDEX entity_name_index
    IF NOT EXISTS
    FOR (n:Entity)
    ON EACH [n.name]
    """)

if __name__ == "__main__":
    create_indexes()
