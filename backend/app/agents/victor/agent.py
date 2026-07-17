# backend/app/agents/victor/agent.py

from backend.app.agents.base_agent import BaseAgent
from backend.app.agents.companion_prompts import COMPANION_PROMPTS, TAVUS_PROMPTS


class VictorAgent(BaseAgent):

    def __init__(self):
        super().__init__(name="Victor")

    def get_prompt(self) -> str:
        return COMPANION_PROMPTS["Victor"]

    def get_tavus_prompt(self) -> str:
        return TAVUS_PROMPTS["Victor"]