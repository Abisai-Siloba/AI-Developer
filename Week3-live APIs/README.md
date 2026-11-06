# Thika Matatu SACCO Member Helper

A small Python command-line assistant for a matatu SACCO secretary. Enter a
member's question and Claude returns a short, friendly answer about balances,
meetings, or membership fees.

The assistant has sample SACCO details in its system prompt:

- The next monthly meeting is the first Saturday after today's date, at
  10:00 a.m. at the SACCO office near Thika Main Stage.
- The one-time joining fee is KSh 2,500.
- Monthly membership dues are KSh 1,000.
- Loans and qualifications.
- It does not have access to members' accounts, so it will not invent a
  personal balance. It directs members to ask the treasurer privately.

These are demo values. Update the system prompt in
`wk3_day1.1_first_api_call.py` to match your SACCO before using it with members.

## Requirements

- Python 3.10 or later
- An Anthropic API key
- Internet access

## Install

Open a terminal in this folder and install the dependency:

```powershell
python -m pip install -r requirements.txt
```

Set your API key for the current PowerShell window:

```powershell
$env:ANTHROPIC_API_KEY = "your_api_key_here"
```

Do not put the key in the script or commit it to GitHub.

## Run

```powershell
python wk3_day1.1_first_api_call.py
```

Type a question at the prompt, for example `What are the monthly fees?` The
script prints the answer and exits. Questions are sent to Anthropic to generate
an answer; avoid entering private member or financial details.

## Run the tests

```powershell
python -m unittest -v test_wk3_sacco_assistant.py
```

The offline tests exercise five different phrasings for each of the three
common question types (15 phrasings total) using a fake AI client. They do not
make API calls or require an API key.
