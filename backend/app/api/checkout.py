from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.checkout_service import create_checkout_order
from app.db.database import SessionLocal
from app.models.models import Cart
from app.schemas.checkout import (
    CheckoutConfirmationRequest,
    CheckoutConfirmationResponse,
)
from app.services.cart_service import validate_checkout


router = APIRouter(
    prefix="/checkout",
    tags=["checkout"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{cart_id}/confirm",
    response_model=CheckoutConfirmationResponse,
)
def confirm_checkout(
    cart_id: int,
    request: CheckoutConfirmationRequest,
    db: Session = Depends(get_db),
):
    cart = (
        db.query(Cart)
        .filter(Cart.id == cart_id)
        .first()
    )

    if cart is None:
        raise HTTPException(
            status_code=404,
            detail="Cart not found",
        )

    try:
        validate_checkout(cart)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return CheckoutConfirmationResponse(
        cart_id=cart.id,
        total=cart.total,
        confirmed=request.confirmed,
    )
    
@router.post(
    "/{cart_id}/create-order",
)
def create_checkout_payment_order(
    cart_id: int,
    request: CheckoutConfirmationRequest,
    db: Session = Depends(get_db),
):
    try:
        return create_checkout_order(
            db,
            cart_id=cart_id,
            confirmed=request.confirmed,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )