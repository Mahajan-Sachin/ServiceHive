class Memory:
    def __init__(self):
        # short-term chat memory (last 20 messages = ~10 turns)
        # Assignment requires 5-6 turn retention — this gives 10 turns of safety
        self.chat_history = []

        # lead + flow state
        self.state = {
            "intent": None,
            "name": None,
            "email": None,
            "platform": None,
            "stage": None   # controls which question we are asking
        }

    # ---------------- CHAT HISTORY ----------------
    def add_message(self, role, content):
        self.chat_history.append({"role": role, "content": content})

        # keep only last 20 messages (~10 conversation turns)
        if len(self.chat_history) > 20:
            self.chat_history.pop(0)

    def get_history(self):
        return self.chat_history

    # ---------------- INTENT ----------------
    def set_intent(self, intent):
        self.state["intent"] = intent

    def get_intent(self):
        return self.state["intent"]

    # ---------------- LEAD FLOW ----------------
    def get_next_field(self):
        """Return which field to collect next, or None if all done."""
        if not self.state["name"]:
            self.state["stage"] = "name"
            return "name"

        if not self.state["email"]:
            self.state["stage"] = "email"
            return "email"

        if not self.state["platform"]:
            self.state["stage"] = "platform"
            return "platform"

        return None

    def handle_input(self, user_input):
        """
        Validate and store user input for the current stage.
        Returns:
          ("stored", next_field)  → value accepted, here's what to ask next (or None)
          ("invalid", stage)      → value rejected, re-ask this stage
        """
        stage = self.state["stage"]

        if stage == "name":
            # Reject if it looks like a question or a full sentence
            if "?" in user_input or len(user_input.split()) > 6:
                return ("invalid", "name")
            self.state["name"] = user_input.strip()
            next_field = self.get_next_field()
            return ("stored", next_field)

        elif stage == "email":
            cleaned = user_input.strip().lower()
            # Basic email check
            if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
                return ("invalid", "email")
            self.state["email"] = cleaned
            next_field = self.get_next_field()
            return ("stored", next_field)

        elif stage == "platform":
            self.state["platform"] = user_input.strip()
            return ("stored", None)

        return ("invalid", stage)

    # CHECK COMPLETE
    def is_complete(self):
        return (
            self.state["name"] is not None and
            self.state["email"] is not None and
            self.state["platform"] is not None
        )

    # RESET
    def reset(self):
        self.state = {
            "intent": None,
            "name": None,
            "email": None,
            "platform": None,
            "stage": None
        }