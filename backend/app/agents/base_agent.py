# backend/app/agents/base_agent.py

class BaseAgent:

    def get_prompt(self):
        raise NotImplementedError