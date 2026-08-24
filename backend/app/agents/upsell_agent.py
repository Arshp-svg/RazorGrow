from app.agents.groq_provider import GroqProvider
from app.schemas.upsell import UpsellResponse


class UpsellAgent:
    def __init__(self, provider: GroqProvider | None = None):
        self.provider = provider or GroqProvider()

    def explain(
        self,
        result: UpsellResponse,
    ) -> str:
        if result.upsell is None:
            return "No suitable upsell is currently available."

        prompt = f"""
You are a shopping upsell explanation assistant.

Explain the provided upsell using ONLY the supplied data.

Original product:
Name: {result.original_product_name}
Price: {result.original_value}

Upsell product:
Name: {result.upsell.name}
Price: {result.upsell.price}
Inventory: {result.upsell.inventory}
Score: {result.upsell.score}

Rules:
- Only mention facts explicitly present above.
- Do not infer why the products are compatible.
- Do not call the upsell an accessory unless that is explicitly provided.
- Do not claim the upsell complements the original product.
- Do not invent product features.
- Do not invent specifications.
- Do not change prices, inventory, or scores.
- Do not claim the customer accepted the upsell.
- Do not mention any other products.
- Keep the explanation concise.
- Return plain text only.

You may mention the original product name and price,
the upsell name, price, inventory, and score.
"""

        return self.provider.generate(prompt)