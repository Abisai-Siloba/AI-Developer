# Daily Sales Email

The day-4 script reads `Week5_Automation/sales.csv` and `inventory.csv`,
calculates the revenue, transaction count, top-selling item, and restock
alert, then sends an HTML summary by Gmail.

## Setup in three steps

1. Copy `Week5_Automation/.env.example` to the project-root `.env` file and set
   `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, and `REPORT_RECIPIENT`.
2. From the project root, run:
   `.\.venv\Scripts\python.exe .\Week5_Automation\wk5_day4_scheduling_and_persistent_scripts.py`
3. In Windows Task Scheduler, create a daily 6:00pm task using that Python
   executable, this script path, and the project folder as its start location.
   Keep the computer online and set its time zone to `Africa/Nairobi`.

Use a Gmail app password and enable Google 2-Step Verification. Each run
appends its date, time, success or error status, and sales-row count to
`Week5_Automation/email_run_log.txt`.
