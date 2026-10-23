from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.schemas.ai_catalog import (
    AIBuyerProcureRequest,
    AIBuyerProcureResponse,
    AIBuyerScenario,
    AICatalogResponse,
)
from app.services.ai_catalog_service import (
    execute_ai_buyer_procurement,
    get_ai_buyer_scenarios,
    get_ai_catalog,
)
from app.security.rate_limiter import rate_limit_agent

router = APIRouter(
    prefix="/ai",
    tags=["ai_catalog"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/catalog", response_model=AICatalogResponse)
def get_ai_readable_catalog(
    merchant_id: int = Query(default=1, description="Merchant ID for catalog discovery"),
    db: Session = Depends(get_db),
):
    try:
        return get_ai_catalog(db, merchant_id=merchant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/buyer/scenarios", response_model=list[AIBuyerScenario])
def get_buyer_demonstration_scenarios():
    return get_ai_buyer_scenarios()


@router.post(
    "/buyer/procure",
    response_model=AIBuyerProcureResponse,
    dependencies=[Depends(rate_limit_agent)],
)
def run_ai_buyer_procurement(
    request: AIBuyerProcureRequest,
    db: Session = Depends(get_db),
):
    try:
        return execute_ai_buyer_procurement(db, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
