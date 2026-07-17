# backend/app/agents/max/agent.py

from backend.app.agents.base_agent import BaseAgent
from backend.app.agents.companion_prompts import COMPANION_PROMPTS, TAVUS_PROMPTS


class MaxAgent(BaseAgent):

    def __init__(self):
        super().__init__(name="Max")

    def get_prompt(self) -> str:
        return COMPANION_PROMPTS["Max"]

    def get_tavus_prompt(self) -> str:
        return TAVUS_PROMPTS["Max"]