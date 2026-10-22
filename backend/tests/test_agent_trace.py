import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.main import app
from app.models.models import AgentExecution, Merchant, MerchantMembership, Product, ToolCall, User
from app.services.auth_service import create_access_token, hash_password
from app.services.trace_service import (
    complete_execution,
    get_execution_trace,
    record_tool_call,
    sanitize_data,
    start_execution,
)

client = TestClient(app)


def test_sanitize_data_masks_sensitive_values():
    raw_payload = {
        "user_email": "merchant@example.com",
        "password": "supersecretpassword123",
        "api_key": "rzp_test_1234567890ABCD",
        "card_info": {
            "card_number": "4111 2222 3333 4444",
            "cvv": "123",
            "notes": "Payment using card 4111222233334444 and key gsk_abcdef1234567890abcdef1234567890",
        },
    }

    sanitized = sanitize_data(raw_payload)

    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["card_info"]["card_number"] == "[REDACTED]"
    assert sanitized["card_info"]["cvv"] == "[REDACTED]"
    assert "4111" not in sanitized["card_info"]["notes"]
    assert "[REDACTED_CARD]" in sanitized["card_info"]["notes"]
    assert "[REDACTED_SECRET]" in sanitized["card_info"]["notes"]
    assert sanitized["user_email"] == "merchant@example.com"


def test_trace_lifecycle_records_execution_and_tool_calls():
    db = SessionLocal()
    try:
        execution = start_execution(
            db=db,
            merchant_id=1,
            session_id=f"sess_{uuid.uuid4().hex[:8]}",
            intent="I need a gaming laptop under 80000",
        )

        assert execution.id is not None
        assert execution.status == "in_progress"
        assert execution.total_latency_ms == 0.0

        # Record tool call 1
        call1 = record_tool_call(
            db=db,
            execution_id=execution.id,
            tool_name="extract_intent",
            input_data={"message": "I need a gaming laptop under 80000"},
            output_data={"category": "laptop", "budget": 80000},
            status="success",
            latency_ms=120.5,
        )
        assert call1.id is not None
        assert call1.latency_ms == 120.5

        # Record tool call 2
        call2 = record_tool_call(
            db=db,
            execution_id=execution.id,
            tool_name="search_catalog",
            input_data={"category": "laptop", "budget": 80000},
            output_data={"results": 2},
            status="success",
            latency_ms=35.2,
        )
        assert call2.id is not None

        # Complete execution
        completed = complete_execution(db, execution.id, status="completed")
        assert completed.status == "completed"
        assert completed.completed_at is not None
        assert completed.total_latency_ms == 155.7

        # Retrieve full reconstructed trace
        trace = get_execution_trace(db, execution.id, merchant_id=1)
        assert trace is not None
        assert trace["execution_id"] == execution.id
        assert trace["tool_calls_count"] == 2
        assert trace["tool_calls"][0]["tool_name"] == "extract_intent"
        assert trace["tool_calls"][1]["tool_name"] == "search_catalog"
    finally:
        db.close()


def test_trace_tenant_isolation_prevents_cross_tenant_access():
    db = SessionLocal()
    try:
        # Create execution under merchant 1
        execution = start_execution(
            db=db,
            merchant_id=1,
            session_id="tenant-test-session",
            intent="Test merchant 1 execution",
        )

        # Attempt to access trace with merchant 2
        trace_for_merchant_2 = get_execution_trace(
            db=db,
            execution_id=execution.id,
            merchant_id=2,
        )
        assert trace_for_merchant_2 is None

        # Access trace with merchant 1 succeeds
        trace_for_merchant_1 = get_execution_trace(
            db=db,
            execution_id=execution.id,
            merchant_id=1,
        )
        assert trace_for_merchant_1 is not None
        assert trace_for_merchant_1["execution_id"] == execution.id
    finally:
        db.close()


def create_auth_token_for_merchant(db, merchant_id: int = 1) -> str:
    user = User(
        email=f"trace_test_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("testpassword123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    membership = MerchantMembership(
        merchant_id=merchant_id,
        user_id=user.id,
        role="OWNER",
    )
    db.add(membership)
    db.commit()

    return create_access_token(user_id=user.id)


def test_agent_chat_api_end_to_end_traced():
    db = SessionLocal()
    try:
        token = create_auth_token_for_merchant(db, merchant_id=1)

        response = client.post(
            "/agent/chat",
            json={"message": "I need a laptop for coding under 70000"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "execution_id" in data
        assert "correlation_id" in data
        assert data["correlation_id"].startswith("corr_")

        exec_id = data["execution_id"]

        # Now query the trace endpoint to verify full reconstruction
        trace_resp = client.get(
            f"/agent/executions/{exec_id}/trace",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert trace_resp.status_code == 200
        trace_data = trace_resp.json()
        assert trace_data["execution_id"] == exec_id
        assert trace_data["status"] == "completed"
        assert trace_data["tool_calls_count"] >= 2
        tool_names = [call["tool_name"] for call in trace_data["tool_calls"]]
        assert "extract_intent" in tool_names
        assert "search_catalog" in tool_names
    finally:
        db.close()
