from wk4_day5_deployed_ai_web_application_app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(__import__('os').environ.get('PORT', 5000)))
