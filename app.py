from flask import Flask, render_template, request, jsonify
from agent.controller import AgentController
import traceback

app = Flask(__name__)

agent = AgentController()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({"reply": "Invalid request"}), 400

        user_message = data["message"]

        print("\n==============================")
        print(f"[USER]: {user_message}")

        response = agent.handle_message(user_message)

        print(f"[BOT]: {response}")
        print("==============================\n")

        return jsonify({"reply": response})

    except Exception as e:
        print("\n🔥 FULL ERROR TRACEBACK:")
        traceback.print_exc()

        # 👇 IMPORTANT: send error to frontend also (for debugging)
        return jsonify({
            "reply": f"ERROR: {str(e)}"
        }), 500


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)