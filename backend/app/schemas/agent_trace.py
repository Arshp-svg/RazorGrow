from typing import Any
from pydantic import BaseModel


class AgentChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class AgentChatResponse(BaseModel):
    reply: str
    execution_id: int
    correlation_id: str
    session_id: str
    intent: dict[str, Any] | None = None
    recommended_product: dict[str, Any] | None = None
    upsell_product: dict[str, Any] | None = None
    total_latency_ms: float


class ToolCallSummary(BaseModel):
    id: int
    tool_name: str
    input_data: Any | None = None
    output_data: Any | None = None
    status: str
    latency_ms: float
    policy_result: str | None = None
    created_at: str | None = None


class ExecutionTraceResponse(BaseModel):
    execution_id: int
    merchant_id: int
    session_id: str
    correlation_id: str
    intent: str | None = None
    status: str
    created_at: str | None = None
    completed_at: str | None = None
    total_latency_ms: float | None = 0.0
    tool_calls_count: int
    tool_calls: list[ToolCallSummary]
