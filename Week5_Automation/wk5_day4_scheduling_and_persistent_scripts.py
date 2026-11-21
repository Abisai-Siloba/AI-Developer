"""Daily Nairobi shop sales email with persistent run logging."""

import argparse
import csv
from datetime import datetime
import html
import os
import smtplib
import sys
import time
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
LOG_PATH = SCRIPT_DIR / "email_run_log.txt"


class EmailDeliveryError(Exception):
    """A user-facing Gmail delivery error."""


@dataclass(frozen=True)
class InventoryItem:
    stock_remaining: int
    restock_level: int


@dataclass(frozen=True)
class SalesSummary:
    revenue: Decimal
    transaction_count: int
    top_selling_items: tuple[tuple[str, int], ...]
    low_stock_items: tuple[tuple[str, InventoryItem], ...]


def _load_env_file() -> None:
    """Load .env from common project locations without stale env shadowing."""
    candidates = (
        PROJECT_DIR / ".env",
        SCRIPT_DIR / ".env",
        Path.cwd() / ".env",
    )
    for env_path in candidates:
        if env_path.is_file():
            load_dotenv(env_path, override=True)
            return


def _read_csv(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"{path} is empty or has no CSV header.")
        missing = required_columns.difference(reader.fieldnames)
        if missing:
            raise ValueError(
                f"{path} is missing required column(s): {', '.join(sorted(missing))}."
            )
        return [row for row in reader if any(value for value in row.values())]


def _parse_nonnegative_int(value: str, column: str, row_number: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"CSV row {row_number}: {column} must be a whole number."
        ) from exc
    if parsed < 0:
        raise ValueError(f"CSV row {row_number}: {column} cannot be negative.")
    return parsed


def calculate_summary(sales_csv: Path, inventory_csv: Path) -> SalesSummary:
    sales_rows = _read_csv(
        sales_csv,
        {"transaction_id", "item_name", "quantity_sold", "price_kes"},
    )
    inventory_rows = _read_csv(
        inventory_csv,
        {"item_name", "stock_remaining", "restock_level"},
    )
    if not sales_rows:
        raise ValueError(f"{sales_csv} contains no sales.")

    revenue = Decimal("0")
    item_quantities: Counter[str] = Counter()
    transaction_ids: set[str] = set()
    for row_number, row in enumerate(sales_rows, start=2):
        transaction_id = row["transaction_id"].strip()
        item_name = row["item_name"].strip()
        if not transaction_id or not item_name:
            raise ValueError(
                f"Sales CSV row {row_number}: transaction_id and item_name are required."
            )
        quantity = _parse_nonnegative_int(
            row["quantity_sold"], "quantity_sold", row_number
        )
        if quantity == 0:
            raise ValueError(
                f"Sales CSV row {row_number}: quantity_sold must be positive."
            )
        try:
            price = Decimal(row["price_kes"])
        except (InvalidOperation, TypeError) as exc:
            raise ValueError(
                f"Sales CSV row {row_number}: price_kes must be a valid amount."
            ) from exc
        if not price.is_finite() or price < 0:
            raise ValueError(
                f"Sales CSV row {row_number}: price_kes must be finite and nonnegative."
            )
        revenue += quantity * price
        item_quantities[item_name] += quantity
        transaction_ids.add(transaction_id)

    inventory: dict[str, InventoryItem] = {}
    for row_number, row in enumerate(inventory_rows, start=2):
        item_name = row["item_name"].strip()
        if not item_name:
            raise ValueError(f"Inventory CSV row {row_number}: item_name is required.")
        if item_name in inventory:
            raise ValueError(
                f"Inventory CSV row {row_number}: duplicate item_name {item_name!r}."
            )
        inventory[item_name] = InventoryItem(
            stock_remaining=_parse_nonnegative_int(
                row["stock_remaining"], "stock_remaining", row_number
            ),
            restock_level=_parse_nonnegative_int(
                row["restock_level"], "restock_level", row_number
            ),
        )

    missing = sorted(set(item_quantities).difference(inventory))
    if missing:
        raise ValueError(
            "Inventory CSV has no stock level for: " + ", ".join(missing)
        )

    top_quantity = max(item_quantities.values())
    top_items = tuple(
        sorted(
            (name, quantity)
            for name, quantity in item_quantities.items()
            if quantity == top_quantity
        )
    )
    low_stock = tuple(
        sorted(
            (name, item)
            for name, item in inventory.items()
            if item.stock_remaining < item.restock_level
        )
    )
    return SalesSummary(
        revenue=revenue,
        transaction_count=len(transaction_ids),
        top_selling_items=top_items,
        low_stock_items=low_stock,
    )


