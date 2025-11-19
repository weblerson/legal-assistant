import typing

from google.adk.agents import LlmAgent
from google.adk.sessions import (
    BaseSessionService,
    DatabaseSessionService,
    Session,
)
from google.adk.runners import Runner

from .subagents.civil_cause.agent import root_agent as civil_law_agent
from .subagents.consumer_cause.agent import root_agent as consumer_law_agent
from .subagents.worker_cause.agent import root_agent as worker_law_agent


async def instantiate_database_session_service(
        db_url: str,
) -> DatabaseSessionService:
    return DatabaseSessionService(db_url)


async def retrieve_session_async(
        database_service: DatabaseSessionService,
        app_name: str,
        user_id: str,
        session_id: str,
) -> typing.Optional[Session]:
    session = await database_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    if session is None:
        return None

    return session


async def create_session_async(
        database_service: DatabaseSessionService,
        app_name: str,
        user_id: str,
        session_id: str,
) -> Session:
    await database_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    created_session = await retrieve_session_async(
        database_service=database_service,
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    if created_session is None:
        raise ValueError("Something went wrong when creating a new session.")

    return created_session


async def delete_session_async(
        database_session_service: DatabaseSessionService,
        app_name: str,
        user_id: str,
        session_id: str,
) -> None:
    await database_session_service.delete_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )


async def create_runner_async(
        app_name: str,
        session_service: BaseSessionService,
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
        model="gemini-2.5-flash",
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
