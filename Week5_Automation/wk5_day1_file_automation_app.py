"""Week 5 file automation examples.

This script demonstrates common file operations in a safe, reusable way.
It avoids crashing when the target folders do not exist and supports a dry-run mode.

Examples:
    python wk5_day1_file_automation_app.py --action list --source "C:/path/to/folder"
    python wk5_day1_file_automation_app.py --action organize --source "C:/path/to/folder" --dry-run
    python wk5_day1_file_automation_app.py --action backup --reports-folder "C:/Sales Reports" --archive-folder "C:/Backups/Sales"
    python wk5_day1_file_automation_app.py --action rename --source "C:/delivery_photos" --order-number "ORD-2024-1157"
"""

import argparse
import csv
import os
import shutil
from datetime import datetime


DEFAULT_SOURCE = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "Mautuma")
DEFAULT_REPORTS_FOLDER = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "Sales Reports")
DEFAULT_ARCHIVE_FOLDER = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "Backups", "Sales")
DEFAULT_PHOTOS_FOLDER = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "delivery_photos")

CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif"],
    "Documents": [".pdf", ".docx", ".txt", ".xlsx"],
    "Scripts": [".py", ".js", ".html"],
    "Other": [],
}

LEGAL_CATEGORIES = {
    ".doc": "Contracts",
    ".docx": "Contracts",
    ".jpg": "Evidence",
    ".jpeg": "Evidence",
    ".png": "Evidence",
    ".pdf": "Filings",
    ".txt": "Correspondence",
    ".eml": "Correspondence",
}
SORT_LOG_FILENAME = "sort_log.txt"


def list_folder_contents(folder):
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        print(f"Folder does not exist: {folder}")
        return []

    files = sorted(os.listdir(folder))
    print(f"Files in folder: {folder}")
    for filename in files:
        print(f"- {filename}")
    return files


