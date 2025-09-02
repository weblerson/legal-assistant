from google.adk.agents import Agent

from .tools import fetch_civil_law

root_agent = Agent(
    name="CivilLawAgent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the Brazilian civil law.",
    instruction="""
        Your job is to answer questions about the civil law to the user.

        Make sure to always reference your responses based on the
        provided context
    """,
    tools=[fetch_civil_law],
)
