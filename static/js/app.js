// ── Auto-greet on load ────────────────────────────────────────────────────────
window.addEventListener("load", () => {
    appendMessage("bot", "👋 Hey! I'm the <b>AutoStream AI</b> assistant.<br>Ask me about our <b>pricing</b>, <b>features</b>, or get started with a plan!");
});

// ── Enter key support ─────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("msg").addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

// ── Main send function ────────────────────────────────────────────────────────
async function sendMessage() {
    const input   = document.getElementById("msg");
    const message = input.value.trim();
    if (!message) return;

    appendMessage("user", escapeHtml(message));
    input.value = "";

    const typingId = showTyping();

    try {
        const res = await fetch("/chat", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ message })
        });

        const data = await res.json();
        removeTyping(typingId);
        appendMessage("bot", data.reply);

    } catch (err) {
        removeTyping(typingId);
        appendMessage("bot", "⚠️ Connection error. Please try again.");
    }
}

// ── Append a message bubble ───────────────────────────────────────────────────
function appendMessage(role, html) {
    const chat = document.getElementById("chat");

    const row = document.createElement("div");
    row.className = `msg-row ${role}`;

    const avatar = document.createElement("div");
    avatar.className = `msg-avatar ${role === "user" ? "user-av" : ""}`;
    avatar.textContent = role === "user" ? "👤" : "🤖";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerHTML = html;   // bot responses may contain <b>, <br> etc.

    const ts = document.createElement("div");
    ts.className = "ts";
    ts.textContent = now();

    const col = document.createElement("div");
    col.className = "msg-col";
    col.appendChild(bubble);
    col.appendChild(ts);

    row.appendChild(avatar);
    row.appendChild(col);
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
}

// ── Typing indicator ──────────────────────────────────────────────────────────
function showTyping() {
    const chat = document.getElementById("chat");
    const id   = "typing-" + Date.now();

    const row = document.createElement("div");
    row.className = "typing-row";
    row.id = id;

    const avatar = document.createElement("div");
    avatar.className = "msg-avatar";
    avatar.textContent = "🤖";

    const bubble = document.createElement("div");
    bubble.className = "typing-bubble";
    bubble.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

    row.appendChild(avatar);
    row.appendChild(bubble);
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;

    return id;
}

function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function now() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}