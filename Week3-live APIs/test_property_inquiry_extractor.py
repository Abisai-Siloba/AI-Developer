import contextlib
import io
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPT_PATH = Path(__file__).with_name("wk3_day2.1_Prompt_engineering.py")
SPEC = importlib.util.spec_from_file_location("property_inquiry_extractor", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load script from {SCRIPT_PATH}")
property_inquiry_extractor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(property_inquiry_extractor)


class FakeMessages:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(text=self.response_text)]
        )


class PropertyInquiryExtractorTests(unittest.TestCase):
    def test_extracts_property_rental_and_sale_inquiries(self) -> None:
        examples = [
            (
                "I am looking for a 3-bedroom house in Kileleshwa, "
                "budget around 80k per month",
                '{"property_type":"house","bedrooms":3,"location":"Kileleshwa",'
                '"budget_kes":80000,"rental_or_sale":"rental"}',
                {
                    "property_type": "house",
                    "bedrooms": 3,
                    "location": "Kileleshwa",
                    "budget_kes": 80000,
                    "rental_or_sale": "rental",
                },
            ),
            (
                "Do you have any bedsitters near Westlands under 20k?",
                '{"property_type":"bedsitter","bedrooms":0,"location":"Westlands",'
                '"budget_kes":20000,"rental_or_sale":null}',
                {
                    "property_type": "bedsitter",
                    "bedrooms": 0,
                    "location": "Westlands",
                    "budget_kes": 20000,
                    "rental_or_sale": None,
                },
            ),
            (
                "I want to buy an apartment in Kilimani",
                '{"property_type":"apartment","bedrooms":null,"location":"Kilimani",'
                '"budget_kes":null,"rental_or_sale":"sale"}',
                {
                    "property_type": "apartment",
                    "bedrooms": None,
                    "location": "Kilimani",
                    "budget_kes": None,
                    "rental_or_sale": "sale",
                },
            ),
        ]

        for inquiry, response_text, expected in examples:
            with self.subTest(inquiry=inquiry):
                messages = FakeMessages(response_text)
                client = SimpleNamespace(messages=messages)

                actual = property_inquiry_extractor.extract_inquiry(
                    inquiry, client=client
                )

                self.assertEqual(actual, expected)
                self.assertEqual(len(messages.calls), 1)
                request = messages.calls[0]
                self.assertEqual(
                    request["messages"], [{"role": "user", "content": inquiry}]
                )
                self.assertIn("exactly one valid JSON object", request["system"])
                self.assertIn('"budget_kes"', request["system"])

    def test_missing_fields_are_printed_as_not_specified(self) -> None:
        messages = FakeMessages(
            '{"property_type":null,"bedrooms":null,"location":"Nairobi",'
            '"budget_kes":null,"rental_or_sale":null}'
        )
        details = property_inquiry_extractor.extract_inquiry(
            "I am looking for a place in Nairobi.",
            client=SimpleNamespace(messages=messages),
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            property_inquiry_extractor.print_inquiry(details)

        self.assertEqual(details["location"], "Nairobi")
        self.assertIsNone(details["budget_kes"])
        self.assertIn("Location: Nairobi", output.getvalue())
        self.assertIn("Budget (KES): Not specified", output.getvalue())
        self.assertIn("Bedrooms: Not specified", output.getvalue())

    def test_invalid_json_is_reported(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
            property_inquiry_extractor._parse_inquiry_json("not JSON")

    def test_blank_inquiry_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Please enter a property inquiry"):
            property_inquiry_extractor.extract_inquiry("   ", client=SimpleNamespace())


if __name__ == "__main__":
    unittest.main()
