from sqlalchemy.orm import Session

from app.schemas.intent import ShoppingIntent
from app.schemas.recommendation import (
    RecommendationItem,
    RecommendationResponse,
)
from app.services.catalog_service import (
    find_candidates,
    rank_candidates,
    score_product,
)


def recommend_products(
    db: Session,
    intent: ShoppingIntent,
) -> RecommendationResponse:
    candidates = find_candidates(db, intent)

    ranked_candidates = rank_candidates(
        candidates,
        intent,
    )

    recommendations = [
        RecommendationItem(
            product_id=product.id,
            name=product.name,
            price=product.price,
            category=product.category,
            inventory=product.inventory,
            score=score_product(product, intent),
        )
        for product in ranked_candidates
    ]

    return RecommendationResponse(
        intent=intent.model_dump(),
        recommendations=recommendations,
    )