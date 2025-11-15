from google.adk.agents import LlmAgent

root_agent = LlmAgent(
    name="WorkerLawAgent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the Brazilian worker law.",
    instruction="""
        Your job is to answer questions about the worker law to the user.

        When responding an user question, you MUST always write at the end
        of the text the related articles, explaining why these articles
        helps the user
    """,
)
