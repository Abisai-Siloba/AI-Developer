from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)               # allows all origins in development

# For production, restrict to your frontend domain only:
# CORS(app, origins=["https://yoursite.com"])


def summarize_text(text):
    text = (text or '').strip()
    if not text:
        return 'No text provided.'

    sentences = [sentence.strip() for sentence in text.replace('\n', ' ').split('. ') if sentence.strip()]
    if not sentences:
        return text[:200]

    summary = ' '.join(sentences[:2])
    if len(summary) > 200:
        summary = summary[:197] + '...'
    return summary


@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.get_json() or {}
    text = data.get('text', '')
    result = summarize_text(text)
    return jsonify({'summary': result})
