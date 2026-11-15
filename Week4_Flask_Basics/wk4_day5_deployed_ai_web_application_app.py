'''
Project: Deployed AI Web Application:
Build an AI web app where the user submits text and gets an AI result.
Deploy to Render using the week4 day4 process.

Check every item on this list before you click Deploy:
requirements.txt includes gunicorn
.env is in .gitignore and NOT committed
API key is set in Render Environment tab
app.run uses PORT from environment variable
Start command is: gunicorn app:app

Write a one-paragraph description that explains what it does and who it is for.
This goes in your GitHub README and portfolio page.

Add the live URL to your GitHub README and portfolio page.
A deployed app with no visible link is invisible to clients.
'''

import os

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from dotenv import load_dotenv
import anthropic

load_dotenv()
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
)
CORS(app)

api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key) if api_key else None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def process():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    if client is None:
        return jsonify({"error": "ANTHROPIC_API_KEY is not set."}), 500

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": text}],
        )
        result = response.content[0].text
        return jsonify({"result": result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)