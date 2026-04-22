# AutoStream AI Agent

An AI-powered conversational sales agent for **AutoStream** — a fictional SaaS platform offering automated video editing tools for content creators.

Built as part of the **ServiceHive / Inflx Machine Learning Intern Assignment**.

---

## How to Run Locally

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd autostream-ai-agent
```

### 2. Create a virtual environment & install dependencies
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root:

```env
# Option A – Gemini 1.5 Flash (FREE · officially listed in assignment)
# Get key at: https://aistudio.google.com
GEMINI_API_KEY=your_gemini_api_key_here

# Option B – Groq / llama-3.1-8b-instant (FREE · used as fallback)
# Get key at: https://console.groq.com
GROQ_API_KEY=your_groq_api_key_here
```

> **The agent auto-detects which key is present.** If both are set, Gemini 1.5 Flash takes priority as it is the officially approved model in the assignment spec.

### 4. Run the Flask server
```bash
python app.py
```

Open your browser at → **http://127.0.0.1:5000**

---

## Architecture Explanation

### Why LangChain with a custom state machine?

I chose **LangChain** for its clean abstraction over LLM calls and prompt chaining. For an assignment of this scope — a single-user conversational agent with a small, fixed knowledge base — wiring up a full LangGraph state graph would be over-engineering. Instead, a lightweight `Memory` class mirrors LangGraph's philosophy: a central state dictionary tracks the conversation stage and collected lead data across turns, retaining the last **20 messages (~10 turns)** in a rolling buffer — well above the required 5–6 turns.

### How state is managed

Each incoming message passes through three stages orchestrated by `controller.py`:

1. **Lead flow check** — if a lead is being collected (stage is active), the next question is served or the tool is fired.
2. **Intent classification** — the LLM (Gemini 1.5 Flash / Groq) classifies the message into `greeting`, `inquiry`, or `high_intent`.
3. **Response routing** — greetings get a welcome reply; inquiries hit the RAG retriever; high-intent starts the lead collection flow.

The RAG pipeline is intentionally simple: keyword-based routing into the correct section of `data/knowledge_base.json`. No vector database is needed — the knowledge base has only ~6 data points, so cosine similarity would add complexity with zero benefit.

**`mock_lead_capture()`** is triggered *only* after all three lead fields (name, email, platform) are collected, preventing premature tool calls.

---

## WhatsApp Deployment via Webhooks

To deploy this agent on WhatsApp, I would use the **Meta WhatsApp Business Cloud API**:

### Architecture

```
WhatsApp User
     ↓  (sends message)
Meta Cloud API
     ↓  (POST to webhook)
Flask  /webhook  ──→  AgentController (per-user Memory instance)
     ↓  (calls WhatsApp Send API)
WhatsApp User  ←  reply delivered
```

### Integration Steps

1. **Create a Meta Developer App** and add the WhatsApp product.
2. **Register a webhook** pointing to `https://your-server.com/webhook` with a verify token.
3. **Add two routes to `app.py`**:
   - `GET /webhook` → verify token handshake with Meta
   - `POST /webhook` → extract message text, pass to `AgentController`, reply via the WhatsApp Send API
4. **Per-user sessions** — use `wa_id` (the WhatsApp phone number) as the session key, mapping each number to its own `Memory` instance stored in a dict or lightweight cache (e.g., `shelve`, Redis).
5. **Deploy** on any platform with a public HTTPS URL (Railway, Render, Fly.io).

### Code Sketch

```python
agents = {}   # { wa_id: AgentController }

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    if request.args.get("hub.verify_token") == os.getenv("VERIFY_TOKEN"):
        return request.args.get("hub.challenge")
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    data    = request.get_json()
    message = data["entry"][0]["changes"][0]["value"]["messages"][0]
    wa_id   = message["from"]
    text    = message["text"]["body"]

    if wa_id not in agents:
        agents[wa_id] = AgentController()

    reply = agents[wa_id].handle_message(text)
    send_whatsapp_message(wa_id, reply)   # calls Meta Send API
    return "OK", 200
```

---

## Project Structure

```
autostream-ai-agent/
├── agent/
│   ├── controller.py      # Orchestration: intent → RAG → lead flow → tool
│   ├── intent.py          # LLM-based intent classifier (Gemini / Groq)
│   ├── llm_provider.py    # Shared LLM initialisation (Gemini → Groq fallback)
│   ├── memory.py          # Rolling chat history + lead collection state
│   ├── rag.py             # Local JSON knowledge base retriever
│   └── tools.py           # mock_lead_capture() tool
├── data/
│   └── knowledge_base.json   # Pricing + company policies
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   └── index.html
├── app.py                 # Flask entrypoint
├── requirements.txt
└── .env                   # API keys (not committed to git)
```

---

## Evaluation Coverage

| Assignment Requirement | Status |
|------------------------|--------|
| Intent detection (greeting / inquiry / high_intent) | ✅ |
| RAG from local knowledge base (JSON) | ✅ |
| Lead capture: name, email, platform | ✅ |
| Tool fires only after all 3 fields collected | ✅ |
| State retained across 5–6 conversation turns | ✅ |
| LangChain used | ✅ |
| Approved LLM — Gemini 1.5 Flash (with Groq fallback) | ✅ |
| WhatsApp webhook deployment explanation | ✅ |
| requirements.txt | ✅ |
| README with setup + architecture + WhatsApp | ✅ |
