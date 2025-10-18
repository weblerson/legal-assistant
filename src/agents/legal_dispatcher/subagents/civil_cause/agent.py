from google.adk.agents import Agent

from .tools import fetch_civil_law

root_agent = Agent(
    name="CivilLawAgent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the Brazilian civil law.",
    instruction="""
        Your job is to answer questions about the civil law to the user.

        You must always call the `fetch_civil_law` tool to ground all
        your responses.

        When responding an user question, you MUST always write at the end
        of the text the related articles, explaining why these articles
        helps the user.
    """,
    tools=[fetch_civil_law],
)
