"""Email a daily sales summary from CSV files using Gmail SMTP."""

import argparse
import csv
import html
import os
import smtplib
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
NAIROBI_TZ = timezone(timedelta(hours=3), name="Africa/Nairobi")


class EmailDeliveryError(Exception):
    """A safe, actionable error raised when SMTP delivery fails."""


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


def _read_csv(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"{path} is empty or has no CSV header.")
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"{path} is missing required column(s): {missing}.")
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
        sales_csv, {"transaction_id", "item_name", "quantity_sold", "price_kes"}
    )
    inventory_rows = _read_csv(
        inventory_csv, {"item_name", "stock_remaining", "restock_level"}
    )
    if not sales_rows:
        raise ValueError(f"{sales_csv} contains no sales.")

    total_revenue = Decimal("0")
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
            raise ValueError(f"Sales CSV row {row_number}: quantity_sold must be positive.")
        try:
            price = Decimal(row["price_kes"])
        except (InvalidOperation, TypeError) as exc:
            raise ValueError(
                f"Sales CSV row {row_number}: price_kes must be a valid amount."
            ) from exc
        if not price.is_finite() or price < 0:
            raise ValueError(
                f"Sales CSV row {row_number}: price_kes must be a finite, nonnegative amount."
            )

        total_revenue += quantity * price
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

    missing_inventory = sorted(set(item_quantities).difference(inventory))
    if missing_inventory:
        raise ValueError(
            "Inventory CSV has no stock level for: " + ", ".join(missing_inventory)
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
            (name, stock)
            for name, stock in inventory.items()
            if stock.stock_remaining < stock.restock_level
        )
    )
    return SalesSummary(
        revenue=total_revenue,
        transaction_count=len(transaction_ids),
        top_selling_items=top_items,
        low_stock_items=low_stock,
    )


def build_email(summary: SalesSummary, recipient: str) -> EmailMessage:
    if not recipient.strip():
        raise ValueError("REPORT_RECIPIENT must be set to an email address.")

    report_date = datetime.now(NAIROBI_TZ).strftime("%A, %d %B %Y")
    top_items_text = ", ".join(
        f"{name} ({quantity} units)" for name, quantity in summary.top_selling_items
    )
    if summary.low_stock_items:
        low_stock_text = ", ".join(
            f"{name} ({stock.stock_remaining} left; restock at {stock.restock_level})"
            for name, stock in summary.low_stock_items
        )
        stock_status = f"Restock required: {low_stock_text}"
    else:
        stock_status = "All items are at or above their restock levels."

    html_body = (
        '<html><body style="font-family:Arial,sans-serif;color:#243447;">'
        '<h2 style="color:#176b57;">Daily Sales Summary</h2>'
        f"<p>{html.escape(report_date)} (Nairobi time)</p>"
        '<table style="border-collapse:collapse;width:100%;" '
        'cellpadding="10" border="1">'
        "<tr><th align=\"left\">Metric</th><th align=\"left\">Today</th></tr>"
        f"<tr><td>Total revenue</td><td>KES {summary.revenue:,.2f}</td></tr>"
        f"<tr><td>Transactions</td><td>{summary.transaction_count}</td></tr>"
        f"<tr><td>Top-selling item</td><td>{html.escape(top_items_text)}</td></tr>"
        f"<tr><td>Restock alert</td><td>{html.escape(stock_status)}</td></tr>"
        "</table></body></html>"
    )
    text_body = (
        f"Daily Sales Summary - {report_date} (Nairobi time)\n"
        f"Total revenue: KES {summary.revenue:,.2f}\n"
        f"Transactions: {summary.transaction_count}\n"
        f"Top-selling item: {top_items_text}\n"
        f"Restock alert: {stock_status}\n"
    )

    message = EmailMessage()
    message["Subject"] = f"Daily Sales Summary - {report_date}"
    message["To"] = recipient
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    return message


