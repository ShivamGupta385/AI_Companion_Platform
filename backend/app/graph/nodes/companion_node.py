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
Age: {profile.get('age', 'Unknown')}
Occupation: {profile.get('occupation', 'Unknown')}
Country: {profile.get('country', 'Unknown')}
Goals: {profile.get('goals', 'Unknown')}
Interests: {profile.get('interests', 'Unknown')}
"""

    personalized_prompt = f"""
{prompt}

USER PROFILE:
{profile_context}

You are chatting with the user inside an ongoing conversation thread.

IMPORTANT BEHAVIOR RULES:

1. Use the user's onboarding profile to personalize your responses.
2. If the user asks about themselves, their goals, interests, occupation, country, or background, use the onboarding profile above.
3. You will also receive conversation memory from the current chat thread.
4. Use that conversation memory to answer follow-up questions naturally and continue the discussion.
5. If the user asks things like:
   - "Do you remember what we discussed?"
   - "What did we do last time?"
   - "Continue from our previous conversation"
   - "What did I tell you earlier?"
   then use the provided conversation memory from this thread.
6. Do NOT say "I don't have access to previous conversations" if conversation memory is available in the prompt.
7. If there is no relevant memory in the current thread, say so naturally, for example:
   - "I don't see anything earlier in this chat about that yet."
   - "We haven't discussed that in this conversation so far."
8. Maintain the companion's personality while still being accurate to the chat history and user profile.
"""

    return {
        **state,
        "system_prompt": personalized_prompt
    }