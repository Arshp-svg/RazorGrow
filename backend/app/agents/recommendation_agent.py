from app.agents.groq_provider import GroqProvider
from app.schemas.intent import ShoppingIntent
from app.schemas.recommendation import RecommendationResponse


class RecommendationAgent:
    def __init__(self, provider: GroqProvider | None = None):
        self.provider = provider or GroqProvider()

    def explain(
        self,
        intent: ShoppingIntent,
        recommendations: RecommendationResponse,
    ) -> str:
        products = []

        for item in recommendations.recommendations:
            products.append(
                {
                    "name": item.name,
                    "price": item.price,
                    "category": item.category,
                    "inventory": item.inventory,
                    "score": item.score,
                }
            )

        prompt = f"""
You are a shopping recommendation explanation assistant.

Explain the recommendations below using ONLY the provided data.

Do not:
- invent products
- invent prices
- invent inventory
- change prices
- claim features that are not provided
- recommend products outside the provided list

Customer intent:
{intent.model_dump_json()}

Grounded recommendations:
{products}

Write 2-4 short sentences explaining the recommendations.

You may mention:
- the customer's requested category
- the customer's budget
- each product's name
- each product's price
- each product's inventory
- each product's recommendation score
- the customer's stated use case

Do NOT mention any other product feature or specification.

Do NOT infer that a product is portable, powerful, lightweight,
large, small, fast, or suitable for a specific task unless that exact
fact is present in the provided data.

Return plain text only.
"""

        return self.provider.generate(prompt)