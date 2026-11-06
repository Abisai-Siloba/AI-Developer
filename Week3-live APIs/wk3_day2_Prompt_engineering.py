import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY is missing. Add it to your .env file.")

client = anthropic.Anthropic(api_key=api_key)

system_prompt = """You are a customer service assistant for Kamau Stores,
a wholesale distributor in Nairobi.

Classify the customer message as one of these exact categories:
- ORDER
- COMPLAINT
- INQUIRY


Reply with only the category name and nothing else.

Rules:
- Only answer questions about orders, pricing, and delivery.
- All prices are in KES.
- Delivery covers Nairobi, Mombasa, Kisumu, and Nakuru only.
- If the message is outside your scope, say: "Please call our office on 0712 345 678 for that."
- Always be polite and professional. End with "Asante kwa kuwasiliana nasi."
"""

question = input("What is your question ").strip()

if not question:
    print("Please enter a message.")
    raise SystemExit

try:
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=128,
        system=system_prompt,
        messages=[{"role": "user", "content": question}],
    )

    response_text = message.content[0].text.strip()
    print(response_text)
    print(f"Token used: {message.usage.input_tokens} in, {message.usage.output_tokens} out")

except anthropic.APIConnectionError:
    print("No internet connection. Check your connection and try again.")

except anthropic.AuthenticationError:
    print("API key is wrong or expired. Check your .env file and try again.")

except anthropic.RateLimitError:
    print("Too many requests. Wait 60 seconds and try again.")

except ValueError as exc:
    print(exc)
