from pydantic import BaseModel, Field


class UpsellItem(BaseModel):
    product_id: int
    name: str
    price: float
    inventory: int
    score: float


class UpsellResponse(BaseModel):
    original_product_id: int
    original_product_name: str
    original_value: float

    upsell: UpsellItem | None = None

    upsell_value: float = Field(default=0, ge=0)

    accepted: bool = False
    
class UpsellAcceptanceRequest(BaseModel):
    accepted: bool