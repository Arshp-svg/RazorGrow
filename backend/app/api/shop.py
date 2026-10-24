import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.intent_agent import IntentAgent
from app.config import settings
from app.db.database import SessionLocal
from app.models.models import (
    ApprovalRequest,
    AuditLog,
    Cart,
    CartItem,
    Merchant,
    Order,
    Policy,
    Product,
)
from app.schemas.product import ProductResponse
from app.services.audit_service import record_audit
from app.services.policy_service import evaluate_policy
from app.services.razorpay_service import create_test_order
from app.services.recommendation_service import recommend_products
from app.services.trace_service import (
    complete_execution,
    record_tool_call,
    start_execution,
)
from app.services.upsell_service import recommend_upsell

router = APIRouter(prefix="/shop", tags=["public-shop"])
intent_agent = IntentAgent()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()] if value else []


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()] if value else []


def product_to_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        name=product.name,
        price=product.price,
        category=product.category,
        tags=parse_list(product.tags),
        use_cases=parse_list(product.use_cases),
        compatible_products=parse_int_list(product.compatible_products),
        upsell_products=parse_int_list(product.upsell_products),
        inventory=product.inventory,
    )


# --- Schemas ---

class ShopInfoResponse(BaseModel):
    merchant_id: int
    store_name: str
    status: str
    currency: str = "INR"
    policy_max_order: float
    approval_threshold: Optional[float]
    products: List[ProductResponse]


class ShopChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ShopChatResponse(BaseModel):
    reply: str
    recommended_product: Optional[ProductResponse] = None
    recommended_upsell: Optional[ProductResponse] = None
    execution_id: Optional[int] = None


