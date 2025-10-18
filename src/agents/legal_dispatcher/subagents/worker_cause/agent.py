from google.adk.agents import LlmAgent

from .tools import fetch_worker_law

root_agent = LlmAgent(
    name="WorkerLawAgent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the Brazilian worker law.",
    instruction="""
        Your job is to answer questions about the worker law to the user.

        You must always call the `fetch_worker_law` tool to ground all
        your responses.

        When responding an user question, you MUST always write at the end
        of the text the related articles, explaining why these articles
        helps the user
    """,
    tools=[fetch_worker_law],
)
