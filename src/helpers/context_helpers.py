from contextvars import ContextVar

from google.adk.agents import LlmAgent

agent_context_var: ContextVar[LlmAgent] = ContextVar("agent", default=None)
