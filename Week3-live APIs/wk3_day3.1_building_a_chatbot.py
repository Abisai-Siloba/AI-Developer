"""Command-line customer-service assistant for Kisumu Pharmacy."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol


MODEL = "claude-haiku-4-5"
LOG_PATH = Path(__file__).with_name("Pharma_log.json")
SYSTEM_PROMPT = """\
You are a friendly, concise customer-service assistant for Kisumu Pharmacy in
Kisumu, Kenya. Help pharmacy staff answer customer questions consistently.

Opening hours (East Africa Time):
- Monday-Saturday: 8:00 a.m.-8:00 p.m.
- Sunday: 10:00 a.m.-6:00 p.m.

Services:
- Prescription dispensing
- Repeat-prescription processing
- Over-the-counter medicines
- Medication-use counselling by the pharmacist
- Blood-pressure checks
- Blood-glucose checks
- First-aid supplies

Prescription guidance:
- A routine prescription usually takes about 15-30 minutes to process after
  the pharmacy receives it. Queues, stock availability, and pharmacist review
  can change this estimate; staff should confirm the current wait.
- For a repeat prescription, ask the customer to bring their current valid
  prescription, identification if requested, and previous medicine packaging
  or dispensing details if available. The pharmacist must confirm what is
  legally and clinically required.
- You do not have live inventory access. Never claim that a specific medicine
  is in stock or out of stock. Tell staff to check the pharmacy's current stock
  records or shelves before answering.

Answer only from these details, keep answers brief, and ask a clarifying
question when needed. Do not diagnose, prescribe, or recommend a change to
prescribed treatment; refer clinical questions to the pharmacist.
"""

DEMO_TURNS = (
    "I have a prescription for my regular medicine.",
    "How long will it take to process it?",
    "What documents do I need for the repeat prescription?",
)
DEMO_REPLIES = (
    "Routine prescriptions usually take about 15-30 minutes after we receive "
    "them. The wait can vary with the queue, medicine availability, and "
    "pharmacist review.",
    "For the prescription you mentioned, allow about 15-30 minutes for routine "
    "processing; the current queue or pharmacist review may affect the wait.",
    "For a repeat, bring your current valid prescription. Please also bring "
    "identification if requested and your previous packaging or dispensing "
    "details if available. The pharmacist can confirm the requirements.",
)


class TextBlock(Protocol):
    text: str

class MessageResponse(Protocol):
    content: list[TextBlock]

class Messages(Protocol):
    def create(
        self,
        *,
        model: str,
        max_tokens: int,
        system: str,
        messages: list[dict[str, str]],
    ) -> MessageResponse: ...


class MessageClient(Protocol):
    messages: Messages


class DemoMessages:
    """Offline client that checks history is carried between demo turns."""

    def __init__(self) -> None:
        self.calls = 0

    def create(
        self,
        *,
        model: str,
        max_tokens: int,
        system: str,
        messages: list[dict[str, str]],
    ) -> MessageResponse:
        if system != SYSTEM_PROMPT:
            raise RuntimeError("The demo did not receive the pharmacy system prompt.")
        if self.calls >= len(DEMO_TURNS):
            raise RuntimeError("The offline demo received more turns than expected.")
        expected_messages: list[dict[str, str]] = []
        for turn in range(self.calls):
            expected_messages.extend(
                [
                    {"role": "user", "content": DEMO_TURNS[turn]},
                    {"role": "assistant", "content": DEMO_REPLIES[turn]},
                ]
            )
        expected_messages.append({"role": "user", "content": DEMO_TURNS[self.calls]})
        if messages != expected_messages:
            raise RuntimeError("Conversation history was not retained between turns.")
        reply = DEMO_REPLIES[self.calls]
        self.calls += 1
        return SimpleNamespace(content=[SimpleNamespace(text=reply)])


class DemoClient:
    def __init__(self) -> None:
        self.messages = DemoMessages()


def create_client() -> MessageClient:
    """Create an Anthropic client using the configured environment key."""
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError(
            "The Anthropic package is missing. Install it with "
            "'python -m pip install -r requirements.txt'."
        ) from exc

    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise RuntimeError(
            "The python-dotenv package is missing. Install it with "
            "'python -m pip install -r requirements.txt'."
        ) from exc

    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add your Anthropic API key "
            "to the environment and try again."
        )
    return anthropic.Anthropic(api_key=api_key)


def save_log(messages: list[dict[str, str]], log_path: Path = LOG_PATH) -> None:
    log = {
        "date": datetime.now(timezone.utc).isoformat(),
        "pharmacy": "Kisumu Pharmacy",
        "messages": messages,
    }
    log_path.write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_conversation(
    client: MessageClient,
    scripted_inputs: tuple[str, ...] | None = None,
    log_path: Path = LOG_PATH,
) -> None:
    """Run a chat while sending and saving the complete conversation history."""
    messages: list[dict[str, str]] = []
    scripted_turns = iter(scripted_inputs) if scripted_inputs is not None else None
    print("Kisumu Pharmacy Assistant. Type 'exit' to quit.")

    try:
        while True:
            if scripted_turns is None:
                try:
                    user_input = input("You: ").strip()
                except EOFError:
                    break
            else:
                try:
                    user_input = next(scripted_turns).strip()
                except StopIteration:
                    break

            if user_input.lower() in {"exit", "quit"}:
                break
            if not user_input:
                print("Please enter a question.")
                continue

            messages.append({"role": "user", "content": user_input})
            response = client.messages.create(
                model=MODEL,
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=messages.copy(),
            )
            if not response.content or not response.content[0].text.strip():
                raise RuntimeError("The AI returned an empty answer. Please try again.")

            reply = response.content[0].text.strip()
            messages.append({"role": "assistant", "content": reply})
            print(f"Assistant: {reply}")
    finally:
        save_log(messages, log_path)
        print(f"Conversation saved to {log_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--demo",
        action="store_true",
        help="run the three-turn offline conversation and verify history is retained",
    )
    args = parser.parse_args()

    if args.demo:
        client: MessageClient = DemoClient()
        scripted_inputs = DEMO_TURNS
    else:
        client = create_client()
        scripted_inputs = None
    run_conversation(client, scripted_inputs=scripted_inputs)


if __name__ == "__main__":
    main()