from langchain_core.prompts import PromptTemplate
from agent.llm_provider import llm

# ── Intent classification prompt ──────────────────────────────────────────────
prompt = PromptTemplate(
    input_variables=["user_input"],
    template="""You are an intent classifier for AutoStream, a SaaS video editing platform.

Classify the user message into EXACTLY one of these three labels:

- greeting    → casual / social messages (hello, hi, how are you, thanks, what's up, bye)
- inquiry     → questions about the product, pricing, plans, features, refunds, or support
- high_intent → user clearly wants to sign up, buy, start a trial, or use the product

Return ONLY the single label word. No explanation. No punctuation. No extra text.

User message: {user_input}
"""
)


def classify_intent(user_input: str) -> str:
    chain = prompt | llm
    response = chain.invoke({"user_input": user_input})
    intent = response.content.strip().lower()

    print(f"[INTENT] '{user_input[:50]}' -> {intent}")

    if intent not in ["greeting", "inquiry", "high_intent"]:
        return "greeting"   # safe fallback

    return intent