def organize_by_category(source, dry_run=False):
    source = os.path.abspath(source)
    if not os.path.isdir(source):
        print(f"Source folder does not exist: {source}")
        return 0

    moved = 0
    for filename in sorted(os.listdir(source)):
        full_path = os.path.join(source, filename)
        if os.path.isdir(full_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        dest_folder = "Other"
        for category, extensions in CATEGORIES.items():
            if ext in extensions:
                dest_folder = category
                break

        dest_dir = os.path.join(source, dest_folder)
        if dry_run:
            print(f"Would move: {filename} -> {dest_folder}/")
        else:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(full_path, os.path.join(dest_dir, filename))
            print(f"Moved {filename} -> {dest_folder}/")
        moved += 1

    if dry_run:
        print(f"Dry run complete. {moved} files would be organized.")
    else:
        print(f"Organized {moved} files in {source}")
    return moved


def sort_legal_documents(source):
    source = os.path.abspath(source)
    if not os.path.isdir(source):
        raise FileNotFoundError(f"Source folder does not exist: {source}")

    log_path = os.path.join(source, SORT_LOG_FILENAME)
    moved = 0
    for filename in sorted(os.listdir(source)):
        source_path = os.path.join(source, filename)
        if os.path.isdir(source_path) or filename == SORT_LOG_FILENAME:
            continue

        extension = os.path.splitext(filename)[1].lower()
        category = LEGAL_CATEGORIES.get(extension, "Other")
        destination_folder = os.path.join(source, category)
        os.makedirs(destination_folder, exist_ok=True)

        destination_path = os.path.join(destination_folder, filename)
        if os.path.exists(destination_path):
            name, extension = os.path.splitext(filename)
            suffix = 1
            while os.path.exists(destination_path):
                destination_path = os.path.join(
                    destination_folder, f"{name} ({suffix}){extension}"
                )
                suffix += 1

        shutil.move(source_path, destination_path)
        with open(log_path, "a", newline="", encoding="utf-8") as log_file:
            csv.writer(log_file).writerow(
                [
                    datetime.now().astimezone().isoformat(timespec="seconds"),
                    source_path,
                    destination_path,
                ]
            )
        print(f"Moved {source_path} -> {destination_path}")
        moved += 1

    print(f"Sorted {moved} files in {source}")
    return moved


def backup_reports(reports_folder, archive_folder, dry_run=False):
    reports_folder = os.path.abspath(reports_folder)
    archive_folder = os.path.abspath(archive_folder)

    if not os.path.isdir(reports_folder):
        print(f"Reports folder does not exist: {reports_folder}")
        return 0

    today = datetime.now().strftime("%Y-%m")
    archive_month = os.path.join(archive_folder, today)
    if not dry_run:
        os.makedirs(archive_month, exist_ok=True)

    moved = 0
    for filename in sorted(os.listdir(reports_folder)):
        if filename.lower().endswith(".xlsx"):
            source_path = os.path.join(reports_folder, filename)
            destination_path = os.path.join(archive_month, filename)
            if dry_run:
                print(f"Would back up: {filename} -> {archive_month}")
            else:
                shutil.copy(source_path, destination_path)
                print(f"Backed up {filename} -> {archive_month}")
            moved += 1

    if dry_run:
        print(f"Dry run complete. {moved} Excel files would be backed up to {archive_month}")
    else:
        print(f"Backed up {moved} reports to {archive_month}")
    return moved


def rename_files(folder, order_number, dry_run=False):
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        print(f"Folder does not exist: {folder}")
        return 0

    count = 0
    for index, filename in enumerate(sorted(os.listdir(folder)), start=1):
        full_path = os.path.join(folder, filename)
        if os.path.isdir(full_path):
            continue

        ext = os.path.splitext(filename)[1]
        new_name = f"{order_number}_photo_{index:02d}{ext}"
        new_path = os.path.join(folder, new_name)

        if dry_run:
            print(f"Would rename: {filename} -> {new_name}")
        else:
            os.rename(full_path, new_path)
            print(f"Renamed: {filename} -> {new_name}")
        count += 1

    if dry_run:
        print(f"Dry run complete. {count} files would be renamed.")
    else:
        print(f"Renamed {count} files in {folder}")
    return count


def file_exists_demo(target_file):
    if os.path.exists(target_file):
        print(f"File exists, proceeding with operations: {target_file}")
    else:
        print(f"File not found: {target_file}")


def create_and_copy_demo(source_file, destination_folder):
    source_file = os.path.abspath(source_file)
    destination_folder = os.path.abspath(destination_folder)

    if not os.path.exists(source_file):
        print(f"Source file not found: {source_file}")
        return

    os.makedirs(destination_folder, exist_ok=True)
    destination_path = os.path.join(destination_folder, os.path.basename(source_file))
    shutil.copy(source_file, destination_path)
    print(f"Copied {source_file} to {destination_path}")


def main():
    parser = argparse.ArgumentParser(description="File automation examples")
    parser.add_argument("--action", choices=["list", "organize", "sort-legal", "backup", "rename", "exists", "copy"], default="list")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Folder to work with")
    parser.add_argument("--reports-folder", default=DEFAULT_REPORTS_FOLDER, help="Folder containing report files")
    parser.add_argument("--archive-folder", default=DEFAULT_ARCHIVE_FOLDER, help="Destination folder for archived files")
    parser.add_argument("--order-number", default="ORD-2024-1157", help="Order code used when renaming files")
    parser.add_argument("--target-file", default="3rd quarter physical meeting.docx", help="File to check for existence")
    parser.add_argument("--destination-folder", default=os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "archive", "2026"), help="Destination folder for copy example")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes instead of making them")
    args = parser.parse_args()

    if args.action == "list":
        list_folder_contents(args.source)
    elif args.action == "organize":
        organize_by_category(args.source, dry_run=args.dry_run)
    elif args.action == "sort-legal":
        sort_legal_documents(args.source)
    elif args.action == "backup":
        backup_reports(args.reports_folder, args.archive_folder, dry_run=args.dry_run)
    elif args.action == "rename":
        rename_files(args.source, args.order_number, dry_run=args.dry_run)
    elif args.action == "exists":
        file_exists_demo(args.target_file)
    elif args.action == "copy":
        create_and_copy_demo(args.target_file, args.destination_folder)


if __name__ == "__main__":
    main()
