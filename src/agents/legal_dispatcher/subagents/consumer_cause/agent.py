from google.adk.agents import LlmAgent

from .tools import fetch_consumer_law

root_agent = LlmAgent(
    name="ConsumerLawAgent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the Brazilian consumer law.",
    instruction="""
        Your job is to answer questions about the consumer law to the user.

        Make sure to always reference your responses based on the
        provided context
    """,
    tools=[fetch_consumer_law],
)
