import json

from app.agents.groq_provider import GroqProvider
from app.schemas.intent import ShoppingIntent


class IntentAgent:
    def __init__(self, provider: GroqProvider | None = None):
        self.provider = provider or GroqProvider()

    def extract(self, user_message: str) -> ShoppingIntent:
        prompt = f"""
    You are a shopping intent extraction system.

    Extract ONLY the customer's shopping requirements.
    Do not recommend products.
    Do not invent information.
    Do not make purchasing decisions.

    Return ONLY valid JSON with exactly these fields:
    - category: string or null
    - budget: positive number or null
    - use_case: string or null
    - constraints: array of strings

    Customer message:
    {user_message}
    """

        raw_response = self.provider.generate(
    prompt,
    json_mode=True,
)

        try:
            data = json.loads(raw_response)
            return ShoppingIntent.model_validate(data)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid intent response: LLM did not return valid JSON."
            ) from exc

        except Exception as exc:
            raise ValueError(
                "Invalid intent response: JSON does not match ShoppingIntent."
            ) from exc