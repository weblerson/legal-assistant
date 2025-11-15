from google.adk.agents import Agent

root_agent = Agent(
    name="CivilLawAgent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the Brazilian civil law.",
    instruction="""
        Your job is to answer questions about the civil law to the user.

        When responding an user question, you MUST always write at the end
        of the text the related articles, explaining why these articles
        helps the user.
    """,
)
