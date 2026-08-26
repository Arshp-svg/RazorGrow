from pydantic import BaseModel


class CheckoutConfirmationRequest(BaseModel):
    confirmed: bool


class CheckoutConfirmationResponse(BaseModel):
    cart_id: int
    total: float
    confirmed: bool