"""Answer common Thika SACCO member questions with help from Claude."""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Protocol


MODEL = "claude-haiku-4-5"
SYSTEM_PROMPT = """\
You are a friendly, concise WhatsApp helper for a matatu SACCO in Thika, Kenya.
Use Kenyan shillings (KSh), plain language, and the sample SACCO information below.

Sample SACCO information:
- The next monthly members' meeting is {meeting_date} at 10:00 a.m. at the
  SACCO office near Thika Main Stage. Meetings are held on the first Saturday
  of each month.
- The one-time joining fee is KSh 2,500.
- Monthly membership dues are KSh 1,000.
- Loan intarest rates 10%
- Loans can be accessed 4 times of members shares. Need quarantees.
- You cannot access the SACCO ledger or any member's personal account balance.
  Never invent a balance. Explain that the member should contact the treasurer
  with their member number through the SACCO's usual private channel.

These are sample details for a demo. Answer only from the information above;
do not make up other fees, dates, or account details. If asked something else,
say you do not have that information and direct the member to the SACCO Manager.
Keep replies helpful and brief.
"""


class MessageClient(Protocol):
    """The small part of the Anthropic client used by this script."""

    messages: "Messages"


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


def next_meeting_date(today: date) -> date:
    """Return the first Saturday strictly after today."""
    year, month = today.year, today.month
    while True:
        first_day = date(year, month, 1)
        first_saturday = first_day + timedelta(days=(5 - first_day.weekday()) % 7)
        if first_saturday > today:
            return first_saturday
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1


def answer_question(question: str, client: MessageClient | None = None) -> str:
    """Send a member's question and the SACCO guidance to Claude."""
    if not question.strip():
        raise ValueError("Please enter a question.")

    if client is None:
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError(
                "The Anthropic package is missing. Install it with "
                "'python -m pip install -r requirements.txt'."
            ) from exc

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add your Anthropic API key "
                "to your environment and try again."
            )
        client = anthropic.Anthropic(api_key=api_key)

    meeting_date = next_meeting_date(date.today()).strftime("%A, %B %d, %Y")
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=SYSTEM_PROMPT.format(meeting_date=meeting_date),
        messages=[{"role": "user", "content": question.strip()}],
    )
    if not response.content or not getattr(response.content[0], "text", ""):
        raise RuntimeError("The AI returned an empty answer. Please try again.")
    return response.content[0].text.strip()


def main() -> None:
    try:
        import anthropic
    except ImportError:
        print(
            "Error: The Anthropic package is missing. Install it with "
            "'python -m pip install -r requirements.txt'."
        )
        return

    question = input("Member question: ").strip()
    try:
        print(f"\n{answer_question(question)}")
    except anthropic.APIConnectionError:
        print("\nError: Could not connect to Anthropic. Check your internet connection.")
    except anthropic.AuthenticationError:
        print("\nError: The API key was rejected. Check ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        print("\nError: The AI service is busy. Wait a moment and try again.")
    except anthropic.APIError:
        print("\nError: The AI service returned an error. Please try again later.")
    except (RuntimeError, ValueError) as exc:
        print(f"\nError: {exc}")


if __name__ == "__main__":
    main()