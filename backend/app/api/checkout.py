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
from app.api.auth_dependencies import (
    get_current_merchant_context,
    require_merchant_roles,
)
from app.auth.roles import MerchantRole

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
    merchant_context=Depends(get_current_merchant_context),
):
    cart = (
    db.query(Cart)
    .filter(
        Cart.id == cart_id,
        Cart.merchant_id == merchant_context[0].id,
    )
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
    merchant_context=Depends(
    require_merchant_roles(
        MerchantRole.OWNER,
        MerchantRole.ADMIN,
        MerchantRole.OPERATOR,
    )
),
):
    try:
        return create_checkout_order(
        db,
        cart_id=cart_id,
        confirmed=request.confirmed,
        merchant_id=merchant_context[0].id,
        idempotency_key=request.idempotency_key,
)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )