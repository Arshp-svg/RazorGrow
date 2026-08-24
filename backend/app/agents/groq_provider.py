from groq import Groq

from app.agents.llm_provider import LLMProvider
from app.config import settings


class GroqProvider(LLMProvider):
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    def generate(
        self,
        prompt: str,
        json_mode: bool = False,
    ) -> str:
        kwargs = {
            "model": "openai/gpt-oss-120b",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0,
            "max_tokens": 400,
        }

        if json_mode:
            kwargs["response_format"] = {
                "type": "json_object"
            }

        response = self.client.chat.completions.create(
            **kwargs
        )

        return response.choices[0].message.content or ""