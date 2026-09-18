from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.products import router as products_router
from app.db.database import SessionLocal
from app.models.models import Order
from app.schemas.order import TestOrderRequest
from app.services.razorpay_service import create_test_order
from app.api.intent import router as intent_router
from app.api.recommendations import router as recommendations_router
from app.api.upsells import router as upsells_router
from app.api.cart import router as cart_router
from app.api.checkout import router as checkout_router
from app.api.policy import router as policy_router
from app.api.dashboard import router as dashboard_router
from app.api.auth import router as auth_router

app = FastAPI(title="RazorGrow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(intent_router)
app.include_router(recommendations_router)
app.include_router(upsells_router)
app.include_router(cart_router)
app.include_router(checkout_router)
app.include_router(policy_router)
app.include_router(dashboard_router)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/orders/test")
def create_test_order_endpoint(request: TestOrderRequest):
    razorpay_order = create_test_order(request.amount)

    db = SessionLocal()

    try:
        order = Order(
            amount=request.amount / 100,
            status=razorpay_order["status"],
            razorpay_order_id=razorpay_order["id"],
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return {
            "local_order_id": order.id,
            "razorpay_order_id": order.razorpay_order_id,
            "amount": razorpay_order["amount"],
            "currency": razorpay_order["currency"],
            "status": order.status,
        }

    finally:
        db.close()