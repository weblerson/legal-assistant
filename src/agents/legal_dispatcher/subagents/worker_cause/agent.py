from google.adk.agents import LlmAgent

from .tools import fetch_worker_law

root_agent = LlmAgent(
    name="WorkerLawAgent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the Brazilian worker law.",
    instruction="""
        Your job is to answer questions about the worker law to the user.

        Make sure to always reference your responses based on the
        provided context
    """,
    tools=[fetch_worker_law],
)
