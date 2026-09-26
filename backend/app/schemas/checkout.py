from pydantic import BaseModel


class CheckoutConfirmationRequest(BaseModel):
    confirmed: bool
    idempotency_key: str


class CheckoutConfirmationResponse(BaseModel):
    cart_id: int
    total: float
    confirmed: bool