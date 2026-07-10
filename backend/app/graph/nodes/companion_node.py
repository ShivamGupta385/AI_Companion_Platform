from backend.app.agents.registry import AGENTS


def companion_node(state):
    companion_name = state["companion_name"]

    agent = AGENTS.get(companion_name)

    if agent:
        prompt = agent.get_prompt()
    else:
        prompt = "You are a helpful AI assistant."

    profile = state.get("user_profile", {})

    profile_context = f"""
Nickname: {profile.get('nickname', 'Not provided')}
Age: {profile.get('age', 'Not provided')}
Primary Focus: {profile.get('current_focus', 'Not provided')}
Preferred Tone: {profile.get('preferred_tone', 'Not provided')}

Goals: {profile.get('goals', 'Not provided')}
Interests & Hobbies: {profile.get('interests', 'Not provided')}
Favorite Topics: {profile.get('favorite_topics', 'Not provided')}
Current Challenge: {profile.get('current_challenge', 'Not provided')}
Country: {profile.get('country', 'Not provided')}
"""

    personalized_prompt = f"""
{prompt}

USER PROFILE:
{profile_context}
"""

    return {
        **state,
        "system_prompt": personalized_prompt
    }