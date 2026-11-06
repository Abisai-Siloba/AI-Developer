# Kericho Tea Harvest Assistant

A command-line AI assistant for a tea estate field supervisor. Ask a question
about the weather or harvesting and it gets current conditions and the next
six hours of forecast for the requested location (Kericho, Kenya by default),
then gives a practical recommendation in plain language.

The assistant applies these harvesting guidelines:

- Good conditions: no rain forecast in the next six hours, temperature from
  15°C through 25°C, and relative humidity of 70% or less.
- Bad conditions: active rain or temperatures above 28°C.
- If neither rule clearly applies, the assistant describes conditions as mixed
  or uncertain.

Weather and harvesting questions use the weather tool. Unrelated questions do
not. Weather data is provided by Open-Meteo; no weather API key is required.

## Requirements

- Python 3.10 or later
- An Anthropic API key
- Internet access

## Install

In PowerShell, from the repository root:

```powershell
python -m pip install -r "Week3-live APIs\requirements.txt"
$env:ANTHROPIC_API_KEY = "your_api_key_here"
Set-Location "Week3-live APIs"
```

Keep the API key in your environment; do not put it in the script or commit it
to the repository.

## Run

```powershell
python "wk3_day4.1_function-calling-and-AI-agents.py"
```

Enter a question at the prompt, such as `Is today good for harvesting?` or
`Will it rain in the next six hours?` You can also ask about another location,
for example `Is it good for harvesting in Kericho today?`

## Run the offline tests

From the `Week3-live APIs` folder:

```powershell
python -m unittest discover -s . -p test_wk3_day4_function_calling.py -v
```

The tests use a fake AI client and weather response; they do not make AI or
weather API calls and do not require an API key.