def build_email(summary: SalesSummary, recipient: str) -> EmailMessage:
    cleaned_recipient = recipient.strip()
    if not cleaned_recipient:
        raise ValueError("REPORT_RECIPIENT must be set to an email address.")
    top_items_text = ", ".join(
        f"{name} ({quantity} units)"
        for name, quantity in summary.top_selling_items
    )
    if summary.low_stock_items:
        low_stock_text = ", ".join(
            f"{name} ({item.stock_remaining} left; restock at {item.restock_level})"
            for name, item in summary.low_stock_items
        )
        stock_status = f"Restock required: {low_stock_text}"
    else:
        stock_status = "All items are at or above their restock levels."

    html_body = (
        '<html><body style="font-family:Arial,sans-serif;color:#243447;">'
        '<h2 style="color:#176b57;">Daily Sales Summary</h2>'
        '<table style="border-collapse:collapse;width:100%;" '
        'cellpadding="10" border="1">'
        '<tr><th align="left">Metric</th><th align="left">Today</th></tr>'
        f"<tr><td>Total revenue</td><td>KES {summary.revenue:,.2f}</td></tr>"
        f"<tr><td>Transactions</td><td>{summary.transaction_count}</td></tr>"
        f"<tr><td>Top-selling item</td><td>{html.escape(top_items_text)}</td></tr>"
        f"<tr><td>Restock alert</td><td>{html.escape(stock_status)}</td></tr>"
        "</table></body></html>"
    )
    text_body = (
        "Daily Sales Summary\n"
        f"Total revenue: KES {summary.revenue:,.2f}\n"
        f"Transactions: {summary.transaction_count}\n"
        f"Top-selling item: {top_items_text}\n"
        f"Restock alert: {stock_status}\n"
    )
    message = EmailMessage()
    message["Subject"] = "Daily Sales Summary"
    message["To"] = cleaned_recipient
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    return message


