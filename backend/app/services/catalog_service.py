from sqlalchemy.orm import Session

from app.models.models import Product
from app.schemas.intent import ShoppingIntent


def parse_list(value: str) -> list[str]:
    if not value:
        return []

    return [
        item.strip().lower()
        for item in value.split(",")
        if item.strip()
    ]


def find_candidates(
    db: Session,
    intent: ShoppingIntent,
) -> list[Product]:
    products = (
        db.query(Product)
        .filter(Product.inventory > 0)
        .all()
    )

    candidates = []

    for product in products:
        if intent.category:
            if product.category.lower() != intent.category.lower():
                continue

        if intent.budget is not None:
            if product.price > intent.budget:
                continue

        if intent.use_case:
            use_case = intent.use_case.lower()

            product_use_cases = parse_list(product.use_cases)
            product_tags = parse_list(product.tags)

            if (
                use_case not in product_use_cases
                and use_case not in product_tags
            ):
                continue

        candidates.append(product)

    return candidates

def score_product(
    product: Product,
    intent: ShoppingIntent,
) -> float:
    score = 0.0

    # Prefer products that use more of the customer's budget
    # without exceeding it.
    if intent.budget is not None and intent.budget > 0:
        budget_ratio = product.price / intent.budget
        score += budget_ratio * 40

    # Strong match for the requested use case.
    if intent.use_case:
        use_case = intent.use_case.lower()

        product_use_cases = parse_list(product.use_cases)
        product_tags = parse_list(product.tags)

        if use_case in product_use_cases:
            score += 30

        if use_case in product_tags:
            score += 10

    # Reward products with more inventory.
    if product.inventory > 0:
        score += min(product.inventory, 20)

    return score

def rank_candidates(
    candidates: list[Product],
    intent: ShoppingIntent,
) -> list[Product]:
    return sorted(
        candidates,
        key=lambda product: score_product(product, intent),
        reverse=True,
    )