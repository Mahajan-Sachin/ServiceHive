import json
import os
from agent.llm_provider import llm


class RAG:
    def __init__(self, file_path=None):
        if file_path is None:
            file_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "knowledge_base.json"
            )
        with open(file_path, "r") as f:
            self.data = json.load(f)

    # ── Context retrieval (smart, not dump-everything) ────────────────────────
    def _retrieve_context(self, question: str) -> str:
        """
        Pick the most relevant section(s) from the knowledge base.
        This is the 'R' in RAG — retrieval step.
        """
        q = question.lower()

        basic   = self.data["pricing"]["basic"]
        pro     = self.data["pricing"]["pro"]
        policy  = self.data["policies"]

        # Policy-related
        if any(w in q for w in ["refund", "cancel", "policy", "support", "help"]):
            return (
                f"Company Policies:\n"
                f"- Refund policy: {policy['refund']}\n"
                f"- Support: {policy['support']}"
            )

        # Basic plan specifically
        if any(w in q for w in ["basic", "starter", "cheap", "29", "affordable", "720"]):
            return (
                f"Basic Plan:\n"
                f"- Price: {basic['price']}\n"
                f"- Videos per month: {basic['videos']}\n"
                f"- Resolution: {basic['resolution']}"
            )

        # Pro plan specifically
        if any(w in q for w in ["pro", "premium", "4k", "unlimited", "caption", "79", "advanced"]):
            return (
                f"Pro Plan:\n"
                f"- Price: {pro['price']}\n"
                f"- Videos per month: {pro['videos']}\n"
                f"- Resolution: {pro['resolution']}\n"
                f"- Extra features: {', '.join(pro['features'])}"
            )

        # General pricing / compare
        return (
            f"AutoStream Pricing:\n\n"
            f"Basic Plan:\n"
            f"- Price: {basic['price']}\n"
            f"- Videos: {basic['videos']}\n"
            f"- Resolution: {basic['resolution']}\n\n"
            f"Pro Plan:\n"
            f"- Price: {pro['price']}\n"
            f"- Videos: {pro['videos']}\n"
            f"- Resolution: {pro['resolution']}\n"
            f"- Extra features: {', '.join(pro['features'])}\n\n"
            f"Policies:\n"
            f"- Refund: {policy['refund']}\n"
            f"- Support: {policy['support']}"
        )

    # ── LLM-generated response (the 'G' in RAG) ───────────────────────────────
    def query(self, question: str, chat_history: list = None) -> str:
        """
        Retrieve relevant context, then let the LLM generate a natural response.
        This is proper RAG — not hardcoded templates.
        """
        context = self._retrieve_context(question)

        # Format conversation history if available
        history_block = ""
        if chat_history:
            lines = []
            for msg in chat_history:
                role = "User" if msg["role"] == "user" else "AutoStream AI"
                lines.append(f"{role}: {msg['content']}")
            history_block = "--- Recent conversation ---\n" + "\n".join(lines) + "\n---------------------------\n"

        prompt = f"""You are a friendly and concise sales assistant for AutoStream, \
a SaaS platform offering automated video editing tools for content creators.

{history_block}
Answer the user's question using ONLY the information provided below. \
Do not invent prices, features, or policies. Keep your reply short and natural — \
like a real human sales rep in a chat window. Reference earlier conversation if relevant.

--- Knowledge Base ---
{context}
----------------------

User question: {question}

Your answer:"""

        response = llm.invoke(prompt)
        return response.content.strip()