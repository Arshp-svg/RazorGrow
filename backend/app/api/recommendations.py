from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.schemas.intent import ShoppingIntent
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import recommend_products
from app.agents.intent_agent import IntentAgent
from app.schemas.intent import IntentRequest
from app.api.auth_dependencies import get_current_merchant_context
from app.agents.recommendation_agent import RecommendationAgent


router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)
agent = IntentAgent()
recommendation_agent = RecommendationAgent()

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=RecommendationResponse)
def get_recommendations(
    intent: ShoppingIntent,
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    return recommend_products(
        db,
        intent,
        merchant_id=merchant_context[0].id,
    )

@router.post(
    "/from-message",
    response_model=RecommendationResponse,
)
def get_recommendations_from_message(
    request: IntentRequest,
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    intent = agent.extract(request.message)

    result = recommend_products(
    db,
    intent,
    merchant_id=merchant_context[0].id,
)

    explanation = recommendation_agent.explain(
        intent,
        result,
    )

    result.explanation = explanation

    return result