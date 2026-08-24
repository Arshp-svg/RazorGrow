from pydantic import BaseModel, Field


class ShoppingIntent(BaseModel):
    category: str | None = None
    budget: float | None = Field(default=None, gt=0)
    use_case: str | None = None
    constraints: list[str] = Field(default_factory=list)
    
class IntentRequest(BaseModel):
    message: str