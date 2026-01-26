from fastapi import APIRouter
from scam_detector.scam_detector import predict_scam

router = APIRouter(prefix="/scam", tags=["Scam Detection"])

@router.post("/check")
def check_scam(payload: dict):
    score = predict_scam(payload)

    risk = (
        "HIGH" if score > 0.8 else
        "MEDIUM" if score > 0.5 else
        "LOW"
    )

    return {
        "risk": risk,
        "score": score
    }
