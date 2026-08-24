from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.services.upsell_service import recommend_upsell
from app.schemas.upsell import (
    UpsellAcceptanceRequest,
    UpsellResponse,
)


router = APIRouter(
    prefix="/upsells",
    tags=["upsells"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{product_id}",
    response_model=UpsellResponse,
)
def get_upsell(
    product_id: int,
    db: Session = Depends(get_db),
):
    try:
        return recommend_upsell(
            db,
            product_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
        
@router.post(
    "/{product_id}/accept",
    response_model=UpsellResponse,
)
def accept_upsell(
    product_id: int,
    request: UpsellAcceptanceRequest,
    db: Session = Depends(get_db),
):
    try:
        result = recommend_upsell(
            db,
            product_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    result.accepted = request.accepted

    return result