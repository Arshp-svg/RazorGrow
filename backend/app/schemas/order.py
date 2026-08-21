from pydantic import BaseModel, Field


class TestOrderRequest(BaseModel):
    amount: int = Field(gt=0)