from fastapi import APIRouter, HTTPException

from app.agents.intent_agent import IntentAgent
from app.schemas.intent import IntentRequest, ShoppingIntent


router = APIRouter(prefix="/intent", tags=["intent"])

agent = IntentAgent()


@router.post("", response_model=ShoppingIntent)
def extract_intent(request: IntentRequest):
    try:
        return agent.extract(request.message)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc