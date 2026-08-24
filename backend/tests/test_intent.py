from app.agents.intent_agent import IntentAgent


agent = IntentAgent()

intent = agent.extract(
    "I need a laptop for programming under 70000 rupees. "
    "It should be portable and have good performance."
)

print(intent.model_dump())