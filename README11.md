# Chama SMS Reminders

This guide covers setup, use, and a suggested price for the weekly meeting and
monthly contribution SMS reminders. Messages are sent through Africa's Talking.

## What it does

- Sends the meeting reminder every Friday at 8:00 a.m.
- Sends the contribution reminder on the 5th of each month at 8:00 a.m.
- Reads member names and international phone numbers from `contacts.csv`.
- Reads editable message text from `Week5_Automation\sms_messages.json`.
- Uses Windows Task Scheduler; the computer must be on and the configured
  Windows user signed in for the tasks to run.

Times use the computer's local time zone.

## Setup on Windows

1. Install the SMS dependencies from the repository root:

   ```powershell
   .venv\Scripts\python.exe -m pip install -r Week5_Automation\sms_requirements.txt
   ```

   If you do not have the repository's `.venv`, replace
   `.venv\Scripts\python.exe` with `python`.

2. Fill in the root `contacts.csv`. Keep the header as `name,phone`, and enter
   each phone number in international format, for example `+254712345678`.
   Remove members who should no longer receive reminders.

3. Edit `Week5_Automation\sms_messages.json` to change the meeting or
   contribution text. Keep both JSON keys (`meeting` and `contribution`) and
   give each a non-empty text value.

4. Add these settings to the root `.env` file:

   ```text
   SMS_USERNAME=sandbox
   SMS_API_KEY=your_africas_talking_api_key
   SMS_SENDER_ID=
   ```

   Use `sandbox` with a sandbox API key while testing. For live sends, use the
   live account username and key, and an approved sender ID if required. Keep
   `.env` private; never commit or share the API key.

5. Validate the contacts, messages, and credentials without sending SMS:

   ```powershell
   .venv\Scripts\python.exe Week5_Automation\wk5_day5_project_automation_tool.py --check
   ```

6. Register or update the Friday and monthly tasks:

   ```powershell
   .\Week5_Automation\setup_sms_tasks.ps1
   ```

   The setup script first runs the non-sending check. It uses `.venv` when
   present, otherwise `python` from `PATH`.

## Testing and manual sends

Use the Africa's Talking sandbox credentials and a sandbox simulator recipient
to test before switching to a live account. The `--check` command does not send
anything. These commands send immediately to every contact in `contacts.csv`,
so only use them when that is intended:

```powershell
.venv\Scripts\python.exe Week5_Automation\wk5_day5_project_automation_tool.py --meeting
.venv\Scripts\python.exe Week5_Automation\wk5_day5_project_automation_tool.py --contribution
```

Changing the message JSON file does not send a test message by itself.

## Suggested charges

These are example service prices in Kenyan shillings, not Africa's Talking
charges or a binding quote:

| Service | Suggested fee | Includes |
| --- | ---: | --- |
| Initial setup | KSh 5,000 once | Install dependencies, configure the two schedules, validate contacts and messages, and perform one sandbox test |
| Ongoing maintenance | KSh 1,500 per month | Monthly configuration and task check, minor contact/message edits, and basic troubleshooting |

SMS fees, sender ID fees, internet, and any Africa's Talking account charges are
excluded and paid by the chama directly to the provider. New features,
significant changes, or extra support outside the scope above should be quoted
separately. Agree on the fee and support response time with the client before
starting paid work.

## Maintenance checklist

- Once a month, run `--check` and confirm both tasks show a successful recent
  run in Windows Task Scheduler.
- Confirm the PC is powered on and the scheduled-task user is signed in around
  each send time.
- Keep the Africa's Talking account funded and the API key valid; rotate the key
  if it may have been exposed, then update `.env`.
- Update `contacts.csv` promptly when membership changes, and use only numbers
  whose owners have agreed to receive the reminders.
- Edit and review the JSON message text before a scheduled send.
- After code or dependency changes, run the focused tests:

  ```powershell
  .venv\Scripts\python.exe -m unittest discover -s Week5_Automation -p test_sms_reminders.py -v
  ```

- Back up contacts and message settings securely, but do not include `.env` or
  API credentials in backups shared with others.

To remove the scheduled tasks, run these commands in PowerShell:

```powershell
Unregister-ScheduledTask -TaskName "Chama Weekly Meeting SMS" -Confirm:$false
Unregister-ScheduledTask -TaskName "Chama Monthly Contribution SMS" -Confirm:$false
```