''' SMS AUTOMATION '''

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

import africastalking
from africastalking.Service import AfricasTalkingException
import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
CONTACTS_FILE = PROJECT_DIR / "contacts.csv"
ENV_FILE = PROJECT_DIR / ".env"
MESSAGES_FILE = Path(__file__).resolve().parent / "sms_messages.json"
PHONE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


class SMSDeliveryError(Exception):
    """An Africa's Talking SMS delivery error."""


def load_messages(path=MESSAGES_FILE):
    with path.open("r", encoding="utf-8") as messages_file:
        messages = json.load(messages_file)

    required_messages = {"meeting", "contribution"}
    if not isinstance(messages, dict):
        raise ValueError(f"{path} must contain a JSON object.")

    missing_messages = required_messages.difference(messages)
    if missing_messages:
        raise ValueError(
            f"{path} is missing message(s): {', '.join(sorted(missing_messages))}."
        )

    cleaned_messages = {}
    for key in required_messages:
        message = messages[key]
        if not isinstance(message, str) or not message.strip():
            raise ValueError(f"{path}: '{key}' message must be a non-empty string.")
        cleaned_messages[key] = message.strip()
    return cleaned_messages


def load_contacts(path=CONTACTS_FILE):
    if not path.is_file():
        raise FileNotFoundError(f"Contacts file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"{path} is empty or has no CSV header.")

        missing_columns = {"name", "phone"}.difference(reader.fieldnames)
        if missing_columns:
            raise ValueError(
                f"{path} is missing required column(s): "
                f"{', '.join(sorted(missing_columns))}."
            )

        contacts = []
        seen_numbers = set()
        for row_number, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            phone = (row.get("phone") or "").strip()
            if not name and not phone:
                continue
            if not name or not phone:
                raise ValueError(
                    f"Contacts CSV row {row_number}: name and phone are required."
                )
            if not PHONE_PATTERN.fullmatch(phone):
                raise ValueError(
                    f"Contacts CSV row {row_number}: phone must use international "
                    "format, for example +254712345678."
                )
            if phone in seen_numbers:
                raise ValueError(
                    f"Contacts CSV row {row_number}: duplicate phone number."
                )
            seen_numbers.add(phone)
            contacts.append({"name": name, "phone": phone})

    if not contacts:
        raise ValueError(f"No members found in {path}.")
    return contacts


def load_credentials():
    load_dotenv(ENV_FILE)
    username = os.getenv("SMS_USERNAME", "").strip()
    api_key = os.getenv("SMS_API_KEY", "").strip()
    sender_id = os.getenv("SMS_SENDER_ID", "").strip() or None
    missing = [
        key
        for key, value in (("SMS_USERNAME", username), ("SMS_API_KEY", api_key))
        if not value
    ]
    if missing:
        raise ValueError("Missing .env setting(s): " + ", ".join(missing))
    return username, api_key, sender_id


def send_reminder(message):
    contacts = load_contacts()
    username, api_key, sender_id = load_credentials()
    africastalking.initialize(username, api_key)

    try:
        response = africastalking.SMS.send(
            message,
            [contact["phone"] for contact in contacts],
            sender_id=sender_id,
        )
    except (AfricasTalkingException, requests.RequestException) as exc:
        raise SMSDeliveryError(f"provider request failed: {exc}") from exc

    sms_data = response.get("SMSMessageData") if isinstance(response, dict) else None
    recipient_results = (
        sms_data.get("Recipients") if isinstance(sms_data, dict) else None
    )
    if (
        not isinstance(recipient_results, list)
        or len(recipient_results) != len(contacts)
    ):
        raise SMSDeliveryError("provider returned an unexpected recipient response.")

    failures = []
    for contact, result in zip(contacts, recipient_results):
        status = result.get("status") if isinstance(result, dict) else None
        if not isinstance(status, str) or status.casefold() != "success":
            status = status or "unknown status"
            failures.append(f"{contact['name']}: {status}")
    if failures:
        raise SMSDeliveryError(
            "provider did not accept SMS for: " + "; ".join(failures)
        )

    print(f"SMS accepted for {len(contacts)} member(s).")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Send scheduled chama reminders using Africa's Talking."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--meeting", action="store_true", help="Send the weekly reminder."
    )
    mode.add_argument(
        "--contribution", action="store_true", help="Send the monthly reminder."
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Validate contacts and credentials without sending SMS.",
    )
    args = parser.parse_args(argv)
    if not (args.meeting or args.contribution or args.check):
        parser.print_help()
        return

    try:
        if args.check:
            contacts = load_contacts()
            load_messages()
            load_credentials()
            print(
                f"Configuration is valid; {len(contacts)} member(s) found. "
                "No SMS sent."
            )
            return
        messages = load_messages()
        message_key = "meeting" if args.meeting else "contribution"
        send_reminder(messages[message_key])
    except (OSError, ValueError, SMSDeliveryError) as exc:
        print(f"SMS reminder failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
    