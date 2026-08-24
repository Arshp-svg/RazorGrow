from sqlalchemy.orm import Session
from app.schemas.upsell import UpsellItem, UpsellResponse
from app.models.models import Product


def parse_product_ids(value: str | None) -> list[int]:
    if not value:
        return []

    ids = []

    for item in value.split(","):
        item = item.strip()

        if item.isdigit():
            ids.append(int(item))

    return ids


def find_upsell_candidates(
    db: Session,
    product: Product,
) -> list[Product]:
    upsell_ids = parse_product_ids(
        product.upsell_products
    )

    if not upsell_ids:
        return []

    candidates = (
        db.query(Product)
        .filter(
            Product.id.in_(upsell_ids),
            Product.inventory > 0,
        )
        .all()
    )

    # Preserve the order defined by upsell_products.
    candidates_by_id = {
        candidate.id: candidate
        for candidate in candidates
    }

    return [
        candidates_by_id[product_id]
        for product_id in upsell_ids
        if product_id in candidates_by_id
    ]
    
def score_upsell(
    base_product: Product,
    candidate: Product,
) -> float:
    score = 0.0

    # Explicit catalog upsell relationship.
    score += 50

    # Compatibility relationship adds further confidence.
    compatible_ids = parse_product_ids(
        base_product.compatible_products
    )

    if candidate.id in compatible_ids:
        score += 30

    # Prefer lower-cost add-ons for easier acceptance.
    if base_product.price > 0:
        price_ratio = candidate.price / base_product.price
        score += max(0, 20 - (price_ratio * 20))

    # Only in-stock candidates reach this function.
    if candidate.inventory > 0:
        score += min(candidate.inventory, 10)

    return score


def rank_upsell_candidates(
    base_product: Product,
    candidates: list[Product],
) -> list[Product]:
    return sorted(
        candidates,
        key=lambda candidate: score_upsell(
            base_product,
            candidate,
        ),
        reverse=True,
    )
    
    
def recommend_upsell(
    db: Session,
    product_id: int,
) -> UpsellResponse:
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise ValueError(
            f"Product {product_id} not found"
        )

    candidates = find_upsell_candidates(
        db,
        product,
    )

    ranked_candidates = rank_upsell_candidates(
        product,
        candidates,
    )

    if not ranked_candidates:
        return UpsellResponse(
            original_product_id=product.id,
            original_product_name=product.name,
            original_value=product.price,
            upsell=None,
            upsell_value=0,
            accepted=False,
        )

    candidate = ranked_candidates[0]

    upsell = UpsellItem(
        product_id=candidate.id,
        name=candidate.name,
        price=candidate.price,
        inventory=candidate.inventory,
        score=score_upsell(
            product,
            candidate,
        ),
    )

    return UpsellResponse(
        original_product_id=product.id,
        original_product_name=product.name,
        original_value=product.price,
        upsell=upsell,
        upsell_value=candidate.price,
        accepted=False,
    )