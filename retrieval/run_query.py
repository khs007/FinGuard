def run_query(driver, query, params=None):
    try:
        with driver.session() as session:
            return list(session.run(query, params or {}))
    except Exception as e:
        print("[KG ERROR]", e)
        return []
