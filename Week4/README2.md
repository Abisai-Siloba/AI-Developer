# AI Text Processor

This project is a simple Flask web app that lets a user paste text into a browser and receive an AI-generated response from Anthropic Claude. It is designed for quick experimentation, writing support, and lightweight text-processing tasks, making it useful for students, freelancers, and small teams who want a fast, browser-based AI tool without needing to code a custom interface from scratch.

## Live Demo

https://your-render-url-here.onrender.com

## How It Works

1. The user enters text in the web form.
2. The frontend sends the text to the Flask backend.
3. The backend calls the Anthropic API using the API key stored in the Render environment variables.
4. The AI response is returned to the browser and displayed on the page.

## Tech Stack

- Python
- Flask
- Anthropic API
- Render
- HTML/CSS/JavaScript

## Local Setup

```bash
cd Week4
python -m pip install -r requirements.txt
python app.py
```

Then open the app in a browser at:

```text
http://127.0.0.1:5000
```

## Deployment

This app is intended for deployment on Render using a Gunicorn start command:

```text
gunicorn app:app
```

Before deploying, make sure:

- `requirements.txt` includes `gunicorn`
- `.env` is in `.gitignore`
- the Anthropic API key is stored in Render environment variables
- the app uses the `PORT` environment variable

## Notes

This version is a lightweight demo application designed to show how to connect a front end to an AI API in a deployed web app.
