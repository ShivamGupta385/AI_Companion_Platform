# backend/app/agents/noor/agent.py

from backend.app.agents.base_agent import BaseAgent
from backend.app.agents.companion_prompts import COMPANION_PROMPTS, TAVUS_PROMPTS


class NoorAgent(BaseAgent):

    def __init__(self):
        super().__init__(name="Noor")

    def get_prompt(self) -> str:
        return COMPANION_PROMPTS["Noor"]

    def get_tavus_prompt(self) -> str:
        return TAVUS_PROMPTS["Noor"]