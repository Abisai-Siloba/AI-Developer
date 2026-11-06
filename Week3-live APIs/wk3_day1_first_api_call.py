import anthropic
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

question = input("Ask me anything: ")

try:
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": question}]
)

    print("Answer:", message.content[0].text)
    print(f"Tokens used: {message.usage.input_tokens} in, {message.usage.output_tokens} out")

except anthropic.APIConnectionError:
    print("No internet connection, Check your connection and try again.")

except anthropic.AuthenticationError:
    print("API Key is wrong or expired. Check your .env file and try again.")

except anthropic.RateLimitError:
    print("Too many requests. Wait 60 seconds and try again.")

