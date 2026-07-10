# backend/app/agents/rene/agent.py

from backend.app.agents.base_agent import BaseAgent
from backend.app.agents.companion_prompts import COMPANION_PROMPTS, TAVUS_PROMPTS


class ReneAgent(BaseAgent):

    def __init__(self):
        super().__init__(name="Rene")

    def get_prompt(self) -> str:
        return COMPANION_PROMPTS["Rene"]

    def get_tavus_prompt(self) -> str:
        return TAVUS_PROMPTS["Rene"]