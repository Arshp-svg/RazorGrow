import uuid
from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.main import app
from app.models.models import ApprovalRequest, Merchant, Order, Product

client = TestClient(app)


def test_ai_catalog_endpoint_structure():
    response = client.get("/ai/catalog?merchant_id=1")
    assert response.status_code == 200
    data = response.json()

    assert data["protocol"] == "razorgrow-ai-commerce/v1.0"
    assert data["merchant"]["id"] == 1
    assert data["merchant"]["currency"] == "INR"

    policies = data["commerce_policies"]
    assert policies["max_transaction_amount"] == 100000.0
    assert policies["max_discount_percent"] == 10.0
    assert policies["merchant_approval_threshold"] == 90000.0

    summary = data["catalog_summary"]
    assert summary["total_items"] >= 10
    assert "laptop" in summary["categories"]

    items = data["items"]
    assert len(items) >= 10

    # Verify laptop product with resolved compatibility
    laptop = next((i for i in items if i["id"] == 1), None)
    assert laptop is not None
    assert laptop["name"] == "ProBook 14 Laptop"
    assert laptop["price"] == 62000.0
    assert laptop["availability"] == "in_stock"
    assert len(laptop["compatibility"]) > 0

    # Ensure compatibility is resolved into rich objects, not raw IDs
    comp_mouse = next((c for c in laptop["compatibility"] if c["product_id"] == 4), None)
    assert comp_mouse is not None
    assert comp_mouse["name"] == "Ergo Wireless Mouse"
    assert comp_mouse["price"] == 1200.0
    assert comp_mouse["in_stock"] is True


def test_ai_buyer_scenarios_endpoint():
    response = client.get("/ai/buyer/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) >= 4
    scenario_ids = [s["id"] for s in scenarios]
    assert "scenario_developer_workstation" in scenario_ids
    assert "scenario_over_limit_block" in scenario_ids
    assert "scenario_approval_checkpoint" in scenario_ids


def test_ai_buyer_procure_success_allow():
    request_data = {
        "merchant_id": 1,
        "query": "Procure a developer laptop under ₹70,000 paired with a compatible wireless mouse",
        "budget_limit": 70000.0,
        "product_id": 1,
        "include_compatible_addon": True,
        "auto_confirm": True,
        "idempotency_key": f"test_ai_buyer_{uuid.uuid4().hex}",
    }

    response = client.post("/ai/buyer/procure", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["policy_decision"]["decision"] == "ALLOW"
    assert data["execution_id"] is not None
    assert data["cart_id"] is not None
    assert data["order"] is not None

    order = data["order"]
    assert order["amount"] == 63200.0
    assert order["razorpay_order_id"] is not None
    assert order["status"] == "created"

    # Verify trace was stored in AgentExecution
    trace_resp = client.get(f"/agent/executions/{data['execution_id']}/trace")
    # Note: /agent/executions trace endpoint requires auth if calling via protected endpoint,
    # but we can check the database directly
    db = SessionLocal()
    try:
        from app.models.models import AgentExecution, ToolCall
        execution = db.query(AgentExecution).filter(AgentExecution.id == data["execution_id"]).first()
        assert execution is not None
        assert execution.status == "success"

        tool_calls = db.query(ToolCall).filter(ToolCall.execution_id == execution.id).all()
        tool_names = [tc.tool_name for tc in tool_calls]
        assert "discover_ai_catalog" in tool_names
        assert "select_grounded_products" in tool_names
        assert "assemble_procurement_cart" in tool_names
        assert "evaluate_policy_gates" in tool_names
        assert "create_razorpay_checkout_order" in tool_names
    finally:
        db.close()


def test_ai_buyer_procure_policy_blocked_on_over_limit():
    request_data = {
        "merchant_id": 1,
        "query": "Procure dual enterprise workstation package exceeding ₹120,000",
        "budget_limit": 150000.0,
        "product_id": 1,
        "include_compatible_addon": False,
        "auto_confirm": True,
    }

    response = client.post("/ai/buyer/procure", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "POLICY_BLOCKED"
    assert data["policy_decision"]["decision"] == "BLOCK"
    assert "exceeds" in data["policy_decision"]["reason"].lower()
    assert data["order"] is None


def test_ai_buyer_procure_needs_approval_at_threshold():
    request_data = {
        "merchant_id": 1,
        "query": "Procure workstation and 4K display package at ₹90,000",
        "budget_limit": 100000.0,
        "product_id": 1,
        "include_compatible_addon": False,
        "auto_confirm": True,
    }

    response = client.post("/ai/buyer/procure", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "NEEDS_APPROVAL"
    assert data["policy_decision"]["decision"] == "NEEDS_APPROVAL"
    assert data["approval_id"] is not None

    db = SessionLocal()
    try:
        approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == data["approval_id"]).first()
        assert approval is not None
        assert approval.status == "PENDING"
        assert approval.merchant_id == 1
    finally:
        db.close()


def test_ai_catalog_tenant_isolation():
    db = SessionLocal()
    try:
        # Create merchant 2 if not exists
        m2 = db.query(Merchant).filter(Merchant.id == 2).first()
        if not m2:
            m2 = Merchant(id=2, name="Tenant 2 Store", status="active")
            db.add(m2)
            db.commit()

        # Add 1 product for Merchant 2
        p2 = db.query(Product).filter(Product.merchant_id == 2).first()
        if not p2:
            p2 = Product(
                merchant_id=2,
                name="Tenant 2 Exclusive Widget",
                price=500.0,
                category="widget",
                tags="widget,tenant2",
                use_cases="demo",
                inventory=5,
            )
            db.add(p2)
            db.commit()

        response = client.get("/ai/catalog?merchant_id=2")
        assert response.status_code == 200
        data = response.json()

        assert data["merchant"]["id"] == 2
        # Merchant 2 should only see Merchant 2's products
        for item in data["items"]:
            assert "ProBook 14 Laptop" not in item["name"]
    finally:
        db.close()
