from agent.intent import classify_intent
from agent.rag import RAG
from agent.memory import Memory
from agent.tools import mock_lead_capture
from agent.llm_provider import llm


class AgentController:
    def __init__(self):
        self.rag = RAG()
        self.memory = Memory()

    # ── Format chat history for LLM context ──────────────────────────────────
    def _history_context(self):
        """Format recent chat history so the LLM remembers the conversation."""
        history = self.memory.get_history()
        if not history:
            return ""
        lines = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "AutoStream AI"
            lines.append(f"{role}: {msg['content']}")
        return "--- Recent conversation ---\n" + "\n".join(lines) + "\n---------------------------\n"

    # ── LLM-powered lead question generator ──────────────────────────────────
    def _ask_field(self, field, context=""):
        """Use LLM to naturally ask for the next piece of info."""
        history = self._history_context()
        prompts = {
            "name": f"""You are AutoStream AI, a friendly sales assistant. The user wants to sign up.
{history}
{context}
Ask for their name in a warm, natural way. Keep it to 1-2 sentences max.
Do NOT mention email or platform yet.""",

            "email": f"""You are AutoStream AI, a friendly sales assistant collecting signup details.
{history}
{context}
Ask for their email address naturally. Keep it to 1-2 sentences max.
Do NOT mention platform yet.""",

            "platform": f"""You are AutoStream AI, a friendly sales assistant collecting signup details.
{history}
{context}
Ask which content creation platform they use. Be open-ended — it could be anything.
Don't assume or list specific platforms. Keep it to 1-2 sentences max."""
        }
        reply = llm.invoke(prompts[field])
        return reply.content.strip()

    def _invalid_field(self, field, user_input):
        """Use LLM to gently re-ask when the user gave invalid input."""
        history = self._history_context()
        reply = llm.invoke(
            f"""You are AutoStream AI collecting signup details.
{history}
The user was asked for their {field} but instead said: "{user_input}"

Respond kindly — acknowledge what they said, and gently re-ask for their {field}.
If they asked a question, briefly address it and then redirect.
Keep it to 1-2 sentences. Be human, not robotic."""
        )
        return reply.content.strip()

    # ── Main handler ─────────────────────────────────────────────────────────
    def handle_message(self, user_input: str):
        # store user message
        self.memory.add_message("user", user_input)

        # ---------------- STEP 1: LEAD COLLECTION FLOW ----------------
        if self.memory.state["stage"] is not None:

            # Detect if user is changing their mind / redirecting mid-flow
            redirect_words = {
                "no", "change", "switch", "cancel", "stop", "nevermind",
                "actually", "wait", "register", "quit", "exit"
            }
            words_in_input = set(user_input.lower().split())
            is_redirecting = bool(words_in_input & redirect_words)

            if is_redirecting:
                self.memory.reset()
            else:
                status, next_field = self.memory.handle_input(user_input)

                if status == "invalid":
                    response = self._invalid_field(next_field, user_input)
                    self.memory.add_message("bot", response)
                    return response

                if status == "stored" and next_field is not None:
                    state = self.memory.state
                    context = f"Collected so far: name = {state['name'] or '?'}, email = {state['email'] or '?'}."
                    context += f"\nThe user just provided: \"{user_input}\""
                    response = self._ask_field(next_field, context)
                    self.memory.add_message("bot", response)
                    return response

                # All fields collected → call tool
                if self.memory.is_complete():
                    state = self.memory.state

                    mock_lead_capture(
                        state["name"],
                        state["email"],
                        state["platform"]
                    )

                    history = self._history_context()
                    reply = llm.invoke(
                        f"""You are AutoStream AI. The user just completed signup.
{history}
Their details: Name = {state['name']}, Email = {state['email']}, Platform = {state['platform']}.
Confirm their registration warmly in 1-2 sentences. Mention their name.
Let them know the team will reach out soon."""
                    )
                    response = reply.content.strip()

                    self.memory.reset()
                    self.memory.add_message("bot", response)
                    return response

        # ---------------- STEP 2: INTENT ----------------
        intent = classify_intent(user_input)
        self.memory.set_intent(intent)

        # ---------------- STEP 3: RESPONSE LOGIC ----------------
        history = self._history_context()

        if intent == "greeting":
            reply = llm.invoke(
                f"""You are AutoStream AI, a friendly sales assistant for a video editing SaaS.
{history}
Respond warmly and naturally to the user's message. Keep it short (1-2 sentences).
Mention you can help with pricing, plans, or getting started — but only if it fits naturally.
Do NOT list features or prices. Just be human and welcoming.

User said: {user_input}"""
            )
            response = reply.content.strip()

        elif intent == "inquiry":
            response = self.rag.query(user_input, self.memory.get_history())

        elif intent == "high_intent":
            next_field = self.memory.get_next_field()
            response = self._ask_field(next_field, f"The user said: \"{user_input}\"")

        else:
            reply = llm.invoke(
                f"""You are AutoStream AI, a helpful assistant for a video editing SaaS.
{history}
The user said something you didn't fully understand. Respond politely and guide them
to ask about pricing, features, or signing up. Keep it to 1-2 sentences.

User said: {user_input}"""
            )
            response = reply.content.strip()

        # store bot response
        self.memory.add_message("bot", response)

        return response