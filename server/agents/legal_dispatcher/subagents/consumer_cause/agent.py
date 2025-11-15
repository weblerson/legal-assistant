from google.adk.agents import LlmAgent

root_agent = LlmAgent(
    name="ConsumerLawAgent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the Brazilian consumer law.",
    instruction="""
        Your job is to answer questions about the consumer law to the user.

        When responding an user question, you MUST always write at the end
        of the text the related articles, explaining why these articles
        helps the user
    """,
)
