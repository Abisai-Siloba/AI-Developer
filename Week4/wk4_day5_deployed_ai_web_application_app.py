'''
Project: Deployed AI Web Application
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

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import anthropic, os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/process", methods=["POST"])
def process():
    try:
        text = request.json.get("text", "")
        if not text:
            return jsonify({"error": "No text provided"}), 400
        response = client.chat.completions.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": text}]
        )
        return jsonify({"result": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)