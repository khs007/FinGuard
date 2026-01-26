import joblib
from scipy.sparse import hstack

bundle = None

def load_scam_bundle():
    global bundle
    if bundle is None:
        bundle = joblib.load(r"C:\langgraph\Project_jan\model\scam_bundle.pkl")

def predict_scam(payload: dict):
    model = bundle["model"]
    tfidf_scam = bundle["tfidf_scam"]
    tfidf_response = bundle["tfidf_response"]
    safe_features = bundle["safe_numerical_features"]

    scam_text = payload["scam_text"]
    response_text = payload.get("response_text", "")

    numeric_values = [payload.get(f, 0) for f in safe_features]

    X_scam = tfidf_scam.transform([scam_text])
    X_resp = tfidf_response.transform([response_text])

    X = hstack([X_scam, X_resp, [numeric_values]])

    proba = model.predict_proba(X)[0][1]
    return float(proba)
