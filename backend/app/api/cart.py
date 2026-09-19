from fastapi import APIRouter, Depends, HTTPException
from app.api.auth_dependencies import (
    get_current_merchant_context,
    require_merchant_roles,
)
from app.auth.roles import MerchantRole
from sqlalchemy.orm import Session
from app.models.models import Cart
from app.db.database import SessionLocal
from app.schemas.cart import (
    AddCartItemRequest,
    CartResponse,
    CreateCartRequest,
)
from app.services.cart_service import (
    add_to_cart,
    get_or_create_cart,
    remove_from_cart,
)


router = APIRouter(
    prefix="/cart",
    tags=["cart"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def serialize_cart(cart) -> CartResponse:
    return CartResponse(
        id=cart.id,
        customer_id=cart.customer_id,
        status=cart.status,
        subtotal=cart.subtotal,
        total=cart.total,
        items=[
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in cart.items
        ],
    )


@router.post("", response_model=CartResponse)
def create_cart(
    request: CreateCartRequest,
    db: Session = Depends(get_db),
    merchant_context=Depends(
    require_merchant_roles(
        MerchantRole.OWNER,
        MerchantRole.ADMIN,
        MerchantRole.OPERATOR,
    )
),
):
    merchant, _membership = merchant_context
    cart = get_or_create_cart(
    db,
    merchant_id=merchant.id,
    customer_id=request.customer_id,
)

    return serialize_cart(cart)


@router.post(
    "/{cart_id}/items",
    response_model=CartResponse,
)
def add_cart_item(
    cart_id: int,
    request: AddCartItemRequest,
    db: Session = Depends(get_db),
    merchant_context=Depends(
    require_merchant_roles(
        MerchantRole.OWNER,
        MerchantRole.ADMIN,
        MerchantRole.OPERATOR,
    )
),
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
        cart = add_to_cart(
            db,
            cart,
            product_id=request.product_id,
            quantity=request.quantity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return serialize_cart(cart)


@router.get(
    "/{cart_id}",
    response_model=CartResponse,
)
def get_cart(
    cart_id: int,
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

    return serialize_cart(cart)

@router.delete(
    "/{cart_id}/items/{product_id}",
    response_model=CartResponse,
)
def remove_cart_item(
    cart_id: int,
    product_id: int,
    db: Session = Depends(get_db),
    merchant_context=Depends(
    require_merchant_roles(
        MerchantRole.OWNER,
        MerchantRole.ADMIN,
        MerchantRole.OPERATOR,
    )
),
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
        cart = remove_from_cart(
            db,
            cart,
            product_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return serialize_cart(cart)