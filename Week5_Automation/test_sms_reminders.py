import csv
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import wk5_day5_project_automation_tool as reminders


class ContactFileTests(unittest.TestCase):
    def write_contacts(self, rows, header=("name", "phone")):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "contacts.csv"
        with path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(header)
            writer.writerows(rows)
        return path

    def test_reads_named_international_contacts(self):
        path = self.write_contacts(
            [("Amina", "+254712345678"), ("Brian", "+254722345678")]
        )

        self.assertEqual(
            reminders.load_contacts(path),
            [
                {"name": "Amina", "phone": "+254712345678"},
                {"name": "Brian", "phone": "+254722345678"},
            ],
        )

    def test_rejects_missing_columns_and_invalid_numbers(self):
        missing_phone = self.write_contacts([("Amina",)], header=("name",))
        invalid_phone = self.write_contacts([("Amina", "0712345678")])

        with self.assertRaisesRegex(ValueError, "missing required column"):
            reminders.load_contacts(missing_phone)
        with self.assertRaisesRegex(ValueError, "international format"):
            reminders.load_contacts(invalid_phone)

    def test_rejects_duplicate_numbers(self):
        path = self.write_contacts(
            [("Amina", "+254712345678"), ("Brian", "+254712345678")]
        )

        with self.assertRaisesRegex(ValueError, "duplicate phone number"):
            reminders.load_contacts(path)


class MessageFileTests(unittest.TestCase):
    def write_messages(self, content):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "messages.json"
        path.write_text(json.dumps(content), encoding="utf-8")
        return path

    def test_loads_both_message_bodies_from_json(self):
        path = self.write_messages(
            {
                "meeting": "Weekly reminder",
                "contribution": "Monthly reminder",
            }
        )

        self.assertEqual(
            reminders.load_messages(path),
            {
                "meeting": "Weekly reminder",
                "contribution": "Monthly reminder",
            },
        )

    def test_rejects_missing_or_empty_message(self):
        missing = self.write_messages({"meeting": "Weekly reminder"})
        empty = self.write_messages(
            {"meeting": "Weekly reminder", "contribution": " "}
        )

        with self.assertRaisesRegex(ValueError, "missing message"):
            reminders.load_messages(missing)
        with self.assertRaisesRegex(ValueError, "non-empty string"):
            reminders.load_messages(empty)

    def test_default_file_contains_both_reminder_texts(self):
        self.assertEqual(
            reminders.load_messages(),
            {
                "meeting": (
                    "dear member, will be having our weekly meeting tomorrow "
                    "saturday at 8:00pm, kindly keep time"
                ),
                "contribution": (
                    "dear member, kindly remember to pay your monthly contribution "
                    "to keep your membership active"
                ),
            },
        )


class SendingTests(unittest.TestCase):
    def setUp(self):
        self.contacts = [
            {"name": "Amina", "phone": "+254712345678"},
            {"name": "Brian", "phone": "+254722345678"},
        ]

    def test_no_arguments_prints_help_without_sending(self):
        output = StringIO()
        with redirect_stdout(output):
            reminders.main([])

        self.assertIn("usage:", output.getvalue())

    @patch.object(reminders, "load_credentials", return_value=("sandbox", "key", None))
    @patch.object(reminders, "load_contacts")
    @patch.object(reminders.africastalking, "initialize")
    @patch.object(reminders.africastalking, "SMS")
    def test_sends_selected_message_to_all_members(
        self, sms_service, _initialize, load_contacts, _credentials
    ):
        load_contacts.return_value = self.contacts
        sms_service.send.return_value = {
            "SMSMessageData": {
                "Recipients": [
                    {"status": "Success"},
                    {"status": "Success"},
                ]
            }
        }

        reminders.send_reminder("Weekly meeting message")

        sms_service.send.assert_called_once_with(
            "Weekly meeting message",
            ["+254712345678", "+254722345678"],
            sender_id=None,
        )

    @patch.object(reminders, "load_credentials", return_value=("sandbox", "key", None))
    @patch.object(reminders, "load_contacts")
    @patch.object(reminders.africastalking, "initialize")
    @patch.object(reminders.africastalking, "SMS")
    def test_reports_recipient_rejection(
        self, sms_service, _initialize, load_contacts, _credentials
    ):
        load_contacts.return_value = self.contacts
        sms_service.send.return_value = {
            "SMSMessageData": {
                "Recipients": [
                    {"status": "Success"},
                    {"status": "Invalid Number"},
                ]
            }
        }

        with self.assertRaisesRegex(reminders.SMSDeliveryError, "Brian"):
            reminders.send_reminder("Monthly contribution message")


if __name__ == "__main__":
    unittest.main()
