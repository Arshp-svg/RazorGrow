from app.agents.intent_agent import IntentAgent
from app.agents.llm_provider import LLMProvider


class BadProvider(LLMProvider):
    def generate(self, prompt: str, json_mode: bool = False) -> str:
        return "This is not valid JSON."


agent = IntentAgent(provider=BadProvider())

try:
    agent.extract("I need a laptop")
except ValueError as error:
    print("Rejected safely:", error)
else:
    raise AssertionError("Invalid LLM output was not rejected")