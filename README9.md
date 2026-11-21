# Daily Nairobi Shop Sales Email

The script in `Week5_Automation/email_automation.py` totals sales, counts
distinct transaction IDs, identifies the item(s) with the highest quantity
sold, and flags inventory below its restock level. It sends a formatted HTML
summary through Gmail SMTP and uses Kenyan shillings (KES).

## Files and setup

- `Week5_Automation/sales.csv` is a 12-row sample. Each row is a sold item;
  transaction IDs may repeat when one transaction contains multiple items.
- `Week5_Automation/inventory.csv` provides each item's current stock and
  restock level. An alert is raised when current stock is strictly below that
  level.
- Copy `Week5_Automation/.env.example` to `.env` in the project root and fill
  in your Gmail address, Gmail app password, and report recipient. The existing
  `.gitignore` excludes `.env`; never commit the real credentials.
- Use a Gmail app password (with Google 2-Step Verification enabled), not the
  account's normal password.

The cashier should update `sales.csv` during the day and keep `inventory.csv`
current. The script expects columns `transaction_id,item_name,quantity_sold,price_kes`
in the sales file and `item_name,stock_remaining,restock_level` in inventory.
Prices are unit prices.

## Run and schedule

From the project root, preview the report without reading credentials or
sending email:

```powershell
.\.venv\Scripts\python.exe .\Week5_Automation\email_automation.py --dry-run
```

Send the report immediately after configuring `.env`:

```powershell
.\.venv\Scripts\python.exe .\Week5_Automation\email_automation.py
```

Check Gmail SMTP authentication without sending a report:

```powershell
.\.venv\Scripts\python.exe .\Week5_Automation\email_automation.py --check-smtp
```

To send it every day at 6:00pm Nairobi time, create a daily task in Windows
Task Scheduler. Set the trigger to 6:00pm and use:

- **Program/script:** `C:\Users\<you>\abisai-ai-demo-ii\.venv\Scripts\python.exe`
- **Arguments:** `C:\Users\<you>\abisai-ai-demo-ii\Week5_Automation\email_automation.py`
- **Start in:** `C:\Users\<you>\abisai-ai-demo-ii\Week5_Automation`

Set Windows to the `Africa/Nairobi` time zone so the 6:00pm trigger is local to
Nairobi. Keep the computer on and connected to the internet at the scheduled
time.

## Validation

Run the focused checks from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\Week5_Automation -p "test_email_automation.py"
```

The test uses a mocked SMTP server; it verifies the generated HTML and SMTP
message without delivering an email.

If Gmail rejects authentication, verify the Gmail address and app password in
`.env`, generate a fresh app password in the Google Account's App passwords
page, and confirm 2-Step Verification is enabled. Replace any revoked password
in `.env`, then run `--check-smtp` before sending. Google Workspace policies
may disable app passwords. If the connection drops during email submission,
delivery may be uncertain; check the recipient's inbox before retrying to avoid
duplicate reports.

## Suggested client pricing

For a single small shop using its existing CSV and Gmail account, I would
charge **KES 15,000 as a one-off implementation fee** for setup, testing, and
handover. I would offer an optional **KES 2,000/month support retainer** for
monitoring, small changes, and help with Gmail or CSV issues. I would not make
the basic automation itself a monthly subscription; a retainer only makes
sense if the owner wants ongoing support.