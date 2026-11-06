import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).with_name(
    "wk3_day4.1_function-calling-and-AI-agents.py"
)
SPEC = importlib.util.spec_from_file_location("tea_harvest_agent", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load script from {SCRIPT_PATH}")
tea_agent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tea_agent)


class FakeMessages:
    def __init__(self, use_weather: bool) -> None:
        self.use_weather = use_weather
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.use_weather and len(self.calls) == 1:
            return SimpleNamespace(
                stop_reason="tool_use",
                content=[
                    SimpleNamespace(
                        type="tool_use",
                        id="weather-call",
                        name="get_weather_forecast",
                        input={"location": "Kericho, Kenya"},
                    )
                ],
            )
        return SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text="A practical answer.")],
        )


class TeaHarvestAgentTests(unittest.TestCase):
    def test_weather_question_calls_tool_and_unrelated_questions_do_not(self) -> None:
        questions = [
            ("Is today good for harvesting?", True),
            ("How are tea leaves processed after picking?", False),
            ("Tell me a short joke about a teacup.", False),
        ]
        weather_calls: list[str] = []

        for question, should_use_weather in questions:
            with self.subTest(question=question):
                messages = FakeMessages(use_weather=should_use_weather)
                client = SimpleNamespace(messages=messages)

                def fake_weather(location: str) -> dict[str, object]:
                    weather_calls.append(location)
                    return {
                        "location": "Kericho, Kenya",
                        "current": {"temperature_c": 20},
                        "next_6_hours": [],
                    }

                answer = tea_agent.answer_question(
                    question,
                    client=client,
                    weather_tool=fake_weather,
                )

                self.assertEqual(answer, "A practical answer.")
                self.assertEqual(len(messages.calls), 2 if should_use_weather else 1)
                self.assertIn("MUST call that tool", messages.calls[0]["system"])
                self.assertIn("70% or less", messages.calls[0]["system"])

        self.assertEqual(weather_calls, ["Kericho, Kenya"])

    def test_weather_tool_normalizes_current_and_six_hour_forecast(self) -> None:
        location_response = {
            "results": [
                {
                    "name": "Kericho",
                    "country": "Kenya",
                    "latitude": -0.37,
                    "longitude": 35.29,
                }
            ]
        }
        forecast_response = {
            "timezone": "Africa/Nairobi",
            "current": {
                "temperature_2m": 20.0,
                "relative_humidity_2m": 65,
                "rain": 0.0,
                "precipitation": 0.0,
            },
            "hourly": {
                "time": ["06:00", "07:00"],
                "temperature_2m": [20.0, 21.0],
                "relative_humidity_2m": [65, 64],
                "precipitation_probability": [0, 10],
                "precipitation": [0.0, 0.0],
                "rain": [0.0, 0.0],
            },
        }
        with patch.object(
            tea_agent,
            "_fetch_json",
            side_effect=[location_response, forecast_response],
        ):
            result = tea_agent.get_weather_forecast()

        self.assertEqual(result["location"], "Kericho, Kenya")
        self.assertEqual(result["current"]["temperature_c"], 20.0)
        self.assertEqual(len(result["next_6_hours"]), 2)
        self.assertEqual(
            result["next_6_hours"][1]["precipitation_probability_percent"], 10
        )

    def test_empty_question_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Please enter a question"):
            tea_agent.answer_question("  ", client=SimpleNamespace())


if __name__ == "__main__":
    unittest.main()
