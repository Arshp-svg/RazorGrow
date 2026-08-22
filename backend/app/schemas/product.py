from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    category: str
    tags: list[str]
    use_cases: list[str]
    compatible_products: list[int]
    upsell_products: list[int]
    inventory: int