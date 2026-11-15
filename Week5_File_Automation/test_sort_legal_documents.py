import csv
import os
import tempfile
import unittest

from wk5_day1_file_automation_app import SORT_LOG_FILENAME, sort_legal_documents


class SortLegalDocumentsTests(unittest.TestCase):
    def test_sorts_mixed_files_and_logs_each_move_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = os.path.join(temporary_directory, "dummy-client-folder")
            os.makedirs(source)
            filenames = [
                "contract.docx",
                "agreement.doc",
                "photo.jpg",
                "scan.jpeg",
                "evidence.png",
                "scan001.pdf",
                "client.txt",
                "message.eml",
                "spreadsheet.xlsx",
                "archive.zip",
                "animation.gif",
                "unknown",
            ]
            for filename in filenames:
                with open(os.path.join(source, filename), "w", encoding="utf-8") as file:
                    file.write("dummy content")

            contracts = os.path.join(source, "Contracts")
            os.makedirs(contracts)
            with open(
                os.path.join(contracts, "contract.docx"),
                "w",
                encoding="utf-8",
            ) as file:
                file.write("keep existing file")

            self.assertEqual(sort_legal_documents(source), len(filenames))

            expected_categories = {
                "contract.docx": ("Contracts", "contract (1).docx"),
                "agreement.doc": ("Contracts", "agreement.doc"),
                "photo.jpg": ("Evidence", "photo.jpg"),
                "scan.jpeg": ("Evidence", "scan.jpeg"),
                "evidence.png": ("Evidence", "evidence.png"),
                "scan001.pdf": ("Filings", "scan001.pdf"),
                "client.txt": ("Correspondence", "client.txt"),
                "message.eml": ("Correspondence", "message.eml"),
                "spreadsheet.xlsx": ("Other", "spreadsheet.xlsx"),
                "archive.zip": ("Other", "archive.zip"),
                "animation.gif": ("Other", "animation.gif"),
                "unknown": ("Other", "unknown"),
            }
            log_path = os.path.join(source, SORT_LOG_FILENAME)
            with open(log_path, newline="", encoding="utf-8") as log_file:
                entries = list(csv.reader(log_file))

            self.assertEqual(len(entries), len(filenames))
            for timestamp, original_path, destination_path in entries:
                original_name = os.path.basename(original_path)
                category, destination_name = expected_categories[original_name]
                self.assertTrue(timestamp)
                self.assertEqual(original_path, os.path.join(source, original_name))
                self.assertEqual(
                    destination_path,
                    os.path.join(source, category, destination_name),
                )
                self.assertTrue(os.path.isfile(destination_path))

            self.assertEqual(sort_legal_documents(source), 0)
            self.assertTrue(os.path.isfile(log_path))
            with open(log_path, newline="", encoding="utf-8") as log_file:
                self.assertEqual(len(list(csv.reader(log_file))), len(filenames))


if __name__ == "__main__":
    unittest.main()
