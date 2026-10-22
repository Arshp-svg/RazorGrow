import json
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.models import AgentExecution, ToolCall

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "razorpay_key_secret",
    "groq_api_key",
    "jwt_secret_key",
    "card_number",
    "cvv",
    "pan",
    "pin",
    "authorization",
}

CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
SECRET_KEY_REGEX = re.compile(r"\b(?:rzp_(?:test|live)_[0-9a-zA-Z]{14,24}|gsk_[0-9a-zA-Z]{20,60})\b")


def sanitize_data(data: Any) -> Any:
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_data(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, str):
        masked = CARD_REGEX.sub("[REDACTED_CARD]", data)
        masked = SECRET_KEY_REGEX.sub("[REDACTED_SECRET]", masked)
        return masked
    return data


def to_sanitized_json(data: Any) -> str:
    if data is None:
        return ""
    try:
        sanitized = sanitize_data(data)
        return json.dumps(sanitized, default=str)
    except Exception:
        return str(sanitize_data(data))


def start_execution(
    db: Session,
    merchant_id: int,
    session_id: str,
    intent: str | None = None,
    correlation_id: str | None = None,
) -> AgentExecution:
    corr_id = correlation_id or f"corr_{uuid.uuid4().hex}"

    execution = AgentExecution(
        merchant_id=merchant_id,
        session_id=session_id,
        correlation_id=corr_id,
        intent=intent,
        status="in_progress",
        created_at=datetime.now(timezone.utc),
        total_latency_ms=0.0,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    return execution


def record_tool_call(
    db: Session,
    execution_id: int,
    tool_name: str,
    input_data: Any = None,
    output_data: Any = None,
    status: str = "success",
    latency_ms: float = 0.0,
    policy_result: str | None = None,
) -> ToolCall:
    tool_call = ToolCall(
        execution_id=execution_id,
        tool_name=tool_name,
        input_data=to_sanitized_json(input_data),
        output_data=to_sanitized_json(output_data),
        status=status,
        latency_ms=round(latency_ms, 2),
        policy_result=policy_result,
        created_at=datetime.now(timezone.utc),
    )
    db.add(tool_call)

    # Accumulate latency on execution
    execution = (
        db.query(AgentExecution)
        .filter(AgentExecution.id == execution_id)
        .first()
    )
    if execution:
        current_latency = execution.total_latency_ms or 0.0
        execution.total_latency_ms = round(current_latency + latency_ms, 2)

    db.commit()
    db.refresh(tool_call)

    return tool_call


def complete_execution(
    db: Session,
    execution_id: int,
    status: str = "completed",
) -> AgentExecution | None:
    execution = (
        db.query(AgentExecution)
        .filter(AgentExecution.id == execution_id)
        .first()
    )
    if not execution:
        return None

    execution.status = status
    execution.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(execution)

    return execution


def get_execution_trace(
    db: Session,
    execution_id: int,
    merchant_id: int,
) -> dict | None:
    execution = (
        db.query(AgentExecution)
        .filter(
            AgentExecution.id == execution_id,
            AgentExecution.merchant_id == merchant_id,
        )
        .first()
    )

    if not execution:
        return None

    calls = []
    for call in execution.tool_calls:
        calls.append({
            "id": call.id,
            "tool_name": call.tool_name,
            "input_data": json.loads(call.input_data) if call.input_data else None,
            "output_data": json.loads(call.output_data) if call.output_data else None,
            "status": call.status,
            "latency_ms": call.latency_ms,
            "policy_result": call.policy_result,
            "created_at": call.created_at.isoformat() if call.created_at else None,
        })

    return {
        "execution_id": execution.id,
        "merchant_id": execution.merchant_id,
        "session_id": execution.session_id,
        "correlation_id": execution.correlation_id,
        "intent": execution.intent,
        "status": execution.status,
        "created_at": execution.created_at.isoformat() if execution.created_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "total_latency_ms": execution.total_latency_ms,
        "tool_calls_count": len(calls),
        "tool_calls": calls,
    }


def list_merchant_executions(
    db: Session,
    merchant_id: int,
    limit: int = 50,
) -> list[dict]:
    executions = (
        db.query(AgentExecution)
        .filter(AgentExecution.merchant_id == merchant_id)
        .order_by(AgentExecution.id.desc())
        .limit(limit)
        .all()
    )

    result = []
    for exc in executions:
        result.append({
            "id": exc.id,
            "session_id": exc.session_id,
            "correlation_id": exc.correlation_id,
            "intent": exc.intent,
            "status": exc.status,
            "created_at": exc.created_at.isoformat() if exc.created_at else None,
            "completed_at": exc.completed_at.isoformat() if exc.completed_at else None,
            "total_latency_ms": exc.total_latency_ms,
            "tool_calls_count": len(exc.tool_calls),
        })
    return result
