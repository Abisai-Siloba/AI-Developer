"""Email and notification automation."""

import argparse
import logging
import os
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    filename="email_log.txt",
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
)


def send_message(msg):
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

    missing_settings = [
        name
        for name, value in (
            ("GMAIL_ADDRESS", gmail_address),
            ("GMAIL_APP_PASSWORD", gmail_app_password),
        )
        if not value
    ]
    if missing_settings:
        print(
            f"Missing required environment variable(s): {', '.join(missing_settings)}",
            file=sys.stderr,
        )
        return False

    msg["From"] = gmail_address

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(gmail_address, gmail_app_password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        print(f"Email authentication failed: {exc}", file=sys.stderr)
    except smtplib.SMTPRecipientsRefused as exc:
        print(f"Recipient was refused: {exc.recipients}", file=sys.stderr)
    except smtplib.SMTPSenderRefused as exc:
        print(f"Sender was refused: {exc.smtp_error}", file=sys.stderr)
    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as exc:
        print(f"Could not connect to the email server: {exc}", file=sys.stderr)
    except smtplib.SMTPException as exc:
        print(f"SMTP error while sending email: {exc}", file=sys.stderr)
    except TimeoutError as exc:
        print(f"Email server timed out: {exc}", file=sys.stderr)
    except OSError as exc:
        print(f"Network error while sending email: {exc}", file=sys.stderr)
    else:
        print(f"Email sent to `{msg['To']}` successfully.")
        return True

    return False


def send_email(to, subject, body):
    if not to or not subject or not body:
        print("Recipient, subject, and body are required.", file=sys.stderr)
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["To"] = to
    return send_message(msg)


def send_html_report(to, data):
    if not to:
        print("Recipient is required.", file=sys.stderr)
        return False

    required_fields = (
        "nairobi_orders",
        "nairobi_revenue",
        "mombasa_orders",
        "mombasa_revenue",
    )
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        print(
            f"Report data is missing required field(s): {', '.join(missing_fields)}",
            file=sys.stderr,
        )
        return False

    html_body = (
        '<html><body style="font-family: Arial, sans-serif;">'
        "<h2 style=\"color: #1F4E79;\">Daily Sales Report</h2>"
        '<table border="1" cellpadding="8" style="border-collapse:collapse;">'
        '<tr style="background:#1F4E79; color:white;"><th>County</th>'
        "<th>Orders</th><th>Revenue (KES)</th></tr>"
        f'<tr><td>Nairobi</td><td>{data["nairobi_orders"]}</td>'
        f'<td>{data["nairobi_revenue"]:,.2f}</td></tr>'
        f'<tr><td>Mombasa</td><td>{data["mombasa_orders"]}</td>'
        f'<td>{data["mombasa_revenue"]:,.2f}</td></tr>'
        "</table></body></html>"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Daily Sales Report"
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))
    return send_message(msg)


def fetch_todays_data():
    """Return today's report data.

    Replace this sample data with a database or API query for production use.
    """
    return {
        "nairobi_orders": 0,
        "nairobi_revenue": 0,
        "mombasa_orders": 0,
        "mombasa_revenue": 0,
    }


def daily_report_job():
    try:
        recipient = os.getenv("REPORT_RECIPIENT")
        if not recipient:
            raise ValueError("REPORT_RECIPIENT is not configured")

        data = fetch_todays_data()
        if send_html_report(recipient, data):
            logging.info("OK - daily report sent")
        else:
            logging.error("FAILED - daily report could not be sent")
    except Exception as exc:
        logging.error("FAILED - %s", exc)


def run_scheduler():
    try:    
        import schedule
    except ImportError:
        print("The 'schedule' package is required; install it with 'pip install schedule'.", file=sys.stderr)
        return

    report_time = os.getenv("REPORT_TIME", "08:00")
    schedule.every().day.at(report_time).do(daily_report_job)
    print(f"Daily report scheduler started for {report_time}.")

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Send email or sales report notifications.")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="run the daily report scheduler instead of sending a test email",
    )
    args = parser.parse_args()

    if args.schedule:
        run_scheduler()
    else:
        recipient = os.getenv("TEST_EMAIL_RECIPIENT") or os.getenv("GMAIL_ADDRESS")
        send_email(
            to=recipient,
            subject="Weekly sales report",
            body="Hello,\n\nThis is a test email for app automation.\n\nRegards",
        )


if __name__ == "__main__":
    main()