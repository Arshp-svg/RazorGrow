from pydantic import BaseModel, Field


class CreateCartRequest(BaseModel):
    customer_id: str | None = None


class AddCartItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemResponse(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class CartResponse(BaseModel):
    id: int
    customer_id: str | None
    status: str
    subtotal: float
    total: float
    items: list[CartItemResponse]