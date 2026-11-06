import anthropic
from dotenv import load_dotenv
import os

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

system_prompt = """You are an assistant for Kanini Haraka Wholesale in Nyeri.
Answer questions about stock, pricing, and delivery.
All prices in KES. Be helpful and brief."""

messages = []
print("Kanini Haraka Wholesale Assistant. Type 'exit' to quit.")

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break
    
    messages.append({"role": "user", "content": user_input})
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        system=system_prompt,
        messages=messages
    )
    
    reply = response.content[0].text
    messages.append({"role": "assistant", "content": reply})
    print(f"Assistant: {reply}")

# Keep only the last 10 messages (5 user + 5 assistant turns)
if len(messages) > 10:
    messages = messages[-10:]


# After the loop ends, save the log
import json
from datetime import datetime

log = {
    "date": datetime.now().isoformat(),
    "messages": messages
}

with open("chat_log.json", "w") as f:
    json.dump(log, f, indent=2)
    
print("Conversation saved to chat_log.json")