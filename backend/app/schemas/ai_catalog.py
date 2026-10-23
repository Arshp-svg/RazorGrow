from typing import Any
from pydantic import BaseModel, Field


class ProductCompatibilityItem(BaseModel):
    product_id: int
    name: str
    price: float
    category: str
    in_stock: bool


class AICatalogProductItem(BaseModel):
    id: int
    name: str
    price: float
    currency: str = "INR"
    category: str
    tags: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    availability: str
    inventory: int
    compatibility: list[ProductCompatibilityItem] = Field(default_factory=list)
    upsell_suggestions: list[ProductCompatibilityItem] = Field(default_factory=list)
    purchase_limits: dict[str, int] = Field(default_factory=dict)


class AICatalogPolicy(BaseModel):
    currency: str = "INR"
    max_transaction_amount: float
    max_discount_percent: float
    merchant_approval_threshold: float | None = None
    customer_confirmation_required: bool = True
    policy_version: int = 1


class AICatalogMerchant(BaseModel):
    id: int
    name: str
    status: str
    currency: str = "INR"


class AICatalogSummary(BaseModel):
    total_items: int
    categories: list[str]
    in_stock_items: int


class AICatalogResponse(BaseModel):
    protocol: str = "razorgrow-ai-commerce/v1.0"
    merchant: AICatalogMerchant
    commerce_policies: AICatalogPolicy
    catalog_summary: AICatalogSummary
    items: list[AICatalogProductItem]


class AIBuyerProcureRequest(BaseModel):
    merchant_id: int = 1
    query: str
    budget_limit: float | None = None
    product_id: int | None = None
    include_compatible_addon: bool = True
    auto_confirm: bool = True
    idempotency_key: str | None = None


class AIBuyerProcureResponse(BaseModel):
    status: str
    message: str
    execution_id: int | None = None
    session_id: str
    procurement_plan: dict[str, Any]
    cart_id: int | None = None
    order: dict[str, Any] | None = None
    approval_id: int | None = None
    policy_decision: dict[str, Any]


class AIBuyerScenario(BaseModel):
    id: str
    title: str
    description: str
    query: str
    budget_limit: float
    product_id: int | None = None
    include_compatible_addon: bool = True
    expected_outcome: str
