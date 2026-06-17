from typing import TypedDict


class CompanionState(TypedDict, total=False):
    conversation_id: str
    companion_name: str
    user_message: str
    user_profile: dict

    system_prompt: str
    history: list
    response: str