def _gmail_credentials() -> tuple[str, str]:
    address_value = os.getenv("GMAIL_ADDRESS")
    password_value = os.getenv("GMAIL_APP_PASSWORD")
    address = address_value.strip() if isinstance(address_value, str) else ""
    password = (
        password_value.replace(" ", "")
        if isinstance(password_value, str)
        else ""
    ).strip()
    missing = [
        name
        for name, value in (
            ("GMAIL_ADDRESS", address),
            ("GMAIL_APP_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        raise ValueError("Missing .env setting(s): " + ", ".join(missing))
    return address, password


def _smtp_attempt(
    port: int,
    address: str,
    password: str,
    message: EmailMessage | None = None,
) -> None:
    stage = "connect"
    try:
        if port == 465:
            server_ctx = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
        elif port == 587:
            server_ctx = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        else:
            raise ValueError(f"Unsupported SMTP port: {port}")

        with server_ctx as server:
            if port == 587:
                stage = "starttls"
                server.ehlo()
                server.starttls()
                server.ehlo()
            stage = "login"
            server.login(address, password)
            if message is not None:
                stage = "send"
                server.send_message(message)
    except smtplib.SMTPAuthenticationError as exc:
        raise EmailDeliveryError(
            "Gmail rejected GMAIL_ADDRESS or GMAIL_APP_PASSWORD (535). "
            "Verify 2-Step Verification is enabled and use a valid 16-character "
            "App Password."
        ) from exc
    except smtplib.SMTPServerDisconnected as exc:
        if stage in ("login", "send"):
            raise EmailDeliveryError(
                f"Gmail closed the connection during {stage} on port {port} "
                "(often caused by rejected credentials or account/Workspace policy)."
            ) from exc
        raise
    except smtplib.SMTPException as exc:
        raise EmailDeliveryError(
            f"Gmail SMTP error during {stage} on port {port}: {exc}"
        ) from exc


def _run_smtp_with_fallback(message: EmailMessage | None = None) -> None:
    address, password = _gmail_credentials()
    prepared_message: EmailMessage | None = None
    if message is not None:
        prepared_message = message
        prepared_message["From"] = address

    last_network_error: Exception | None = None
    for port in (465, 587):
        try:
            _smtp_attempt(port, address, password, prepared_message)
            return
        except EmailDeliveryError:
            raise
        except (
            smtplib.SMTPServerDisconnected,
            smtplib.SMTPConnectError,
            TimeoutError,
            OSError,
        ) as exc:
            last_network_error = exc

    raise EmailDeliveryError(
        f"Could not reach Gmail SMTP on ports 465 and 587: {last_network_error}"
    ) from last_network_error


def send_email(message: EmailMessage) -> None:
    _run_smtp_with_fallback(message=message)


def check_smtp_authentication() -> None:
    _run_smtp_with_fallback(message=None)


def append_run_log(status: str, rows_processed: int) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"{timestamp} | status={status.lower()} | "
            f"rows_processed={rows_processed}\n"
        )


def count_sales_rows(sales_csv: Path) -> int:
    if not sales_csv.exists():
        return 0
    with sales_csv.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return sum(
            1
            for row in csv.DictReader(csv_file)
            if any(value for value in row.values())
        )


def run_report(sales_csv: Path, inventory_csv: Path) -> int:
    summary = calculate_summary(sales_csv, inventory_csv)
    recipient = os.getenv("REPORT_RECIPIENT", "").strip()
    send_email(build_email(summary, recipient))
    return count_sales_rows(sales_csv)


def run_scheduler(report_time: str) -> None:
    try:
        import schedule
    except ImportError as exc:
        raise RuntimeError(
            "Install the schedule package with "
            "'python -m pip install schedule'."
        ) from exc

    def scheduled_job() -> None:
        try:
            rows = run_report(
                SCRIPT_DIR / "sales.csv", SCRIPT_DIR / "inventory.csv"
            )
            append_run_log("success", rows)
            print(f"Scheduled sales summary sent; {rows} sales rows processed.")
        except Exception as exc:
            try:
                rows = count_sales_rows(SCRIPT_DIR / "sales.csv")
            except (OSError, csv.Error):
                rows = 0
            append_run_log("error", rows)
            print(f"Scheduled sales summary failed: {exc}", file=sys.stderr)

    schedule.every().day.at(report_time).do(scheduled_job)
    print(f"Sales summary scheduler started for {report_time} daily.")
    while True:
        schedule.run_pending()
        time.sleep(30)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send and schedule a daily shop sales summary."
    )
    parser.add_argument(
        "--sales-csv", type=Path, default=SCRIPT_DIR / "sales.csv"
    )
    parser.add_argument(
        "--inventory-csv", type=Path, default=SCRIPT_DIR / "inventory.csv"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check-smtp", action="store_true")
    mode.add_argument("--schedule", action="store_true")
    args = parser.parse_args()

    _load_env_file()

    if args.schedule:
        try:
            run_scheduler(os.getenv("REPORT_TIME", "18:00").strip())
        except (RuntimeError, ValueError) as exc:
            parser.exit(1, f"Scheduler failed: {exc}\n")
        return

    if args.check_smtp:
        try:
            check_smtp_authentication()
        except (
            EmailDeliveryError,
            smtplib.SMTPAuthenticationError,
            smtplib.SMTPException,
            TimeoutError,
            OSError,
            ValueError,
        ) as exc:
            parser.exit(1, f"SMTP check failed: {exc}\n")
        print("Gmail SMTP authentication succeeded; no email was sent.")
        return

    rows = 0
    recipient = ""
    try:
        rows = count_sales_rows(args.sales_csv)
        summary = calculate_summary(args.sales_csv, args.inventory_csv)
        recipient = os.getenv("REPORT_RECIPIENT", "").strip()
        message = build_email(summary, recipient)
        if args.dry_run:
            print(message)
            append_run_log("success", rows)
            return
        send_email(message)
    except (
        EmailDeliveryError,
        smtplib.SMTPAuthenticationError,
        OSError,
        ValueError,
    ) as exc:
        append_run_log("error", rows)
        parser.exit(1, f"Sales summary failed: {exc}\n")

    append_run_log("success", rows)
    print(f"Sales summary sent to {recipient}; {rows} sales rows processed.")


if __name__ == "__main__":
    main()