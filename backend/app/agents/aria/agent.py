# backend/app/agents/aria/agent.py

from backend.app.agents.base_agent import BaseAgent
from backend.app.agents.companion_prompts import COMPANION_PROMPTS, TAVUS_PROMPTS


class AriaAgent(BaseAgent):

    def __init__(self):
        super().__init__(name="Aria")

    def get_prompt(self) -> str:
        return COMPANION_PROMPTS["Aria"]

    def get_tavus_prompt(self) -> str:
        return TAVUS_PROMPTS["Aria"]