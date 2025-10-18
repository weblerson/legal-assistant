from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

from .subagents.civil_cause.agent import root_agent as civil_law_agent
from .subagents.consumer_cause.agent import root_agent as consumer_law_agent
from .subagents.worker_cause.agent import root_agent as worker_law_agent


async def create_temporary_session_async(
        app_name: str,
        user_id: str,
        session_id: str,
) -> InMemorySessionService:
    temp_service = InMemorySessionService()
    await temp_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    return temp_service


async def create_runner_async(
        app_name: str,
        session_service: InMemorySessionService,
        agent: LlmAgent,
) -> Runner:
    runner = Runner(
        app_name=app_name,
        session_service=session_service,
        agent=agent,
    )

    return runner


# TODO: no sistema linear, x1 de n gera a saída y1 de n
async def create_root_agent_async() -> LlmAgent:
    root_agent = LlmAgent(
        name="LegalAssistant",
        model="gemini-2.0-flash",
        instruction="""
            Route user requests:
            Use Civil Law Agent for questions about the Brazilian civil law,
            Consumer Law Agent for questions about the Brazilian consumer law.
            Worker Law Agent for questions about the Brazilian worker law.

            For any other questions, reply that you are not able to respond
            properly.
        """,
        description="Main entrypoint for legal questions",
        # allow_transfer=True is often implicit with sub_agents in AutoFlow
        sub_agents=[civil_law_agent, consumer_law_agent, worker_law_agent]
    )

    return root_agent
