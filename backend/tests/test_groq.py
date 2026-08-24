from app.agents.groq_provider import GroqProvider


provider = GroqProvider()

response = provider.generate(
    "Respond with exactly: RazorGrow Groq connection works."
)

print(response)