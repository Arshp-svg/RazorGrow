import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.main import app
from app.models.models import AuditLog, Campaign, Cart, CartItem, Merchant, MerchantMembership, Order, Product, User
from app.services.analytics_service import (
    decide_campaign,
    generate_revenue_insights,
    get_agent_metrics,
    get_revenue_metrics,
)
from app.services.auth_service import create_access_token, hash_password
from app.services.trace_service import record_tool_call, start_execution

client = TestClient(app)


def create_merchant_user(db, role: str = "OWNER") -> tuple[User, str]:
    user = User(
        email=f"analytics_test_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("analytics_secret_123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    membership = MerchantMembership(
        merchant_id=1,
        user_id=user.id,
        role=role,
    )
    db.add(membership)
    db.commit()

    token = create_access_token(user_id=user.id)
    return user, token


def test_revenue_metrics_calculation():
    db = SessionLocal()
    try:
        # Create a paid order with upsell item
        cart = Cart(merchant_id=1, customer_id="analytics_cust", status="active", subtotal=63200, total=63200)
        db.add(cart)
        db.commit()
        db.refresh(cart)

        item1 = CartItem(cart_id=cart.id, product_id=1, quantity=1, unit_price=62000)
        item2 = CartItem(cart_id=cart.id, product_id=4, quantity=1, unit_price=1200)
        db.add_all([item1, item2])
        db.commit()

        order = Order(
            merchant_id=1,
            cart_id=cart.id,
            idempotency_key=f"analytics_order_{uuid.uuid4().hex}",
            amount=63200,
            status="paid",
            razorpay_order_id=f"order_analyt_{uuid.uuid4().hex[:10]}",
        )
        db.add(order)
        db.commit()

        metrics = get_revenue_metrics(db, merchant_id=1)

        assert metrics["total_orders"] >= 1
        assert metrics["successful_payments"] >= 1
        assert metrics["total_revenue"] >= 63200
        assert metrics["upsell_revenue"] >= 1200
        assert metrics["ai_influenced_revenue"] >= 63200
        assert metrics["average_order_value"] > 0
    finally:
        db.close()


def test_agent_metrics_calculation():
    db = SessionLocal()
    try:
        exec_record = start_execution(
            db,
            merchant_id=1,
            session_id=f"sess_analyt_{uuid.uuid4().hex[:6]}",
            intent="Laptop search",
        )
        record_tool_call(
            db,
            execution_id=exec_record.id,
            tool_name="extract_intent",
            status="success",
            latency_ms=85.0,
        )

        metrics = get_agent_metrics(db, merchant_id=1)

        assert metrics["total_executions"] >= 1
        assert metrics["total_tool_calls"] >= 1
        assert "extract_intent" in metrics["tool_breakdown"]
    finally:
        db.close()


def test_generate_revenue_insights_creates_grounded_campaign():
    db = SessionLocal()
    try:
        insights = generate_revenue_insights(db, merchant_id=1)

        assert "insights" in insights
        assert len(insights["insights"]) >= 1
        assert "recommendations" in insights
        assert insights["campaign_proposal"] is not None

        proposal = insights["campaign_proposal"]
        assert proposal["id"] is not None
        assert "AI Bundle:" in proposal["title"]
        assert proposal["status"] == "PENDING_APPROVAL"
        assert proposal["discount_percent"] == 10.0

        # Verify saved in Campaign table
        saved = db.query(Campaign).filter(Campaign.id == proposal["id"]).first()
        assert saved is not None
        assert saved.status == "PENDING_APPROVAL"

        # Verify audit log was recorded
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.merchant_id == 1,
                AuditLog.action == "revenue_insight_generated",
                AuditLog.entity_id == str(saved.id),
            )
            .first()
        )
        assert audit is not None
        assert audit.policy_result == "NEEDS_APPROVAL"
    finally:
        db.close()


def test_campaign_decision_lifecycle():
    db = SessionLocal()
    try:
        user, _ = create_merchant_user(db, role="OWNER")
        insights = generate_revenue_insights(db, merchant_id=1)
        campaign_id = insights["campaign_proposal"]["id"]

        # Approve the proposal
        approved = decide_campaign(db, campaign_id=campaign_id, merchant_id=1, user_id=user.id, approve=True)
        assert approved.status == "APPROVED"
        assert approved.decided_at is not None
        assert approved.decided_by_user_id == user.id

        # Verify cannot re-decide already decided campaign
        with pytest.raises(ValueError, match="already in status"):
            decide_campaign(db, campaign_id=campaign_id, merchant_id=1, user_id=user.id, approve=False)
    finally:
        db.close()


def test_analytics_api_endpoints():
    db = SessionLocal()
    try:
        user, token = create_merchant_user(db, role="OWNER")
        headers = {"Authorization": f"Bearer {token}"}

        # GET /analytics/overview
        overview_resp = client.get("/analytics/overview", headers=headers)
        assert overview_resp.status_code == 200
        overview_data = overview_resp.json()
        assert "metrics" in overview_data
        assert "agent" in overview_data
        assert "activity" in overview_data

        # GET /analytics/revenue
        rev_resp = client.get("/analytics/revenue", headers=headers)
        assert rev_resp.status_code == 200
        rev_data = rev_resp.json()
        assert "total_revenue" in rev_data
        assert "ai_influenced_revenue" in rev_data
        assert "upsell_revenue" in rev_data

        # POST /analytics/insights
        insight_resp = client.post("/analytics/insights", headers=headers)
        assert insight_resp.status_code == 200
        insight_data = insight_resp.json()
        assert "campaign_proposal" in insight_data
        proposal_id = insight_data["campaign_proposal"]["id"]

        # POST /analytics/campaigns/{id}/approve
        approve_resp = client.post(f"/analytics/campaigns/{proposal_id}/approve", headers=headers)
        assert approve_resp.status_code == 200
        assert approve_resp.json()["campaign_status"] == "APPROVED"

    finally:
        db.close()
