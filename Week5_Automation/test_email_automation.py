import unittest
from contextlib import redirect_stderr, redirect_stdout
from email import policy
from email.parser import Parser
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import email_automation


SCRIPT_DIR = Path(__file__).resolve().parent


class SalesEmailTests(unittest.TestCase):
    def setUp(self):
        self.summary = email_automation.calculate_summary(
            SCRIPT_DIR / "sales.csv", SCRIPT_DIR / "inventory.csv"
        )

    def test_sample_csv_calculates_all_four_metrics(self):
        self.assertEqual(self.summary.revenue, 5020)
        self.assertEqual(self.summary.transaction_count, 12)
        self.assertEqual(
            self.summary.top_selling_items, (("White sugar 1kg", 12),)
        )
        self.assertEqual(
            [name for name, _ in self.summary.low_stock_items],
            ["Cooking oil 1L", "Eggs tray", "Unga wa ngano 2kg", "White sugar 1kg"],
        )

    @patch.dict(
        "os.environ",
        {
            "GMAIL_ADDRESS": "shop@gmail.com",
            "GMAIL_APP_PASSWORD": "fake-app-password",
        },
        clear=True,
    )
    @patch("email_automation.smtplib.SMTP_SSL")
    def test_sender_transmits_html_with_all_metrics(self, smtp_ssl):
        message = email_automation.build_email(self.summary, "owner@example.com")

        email_automation.send_email(message)

        smtp_ssl.assert_called_once_with("smtp.gmail.com", 465, timeout=30)
        server = smtp_ssl.return_value.__enter__.return_value
        server.login.assert_called_once_with("shop@gmail.com", "fake-app-password")
        sent_message = Parser(policy=policy.default).parsestr(
            server.send_message.call_args.args[0].as_string()
        )
        html_part = next(
            part.get_content()
            for part in sent_message.walk()
            if part.get_content_type() == "text/html"
        )
        self.assertIn("KES 5,020.00", html_part)
        self.assertIn("Transactions</td><td>12", html_part)
        self.assertIn("White sugar 1kg (12 units)", html_part)
        self.assertIn("Restock required:", html_part)
        self.assertIn("Cooking oil 1L", html_part)

    @patch.dict(
        "os.environ",
        {
            "GMAIL_ADDRESS": "shop@gmail.com",
            "GMAIL_APP_PASSWORD": "fake-app-password",
        },
        clear=True,
    )
    @patch("email_automation.smtplib.SMTP_SSL")
    def test_authentication_disconnect_has_actionable_error(self, smtp_ssl):
        server = smtp_ssl.return_value.__enter__.return_value
        server.login.side_effect = email_automation.smtplib.SMTPServerDisconnected(
            "Connection unexpectedly closed"
        )
        message = email_automation.build_email(self.summary, "owner@example.com")

        with self.assertRaises(email_automation.EmailDeliveryError) as raised:
            email_automation.send_email(message)

        self.assertIn(
            "closed the connection during authentication", str(raised.exception)
        )
        server.send_message.assert_not_called()

    def test_check_smtp_authenticates_without_sending(self):
        output = StringIO()
        with patch.dict(
            "os.environ",
            {
                "GMAIL_ADDRESS": "shop@gmail.com",
                "GMAIL_APP_PASSWORD": "fake-app-password",
            },
            clear=True,
        ), \
            patch("email_automation.load_dotenv"), \
            patch("email_automation.smtplib.SMTP_SSL") as smtp_ssl, \
            patch("sys.argv", ["email_automation.py", "--check-smtp"]), \
            redirect_stdout(output):
            email_automation.main()

        server = smtp_ssl.return_value.__enter__.return_value
        server.login.assert_called_once_with("shop@gmail.com", "fake-app-password")
        server.send_message.assert_not_called()
        self.assertIn("authentication succeeded; no email was sent", output.getvalue())

    @patch(
        "email_automation.send_email",
        side_effect=email_automation.EmailDeliveryError("SMTP test failure"),
    )
    @patch("sys.argv", new=["email_automation.py"])
    @patch.dict("os.environ", {"REPORT_RECIPIENT": "owner@example.com"}, clear=True)
    def test_main_reports_delivery_failure_without_traceback(self, _send_email):
        error_output = StringIO()

        with redirect_stderr(error_output):
            with self.assertRaises(SystemExit) as raised:
                email_automation.main()

        self.assertEqual(raised.exception.code, 1)
        self.assertIn("Email delivery failed: SMTP test failure", error_output.getvalue())
        self.assertNotIn("Traceback", error_output.getvalue())


if __name__ == "__main__":
    unittest.main()
