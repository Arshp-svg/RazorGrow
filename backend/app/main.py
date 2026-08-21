from fastapi import FastAPI

from app.db.database import SessionLocal
from app.models.models import Order
from app.schemas.order import TestOrderRequest
from app.services.razorpay_service import create_test_order


app = FastAPI(title="RazorGrow API")


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