from google.adk.agents import LlmAgent

from .tools import fetch_consumer_law

root_agent = LlmAgent(
    name="ConsumerLawAgent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the Brazilian consumer law.",
    instruction="""
        Your job is to answer questions about the consumer law to the user.

        You must always call the `fetch_consumer_law` tool to ground all
        your responses.
    """,
    tools=[fetch_consumer_law],
)
