from datetime import datetime

from pydantic import BaseModel


class ApprovalRequestResponse(BaseModel):
    id: int
    merchant_id: int
    order_id: int
    status: str
    requested_at: datetime
    expires_at: datetime | None = None
    decided_at: datetime | None = None
    decided_by_user_id: int | None = None
    decision_reason: str | None = None


class ApprovalDecisionRequest(BaseModel):
    reason: str | None = None
