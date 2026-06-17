from backend.app.agents.registry import AGENTS


def companion_node(state):

    companion_name = state["companion_name"]

    agent = AGENTS.get(
        companion_name
    )

    if agent:
        prompt = agent.get_prompt()
    else:
        prompt = (
            "You are a helpful AI assistant."
        )

    profile = state.get(
        "user_profile",
        {}
    )

    profile_context = f"""
    Age: {profile.get('age', 'Unknown')}
    Occupation: {profile.get('occupation', 'Unknown')}
    Country: {profile.get('country', 'Unknown')}
    Goals: {profile.get('goals', 'Unknown')}
    Interests: {profile.get('interests', 'Unknown')}
    """

    personalized_prompt = f"""
    {prompt}

    USER PROFILE

    {profile_context}

    Use the user's onboarding profile
    to personalize your responses.

    If the user asks about themselves,
    their goals, interests, occupation,
    country or background,
    use this information.
    """

    return {
        **state,
        "system_prompt":
            personalized_prompt
    }