class ShopCartItemInput(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class ShopCheckoutRequest(BaseModel):
    items: List[ShopCartItemInput]
    customer_email: str = "guest@example.com"
    customer_name: str = "Guest Shopper"
    confirmed: bool = True
    idempotency_key: Optional[str] = None


class ShopCheckoutResponse(BaseModel):
    status: str  # "SUCCESS" or "NEEDS_APPROVAL"
    order_id: int
    amount: float
    currency: str = "INR"
    razorpay_order_id: Optional[str] = None
    razorpay_key_id: Optional[str] = None
    message: Optional[str] = None


class ShopPaymentVerifyRequest(BaseModel):
    order_id: int
    razorpay_order_id: str
    razorpay_payment_id: str


# --- Endpoints ---

@router.get("/{merchant_id}/info", response_model=ShopInfoResponse)
def get_shop_info(merchant_id: int, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id, Merchant.status == "active").first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Store not found or inactive")

    policy = db.query(Policy).filter(Policy.merchant_id == merchant_id).order_by(Policy.id.desc()).first()
    max_order = policy.max_order_amount if policy else 100000.0
    approval_threshold = policy.approval_threshold if policy else 90000.0

    products = db.query(Product).filter(Product.merchant_id == merchant_id, Product.inventory > 0).all()

    return ShopInfoResponse(
        merchant_id=merchant.id,
        store_name=merchant.name,
        status=merchant.status,
        currency="INR",
        policy_max_order=max_order,
        approval_threshold=approval_threshold,
        products=[product_to_response(p) for p in products],
    )


@router.post("/{merchant_id}/chat", response_model=ShopChatResponse)
def shop_agent_chat(merchant_id: int, request: ShopChatRequest, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id, Merchant.status == "active").first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Store not found")

    session_id = request.session_id or f"shop_sess_{uuid.uuid4().hex[:12]}"
    execution = start_execution(
        db=db,
        merchant_id=merchant.id,
        session_id=session_id,
        intent=request.message,
    )

    try:
        # 1. Extract Intent
        intent = intent_agent.extract(request.message)
        record_tool_call(
            db=db,
            execution_id=execution.id,
            tool_name="extract_intent",
            input_data={"message": request.message},
            output_data=intent.model_dump(),
            latency_ms=10.0,
        )

        # 2. Search Grounded Products for this Merchant
        rec_response = recommend_products(db, intent, merchant_id=merchant.id)
        primary_prod = None
        if rec_response.recommendations:
            top_rec = rec_response.recommendations[0]
            primary_prod = db.query(Product).filter(Product.id == top_rec.product_id).first()

        record_tool_call(
            db=db,
            execution_id=execution.id,
            tool_name="search_catalog",
            input_data={"category": intent.category, "budget": intent.budget, "merchant_id": merchant.id},
            output_data=rec_response.model_dump(),
            latency_ms=5.0,
        )

        # 3. Compatible Upsell
        upsell_prod = None
        if primary_prod:
            upsell_resp = recommend_upsell(db=db, product_id=primary_prod.id, merchant_id=merchant.id)
            if upsell_resp and upsell_resp.upsell:
                upsell_prod = db.query(Product).filter(Product.id == upsell_resp.upsell.product_id).first()
                record_tool_call(
                    db=db,
                    execution_id=execution.id,
                    tool_name="recommend_upsell",
                    input_data={"primary_id": primary_prod.id, "merchant_id": merchant.id},
                    output_data=upsell_resp.model_dump(),
                    latency_ms=3.0,
                )

        if not primary_prod:
            reply = "I couldn't find an in-stock item matching that exact budget or specification. Let me know if you'd like to explore other categories!"
        else:
            reply = f"I recommend the **{primary_prod.name}** priced at ₹{primary_prod.price:,.0f}."
            if upsell_prod:
                reply += f" A great companion item is the **{upsell_prod.name}** for an additional ₹{upsell_prod.price:,.0f}."

        complete_execution(
            db=db,
            execution_id=execution.id,
            status="completed",
        )

        return ShopChatResponse(
            reply=reply,
            recommended_product=product_to_response(primary_prod) if primary_prod else None,
            recommended_upsell=product_to_response(upsell_prod) if upsell_prod else None,
            execution_id=execution.id,
        )
    except Exception as exc:
        complete_execution(
            db=db,
            execution_id=execution.id,
            status="failed",
        )
        raise HTTPException(status_code=500, detail=f"AI Sales Agent error: {exc}")


@router.post("/{merchant_id}/checkout", response_model=ShopCheckoutResponse)
def shop_checkout(merchant_id: int, request: ShopCheckoutRequest, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id, Merchant.status == "active").first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Store not found")

    if not request.items:
        raise HTTPException(status_code=400, detail="Cannot checkout an empty cart")

    # 1. Server-side product price & inventory lock
    product_ids = [item.product_id for item in request.items]
    products = db.query(Product).filter(Product.id.in_(product_ids), Product.merchant_id == merchant_id).all()
    product_map = {p.id: p for p in products}

    if len(product_map) != len(product_ids):
        raise HTTPException(status_code=400, detail="One or more products are unavailable in this store")

    subtotal = 0.0
    for item in request.items:
        p = product_map[item.product_id]
        if p.inventory < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient inventory for '{p.name}' (Available: {p.inventory})")
        subtotal += p.price * item.quantity

    # 2. Assemble Cart in Database
    cart = Cart(
        merchant_id=merchant.id,
        customer_id=request.customer_email,
        subtotal=subtotal,
        total=subtotal,
        status="active",
    )
    db.add(cart)
    db.flush()

    for item in request.items:
        p = product_map[item.product_id]
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=p.id,
            quantity=item.quantity,
            unit_price=p.price,
        )
        db.add(cart_item)

    # 3. Deterministic Policy Evaluation
    policy = db.query(Policy).filter(Policy.merchant_id == merchant_id).order_by(Policy.id.desc()).first()
    if not policy:
        policy = Policy(
            merchant_id=merchant_id,
            max_order_amount=100000.0,
            max_discount=10.0,
            approval_threshold=90000.0,
            confirmation_required=True,
            version=1,
        )
        db.add(policy)
        db.flush()

    decision = evaluate_policy(
        policy=policy,
        order_amount=subtotal,
        discount=0.0,
        confirmed=request.confirmed,
    )

    if decision.decision == "BLOCK":
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Policy Blocked Checkout: {decision.reason}")

    idempotency_key = request.idempotency_key or f"shop_order_{uuid.uuid4().hex}"

    # 4. Check if paused for Human-In-The-Loop Approval
    if decision.decision == "NEEDS_APPROVAL":
        order = Order(
            merchant_id=merchant_id,
            cart_id=cart.id,
            idempotency_key=idempotency_key,
            amount=subtotal,
            status="PENDING_APPROVAL",
        )
        db.add(order)
        db.flush()

        approval = ApprovalRequest(
            merchant_id=merchant_id,
            order_id=order.id,
            status="PENDING",
        )
        db.add(approval)
        db.commit()
        db.refresh(order)

        return ShopCheckoutResponse(
            status="NEEDS_APPROVAL",
            order_id=order.id,
            amount=order.amount,
            currency="INR",
            message=f"Order exceeds the merchant high-value approval threshold (₹{policy.approval_threshold:,.0f}). It has been submitted for merchant approval.",
        )

    # 5. Policy Allowed -> Create Razorpay Test Order
    amount_paise = int(round(subtotal * 100))
    razorpay_order = create_test_order(amount_paise)

    order = Order(
        merchant_id=merchant_id,
        cart_id=cart.id,
        idempotency_key=idempotency_key,
        amount=subtotal,
        status="CREATED",
        razorpay_order_id=razorpay_order.get("id"),
    )
    db.add(order)

    # Audit log
    db.commit()
    db.refresh(order)

    record_audit(
        db=db,
        merchant_id=merchant_id,
        action="order_checkout_created",
        entity_id=str(order.id),
        policy_result="ALLOW",
        external_result=f"Order created for customer {request.customer_email}. Amount: ₹{subtotal:,.2f}",
    )

    return ShopCheckoutResponse(
        status="SUCCESS",
        order_id=order.id,
        amount=order.amount,
        currency="INR",
        razorpay_order_id=razorpay_order.get("id"),
        razorpay_key_id=settings.razorpay_key_id,
        message="Razorpay test order initialized.",
    )


@router.post("/{merchant_id}/verify-payment")
def shop_verify_payment(merchant_id: int, request: ShopPaymentVerifyRequest, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        Order.id == request.order_id,
        Order.merchant_id == merchant_id,
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Transition order state machine to PAID
    order.status = "PAID"

    # Decrement inventory for purchased products
    cart_items = db.query(CartItem).filter(CartItem.cart_id == order.cart_id).all()
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product and product.inventory >= item.quantity:
            product.inventory -= item.quantity

    db.commit()

    record_audit(
        db=db,
        merchant_id=merchant_id,
        action="payment_status_updated",
        entity_id=str(order.id),
        policy_result="APPROVED",
        external_result=f"Payment verified successfully. Razorpay Payment ID: {request.razorpay_payment_id}",
    )

    return {
        "status": "PAID",
        "order_id": order.id,
        "amount": order.amount,
        "razorpay_payment_id": request.razorpay_payment_id,
        "message": "Payment verified and order confirmed successfully!",
    }
