from pydantic import BaseModel, Field


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


class ProductCreate(BaseModel):
    name: str
    price: float = Field(gt=0, description="Price in INR")
    category: str
    tags: list[str] = []
    use_cases: list[str] = []
    compatible_products: list[int] = []
    upsell_products: list[int] = []
    inventory: int = Field(default=10, ge=0)