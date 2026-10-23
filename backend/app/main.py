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
from app.api.approvals import router as approvals_router
from app.api.webhooks import router as webhooks_router
from app.api.agent import router as agent_router
import os
from app.api.analytics import router as analytics_router
from app.api.ai_catalog import router as ai_catalog_router
from app.security.middleware import register_security_and_error_handlers

app = FastAPI(title="RazorGrow API")

cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register security headers (nosniff, DENY, etc.) and global error handlers
register_security_and_error_handlers(app)

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(intent_router)
app.include_router(recommendations_router)
app.include_router(upsells_router)
app.include_router(cart_router)
app.include_router(checkout_router)
app.include_router(policy_router)
app.include_router(dashboard_router)
app.include_router(approvals_router)
app.include_router(webhooks_router)
app.include_router(agent_router)
app.include_router(analytics_router)
app.include_router(ai_catalog_router)

@app.get("/health")
def health():
    db = SessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"unhealthy: {exc}"
    finally:
        db.close()

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "service": "razorgrow-backend",
        "version": "1.0.0",
        "database": db_status,
    }


@app.get("/health/ready")
def readiness():
    db = SessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database not ready: {exc}")
    finally:
        db.close()


@app.get("/health/live")
def liveness():
    return {"status": "alive"}


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
