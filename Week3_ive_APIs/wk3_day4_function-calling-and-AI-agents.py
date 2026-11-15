import os

import anthropic
from dotenv import load_dotenv


inventory = {
    "maize flour": 120,
    "wheat flour": 85,
    "rice": 200,
    "sugar": 0,
    "cooking oil": 45
}

# Define the tools in the format the API understands.
tools = [
    {
        "name": "get_stock_level",
        "description": "Get the current stock quantity for a product at Kamau Stores",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "The name of the product to check"
                }
            },
            "required": ["product_name"]
        }
    }
]


def get_stock_level(product_name):
    product = product_name.lower()
    if product in inventory:
        qty = inventory[product]
        if qty == 0:
            return f"{product_name} is currently out of stock."
        return f"{product_name}: {qty} units in stock."
    return f"Product '{product_name}' not found in the system."


def main():
    load_dotenv()
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    messages = [
        {"role": "user", "content": "How much maize flour do we have?"}
    ]

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        tools=tools,
        messages=messages,
    )

    while response.stop_reason == "tool_use":
        tool_results = []
        for content_block in response.content:
            if content_block.type != "tool_use":
                continue
            if content_block.name != "get_stock_level":
                raise ValueError(f"Unknown tool requested: {content_block.name}")

            result = get_stock_level(content_block.input["product_name"])
            print(f"Function called: {content_block.name}({content_block.input})")
            print(f"Result: {result}")
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": result,
                }
            )

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            tools=tools,
            messages=messages,
        )

    for content_block in response.content:
        if content_block.type == "text":
            print(f"Assistant: {content_block.text}")


prices = {
    "maize flour": 2800, 
    "wheat flour": 3200, 
    "rice": 4500
    }

def get_price(product_name):
    p = product_name.lower()
    if p in prices:
        return f"{product_name}: KES {prices[p]:,} per bag"
    return f"Price not found for '{product_name}'"


if __name__ == "__main__":
    main()
