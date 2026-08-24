from pydantic import BaseModel


class RecommendationItem(BaseModel):
    product_id: int
    name: str
    price: float
    category: str
    inventory: int
    score: float


class RecommendationResponse(BaseModel):
    intent: dict
    recommendations: list[RecommendationItem]
    explanation: str | None = None