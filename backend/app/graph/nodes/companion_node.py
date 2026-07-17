# backend/app/graph/nodes/companion_node.py

from backend.app.agents.registry import AGENTS


def companion_node(state):
    companion_name = state["companion_name"]

    agent = AGENTS.get(companion_name)

    if agent:
        prompt = agent.get_prompt()
    else:
        prompt = "You are a helpful AI assistant."

    profile = state.get("user_profile", {})

    # --------------------------------------------------
    # Try multiple possible name fields from onboarding
    # --------------------------------------------------
    user_name = (
        profile.get("name")
        or profile.get("full_name")
        or profile.get("first_name")
        or profile.get("username")
        or "Unknown"
    )

    profile_context = f"""
Name: {user_name}
Age: {profile.get('age', 'Unknown')}
Occupation: {profile.get('occupation', 'Unknown')}
Country: {profile.get('country', 'Unknown')}
Goals: {profile.get('goals', 'Unknown')}
Interests: {profile.get('interests', 'Unknown')}
"""

    # --------------------------------------------------
    # Cross-agent context (from cross_memory_node)
    # --------------------------------------------------
    cross_agent_context = state.get("cross_agent_context", "")
    cross_memory_section = ""

    if cross_agent_context and cross_agent_context.strip():
        cross_memory_section = f"""
{cross_agent_context}
"""

    personalized_prompt = f"""
{prompt}

USER PROFILE (background information, NOT conversation history):
{profile_context}
{cross_memory_section}
You are chatting with the user inside an ongoing conversation thread.

IMPORTANT BEHAVIOR RULES:

1. Use the USER PROFILE above to personalize your responses — it tells you who the user is (name, age, occupation, etc.).

2. The user's name is {user_name}. Use it naturally when appropriate — do NOT ask for their name if it's provided above.

3. CRITICAL DISTINCTION: The USER PROFILE is background data collected during onboarding. It is NOT a record of what was "discussed" or "talked about" in conversations. Do NOT say things like "we discussed your age" or "you mentioned you're a student" when referring to profile data — that data was not discussed, it was provided during signup.

4. If the user asks "what do you know about me?", you may reference BOTH the user profile AND any actual conversation memory available. But be honest about the source: "From your profile, I know you're a student" — NOT "we discussed that you're a student."

5. If the user asks about "earlier conversations", "what we discussed before", "what we talked about last time", or "do you remember" — ONLY look at:
   - THREAD CONVERSATION MEMORY (current chat)
   - LONG-TERM USER MEMORY
   - PAST CONVERSATION SUMMARIES
   Do NOT treat USER PROFILE data as conversation history.

6. If the user asks about previous conversations:
   - If PAST CONVERSATION SUMMARIES or LONG-TERM MEMORIES are present in your prompt, you MUST reference them. Say things like "Yes, we've talked about your internship at Astranova" or "In our past chats, we discussed your resume." 
   - ONLY say "This is actually our first conversation" if BOTH the LONG-TERM USER MEMORY list AND the PAST CONVERSATION SUMMARIES list are completely empty.
   - NEVER say "This is our first conversation" if you can see summaries or memories below.

7. Do NOT say "I don't have access to previous conversations" if actual conversation memory or summaries ARE available in the prompt.

8. If there is no relevant memory in the current thread AND no long-term memory, say so naturally:
   - "I don't see anything earlier in this chat about that yet."
   - "We haven't discussed that in this conversation so far."

9. Maintain the companion's personality while being accurate to the chat history and user profile.

10. If CROSS-COMPANION INTELLIGENCE is provided above, use it naturally.
    - Reference what other companions have learned about the user when relevant.
    - Do NOT say "Noor told me" or "Max said" — instead, weave the insight in naturally.
    - Example: Instead of "Noor told me you slept 4 hours", say "I noticed you mentioned sleeping poorly last night — let's take it easy today."
    - NEVER break the fourth wall about the companion system.
"""

    return {
        **state,
        "system_prompt": personalized_prompt
    }