import importlib.util
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace


SCRIPT_PATH = Path(__file__).with_name("wk3_day1.1_first_api_call.py")
SPEC = importlib.util.spec_from_file_location("sacco_assistant", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load script from {SCRIPT_PATH}")
sacco_assistant = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sacco_assistant)


class FakeMessages:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(text="Sample answer.")])


class SaccoAssistantTests(unittest.TestCase):
    def test_member_question_variations_are_sent_with_sacco_guidance(self) -> None:
        questions = {
            "balance": [
                "What is my balance?",
                "How much do I owe?",
                "Can you check my account balance?",
                "What's my outstanding amount?",
                "How much have I paid so far?",
            ],
            "meeting": [
                "When is our next meeting?",
                "What day are we meeting next?",
                "Is there a members' meeting coming up?",
                "When should I come to the SACCO meeting?",
                "What's the date and time for the next gathering?",
            ],
            "fees": [
                "What are the current membership fees?",
                "How much is it to join?",
                "How much do I pay each month?",
                "Tell me the joining fee and monthly dues.",
                "What is the monthly subscription?",
            ],
        }

        for category, variations in questions.items():
            for question in variations:
                with self.subTest(category=category, question=question):
                    messages = FakeMessages()
                    client = SimpleNamespace(messages=messages)

                    answer = sacco_assistant.answer_question(question, client=client)

                    self.assertEqual(answer, "Sample answer.")
                    self.assertEqual(len(messages.calls), 1)
                    request = messages.calls[0]
                    self.assertEqual(request["messages"], [
                        {"role": "user", "content": question}
                    ])
                    system_prompt = request["system"]
                    self.assertIn("KSh 2,500", system_prompt)
                    self.assertIn("KSh 1,000", system_prompt)
                    self.assertIn("never invent a balance", system_prompt.lower())
                    self.assertIn("10:00 a.m.", system_prompt)

    def test_next_meeting_is_first_saturday_strictly_after_today(self) -> None:
        self.assertEqual(
            sacco_assistant.next_meeting_date(date(2026, 10, 30)),
            date(2026, 11, 7),
        )
        self.assertEqual(
            sacco_assistant.next_meeting_date(date(2026, 11, 7)),
            date(2026, 12, 5),
        )

    def test_blank_question_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Please enter a question"):
            sacco_assistant.answer_question("   ", client=SimpleNamespace())


if __name__ == "__main__":
    unittest.main()
