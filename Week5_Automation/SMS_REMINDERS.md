# Chama SMS reminders

The script sends the weekly meeting reminder every Friday and the contribution
reminder on the 5th of each month. Windows Task Scheduler runs both at 8:00 a.m.
using the computer's local time.

## Configure

1. Add members to the root `contacts.csv`, with columns `name,phone`. Use
   international phone numbers, for example `+254712345678`.
2. Edit the message text in `sms_messages.json`. Keep the `meeting` and
   `contribution` entries as non-empty strings.
3. Install the dependencies into the repository's `.venv` from the repository
   root. If `.venv` does not exist, replace `.venv\Scripts\python.exe` with
   `python`:

   ```powershell
   .venv\Scripts\python.exe -m pip install -r Week5_Automation\sms_requirements.txt
   ```

4. Add the settings below to the root `.env` file. Get the API key from the
   Africa's Talking dashboard. Use `sandbox` for sandbox credentials or your
   live account username for production. `SMS_SENDER_ID` is optional.

   ```text
   SMS_USERNAME=sandbox
   SMS_API_KEY=your_api_key
   SMS_SENDER_ID=
   ```

5. Check the configuration without sending an SMS, then register both tasks:

   ```powershell
   .venv\Scripts\python.exe Week5_Automation\wk5_day5_project_automation_tool.py --check
   .\Week5_Automation\setup_sms_tasks.ps1
   ```

The setup script uses the repository's `.venv` Python when available, otherwise
the `python` on `PATH`. Scheduled tasks run as the current Windows user; the
computer must be on and that user signed in at the scheduled time. Configure
Windows to use the intended local time zone.

The API key belongs in `.env`, which is ignored by Git. Never put it in the
script or commit it. The example `sms.env.example` contains placeholders only.
