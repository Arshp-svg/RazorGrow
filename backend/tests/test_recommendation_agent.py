from app.agents.intent_agent import IntentAgent
from app.db.database import SessionLocal
from app.services.recommendation_service import recommend_products
from app.agents.recommendation_agent import RecommendationAgent


db = SessionLocal()

try:
    message = (
        "I need a laptop for programming under 70000 rupees. "
        "It should be portable."
    )

    intent = IntentAgent().extract(message)

    recommendations = recommend_products(
        db,
        intent,
    )

    explanation = RecommendationAgent().explain(
        intent,
        recommendations,
    )

    print("Recommendations:")
    for item in recommendations.recommendations:
        print(
            item.name,
            item.price,
            item.inventory,
        )

    print("\nExplanation:")
    print(explanation)

finally:
    db.close()