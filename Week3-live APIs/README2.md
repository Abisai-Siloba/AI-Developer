# Nairobi Property Inquiry Extractor

This command-line script takes a raw WhatsApp property inquiry and uses
Anthropic's Claude API to extract its requirements as JSON. It parses the JSON
into a Python dictionary and prints each field with a readable label. Missing
or unclear details are shown as `Not specified`, not guessed.

## Extracted fields

- `property_type`: The requested type, such as a house, apartment, or bedsitter.
  This helps the agent match the inquiry to the right listings.
- `bedrooms`: The requested bedroom count (a bedsitter is represented as `0`).
  This narrows the search to suitable properties.
- `location`: The named neighborhood or area. This helps find listings in the
  client's preferred part of Nairobi.
- `budget_kes`: The budget in Kenyan shillings, normalized to a whole number
  (for example, `80k` becomes `80000`). This helps filter by affordability.
- `rental_or_sale`: Whether the client is looking to rent or buy. This helps
  route the inquiry to the right listings and process.

## Requirements

- Python 3.10 or later
- An Anthropic API key
- Internet access

Install the dependency from this folder:

```powershell
python -m pip install -r requirements.txt
```

Create a `.env` file in this folder or the repository root and add your API
key:

```text
ANTHROPIC_API_KEY=your_api_key_here
```

The script loads this value from `.env`. The file is ignored by Git; do not put
the key in the script or commit it to GitHub. Alternatively, set
`ANTHROPIC_API_KEY` in your environment before running the script.

## Run

```powershell
python wk3_day2.1_Prompt_engineering.py
```

Enter an inquiry when prompted, for example:

```text
I am looking for a 3-bedroom house in Kileleshwa, budget around 80k per month
```

The script prints the extracted property type, bedroom count, location, budget,
and whether it is a rental or sale. An absent or unclear field is returned as
JSON `null` and printed as `Not specified`.

## Test

Run the offline tests with:

```powershell
python -m unittest -v test_property_inquiry_extractor.py
```

The tests cover a 3-bedroom rental inquiry, a bedsitter inquiry with unclear
rental-or-sale intent, a purchase inquiry with missing bedrooms and budget,
and a separate inquiry with multiple missing fields. They use a fake API client
and do not require an API key or make network requests.