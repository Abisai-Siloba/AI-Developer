"""Answer tea-harvesting questions using current and forecast weather."""

from __future__ import annotations

import json
import os
from typing import Callable, Protocol
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


MODEL = "claude-haiku-4-5"
SYSTEM_PROMPT = """\
You are a practical field assistant for a tea estate in Kericho, Kenya.
Answer in plain language and base weather recommendations on the result of the
get_weather_forecast tool. When a question asks about weather, conditions, or
harvesting, you MUST call that tool before answering. Do not call it for
unrelated questions.

Tea harvesting guidance:
- Good conditions require no rain forecast in the next 6 hours, a temperature
  from 15°C through 25°C, and low relative humidity (70% or less).
- Active rain is bad for harvesting.
- Temperatures above 28°C are bad for harvesting.
- If conditions meet neither the good nor bad rules, describe them as mixed
  or uncertain rather than calling them good.
Give a direct recommendation and briefly explain which observed conditions
support it. Never claim weather values that are absent from the tool result.
"""

WEATHER_TOOL = {
    "name": "get_weather_forecast",
    "description": (
        "Get current conditions and the next six hours of weather for a location. "
        "Use this for weather, conditions, or tea-harvesting questions. "
        "The default location is Kericho, Kenya."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "A town or place name; defaults to Kericho, Kenya.",
            }
        },
        "required": [],
    },
}


class MessageResponse(Protocol):
    content: list[object]
    stop_reason: str


class Messages(Protocol):
    def create(self, **kwargs: object) -> MessageResponse: ...


class MessageClient(Protocol):
    messages: Messages


def _fetch_json(url: str) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": "TeaHarvestAssistant/1.0"})
    with urlopen(request, timeout=15) as response:
        try:
            payload = json.load(response)
        except json.JSONDecodeError as exc:
            raise RuntimeError("The weather service returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("The weather service returned an unexpected response.")
    return payload


def get_weather_forecast(location: str = "Kericho, Kenya") -> dict[str, object]:
    """Fetch current conditions and six forecast hours from Open-Meteo."""
    if not location.strip():
        raise ValueError("Please provide a location for the weather forecast.")

    geocoding_url = "https://geocoding-api.open-meteo.com/v1/search?" + urlencode(
        {"name": location.strip(), "count": 1, "language": "en", "format": "json"}
    )
    geocoding = _fetch_json(geocoding_url)
    results = geocoding.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError(f"No weather location found for '{location}'.")
    place = results[0]
    if not isinstance(place, dict):
        raise RuntimeError("The location service returned an unexpected result.")

    try:
        latitude = float(place["latitude"])
        longitude = float(place["longitude"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("The location service did not return valid coordinates.") from exc

    forecast_url = "https://api.open-meteo.com/v1/forecast?" + urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,rain,precipitation",
            "hourly": (
                "temperature_2m,relative_humidity_2m,precipitation_probability,"
                "precipitation,rain"
            ),
            "forecast_hours": 6,
            "timezone": "auto",
        }
    )
    forecast = _fetch_json(forecast_url)
    current = forecast.get("current")
    hourly = forecast.get("hourly")
    if not isinstance(current, dict) or not isinstance(hourly, dict):
        raise RuntimeError("The weather service did not return current and hourly data.")

    hourly_fields = (
        "time",
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation_probability",
        "precipitation",
        "rain",
    )
    if any(not isinstance(hourly.get(field), list) for field in hourly_fields):
        raise RuntimeError("The weather service returned incomplete hourly data.")
    if any(not isinstance(current.get(field), (int, float)) for field in (
        "temperature_2m",
        "relative_humidity_2m",
        "rain",
        "precipitation",
    )):
        raise RuntimeError("The weather service returned incomplete current conditions.")

    times = hourly["time"]
    hourly_values = [hourly[field] for field in hourly_fields[1:]]
    hours = [
        {
            "time": times[index],
            "temperature_c": hourly_values[0][index],
            "relative_humidity_percent": hourly_values[1][index],
            "precipitation_probability_percent": hourly_values[2][index],
            "precipitation_mm": hourly_values[3][index],
            "rain_mm": hourly_values[4][index],
        }
        for index in range(min(6, *(len(values) for values in [times, *hourly_values])))
    ]
    if not hours:
        raise RuntimeError("The weather service returned no forecast hours.")

    return {
        "location": ", ".join(
            str(part) for part in (place.get("name"), place.get("country"))
            if part
        ),
        "timezone": forecast.get("timezone"),
        "current": {
            "temperature_c": current["temperature_2m"],
            "relative_humidity_percent": current["relative_humidity_2m"],
            "rain_mm": current["rain"],
            "precipitation_mm": current["precipitation"],
        },
        "next_6_hours": hours,
    }


def _create_client() -> MessageClient:
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
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    return anthropic.Anthropic(api_key=api_key)


def answer_question(
    question: str,
    client: MessageClient | None = None,
    weather_tool: Callable[[str], dict[str, object]] | None = None,
) -> str:
    """Ask Claude a question and run any weather tool calls it requests."""
    if not question.strip():
        raise ValueError("Please enter a question.")

    if client is None:
        client = _create_client()
    if weather_tool is None:
        weather_tool = get_weather_forecast

    messages: list[dict[str, object]] = [
        {"role": "user", "content": question.strip()}
    ]
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        tools=[WEATHER_TOOL],
        messages=messages,
    )

    while response.stop_reason == "tool_use":
        tool_results: list[dict[str, object]] = []
        for block in response.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            tool_name = getattr(block, "name", None)
            if tool_name != WEATHER_TOOL["name"]:
                raise RuntimeError(f"Unknown tool requested: {tool_name}")
            tool_input = getattr(block, "input", None)
            if not isinstance(tool_input, dict):
                raise RuntimeError("The AI returned invalid weather-tool input.")
            location = tool_input.get("location", "Kericho, Kenya")
            if not isinstance(location, str):
                raise RuntimeError("The AI returned an invalid weather location.")

            result = weather_tool(location)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": getattr(block, "id", ""),
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        if not tool_results:
            raise RuntimeError("The AI requested a tool but provided no tool call.")
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            tools=[WEATHER_TOOL],
            messages=messages,
        )

    answer = "\n".join(
        text.strip()
        for block in response.content
        if getattr(block, "type", None) == "text"
        and isinstance((text := getattr(block, "text", None)), str)
        and text.strip()
    )
    if not answer:
        raise RuntimeError("The AI returned an empty answer. Please try again.")
    return answer


def main() -> None:
    try:
        import anthropic
    except ImportError:
        print(
            "Error: The Anthropic package is missing. Install it with "
            "'python -m pip install -r requirements.txt'."
        )
        return

    print("Tea Harvest Assistant (Kericho).")
    question = input("Your question: ").strip()
    try:
        print(f"\nAssistant: {answer_question(question)}")
    except anthropic.APIConnectionError:
        print("\nError: Could not connect to Anthropic. Check your internet connection.")
    except anthropic.AuthenticationError:
        print("\nError: The API key was rejected. Check ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        print("\nError: The AI service is busy. Wait a moment and try again.")
    except anthropic.APIError as exc:
        print(f"\nError: The AI service returned an error: {exc}")
    except (RuntimeError, ValueError, URLError, TimeoutError) as exc:
        print(f"\nError: {exc}")


if __name__ == "__main__":
    main()