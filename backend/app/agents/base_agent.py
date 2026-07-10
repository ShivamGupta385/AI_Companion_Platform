# backend/app/agents/base_agent.py


class BaseAgent:

    def __init__(self, name: str = ""):
        self.name = name

    def get_prompt(self) -> str:
        raise NotImplementedError

    def get_tavus_prompt(self) -> str:
        return ""