def _gmail_credentials() -> tuple[str, str]:
    gmail_address = os.getenv("GMAIL_ADDRESS", "").strip()
    app_password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    missing = [
        name
        for name, value in (
            ("GMAIL_ADDRESS", gmail_address),
            ("GMAIL_APP_PASSWORD", app_password),
        )
        if not value
    ]
    if missing:
        raise ValueError("Missing .env setting(s): " + ", ".join(missing))
    return gmail_address, app_password


def _run_smtp(message: Optional[EmailMessage] = None) -> None:
    gmail_address, app_password = _gmail_credentials()
    if message is not None:
        message["From"] = gmail_address
    stage = "connecting to Gmail"
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            stage = "authenticating with Gmail"
            server.login(gmail_address, app_password)
            if message is not None:
                stage = "submitting the email"
                server.send_message(message)
    except smtplib.SMTPAuthenticationError as exc:
        raise EmailDeliveryError(
            "Gmail rejected authentication. Check GMAIL_ADDRESS and use a valid "
            "Gmail app password with 2-Step Verification enabled."
        ) from exc
    except smtplib.SMTPRecipientsRefused as exc:
        raise EmailDeliveryError(
            "Gmail refused the recipient. Check REPORT_RECIPIENT."
        ) from exc
    except smtplib.SMTPSenderRefused as exc:
        raise EmailDeliveryError(
            "Gmail refused the sender. Check GMAIL_ADDRESS."
        ) from exc
    except smtplib.SMTPServerDisconnected as exc:
        if stage == "submitting the email":
            detail = (
                "The connection dropped while submitting the email; delivery "
                "status is uncertain. Check the recipient's inbox before retrying."
            )
        elif stage == "authenticating with Gmail":
            detail = (
                "Gmail closed the connection during authentication. Verify "
                "GMAIL_ADDRESS, generate a fresh Google app password, and check "
                "that 2-Step Verification and your account policy allow app passwords."
            )
        else:
            detail = "Gmail disconnected while establishing the connection."
        raise EmailDeliveryError(detail) from exc
    except smtplib.SMTPConnectError as exc:
        raise EmailDeliveryError(
            f"Could not connect to Gmail SMTP: {exc}"
        ) from exc
    except TimeoutError as exc:
        raise EmailDeliveryError(
            f"Timed out while {stage}; check the internet connection and retry."
        ) from exc
    except OSError as exc:
        raise EmailDeliveryError(
            f"Network error while {stage}: {exc}"
        ) from exc
    except smtplib.SMTPException as exc:
        raise EmailDeliveryError(
            f"Gmail SMTP error while {stage}: {exc}"
        ) from exc


def send_email(message: EmailMessage) -> None:
    _run_smtp(message)


def check_smtp_authentication() -> None:
    _run_smtp()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a daily sales summary from sales and inventory CSV files."
    )
    parser.add_argument(
        "--sales-csv", type=Path, default=SCRIPT_DIR / "sales.csv"
    )
    parser.add_argument(
        "--inventory-csv", type=Path, default=SCRIPT_DIR / "inventory.csv"
    )
    run_mode = parser.add_mutually_exclusive_group()
    run_mode.add_argument(
        "--dry-run",
        action="store_true",
        help="print the email preview without loading credentials or sending email",
    )
    run_mode.add_argument(
        "--check-smtp",
        action="store_true",
        help="test Gmail authentication without sending an email",
    )
    args = parser.parse_args()

    try:
        if args.check_smtp:
            load_dotenv(PROJECT_DIR / ".env")
            check_smtp_authentication()
            print("Gmail SMTP authentication succeeded; no email was sent.")
            return

        summary = calculate_summary(args.sales_csv, args.inventory_csv)
        recipient = os.getenv("REPORT_RECIPIENT", "").strip()
        if args.dry_run:
            recipient = recipient or "(recipient configured in .env)"
        else:
            load_dotenv(PROJECT_DIR / ".env")
            recipient = os.getenv("REPORT_RECIPIENT", "").strip()

        message = build_email(summary, recipient)
        if args.dry_run:
            print(message)
            return

        send_email(message)
    except EmailDeliveryError as exc:
        parser.exit(1, f"Email delivery failed: {exc}\n")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Sales summary sent to {recipient}.")


if __name__ == "__main__":
    main()