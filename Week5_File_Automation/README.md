# Law Firm Document Sorter

This script organizes files in a target folder into subfolders by file
extension. It is intended for a law firm sorting contracts, evidence images,
court filings, correspondence, and other documents.

## Categories

| Folder | File extensions |
| --- | --- |
| `Contracts` | `.docx`, `.doc` |
| `Evidence` | `.jpg`, `.jpeg`, `.png` |
| `Filings` | `.pdf` |
| `Correspondence` | `.txt`, `.eml` |
| `Other` | Everything else, including files without an extension |

The sorter processes files directly inside the target folder and skips
subfolders. Extension matching is case-insensitive. If a destination filename
already exists, the moved file gets a numbered suffix rather than overwriting
the existing file.

## Run

Requires Python 3.6 or later and uses only the standard library. The script
moves files, so back up important documents and try it on a copy of the folder
first.

From the project root, run:

```powershell
python Week5_File_Automation/wk5_day1_file_automation_app.py --action sort-legal --source "C:\path\to\client-documents"
```

Replace the example path with the folder to sort. The script creates the
category folders as needed and appends one CSV-formatted row for each
successful move to `sort_log.txt` in the target folder. Each row contains the
local timestamp, original path, and destination path. The log is skipped on
later runs.

Sorting is based on file extensions, not document contents. For example, a
PDF email is categorized as a filing.

## Test

From this folder, run:

```powershell
python -m unittest -v test_sort_legal_documents
```

The test creates a temporary dummy folder containing 12 mixed files. It checks
the category assignments, log entries, collision handling, and rerun behavior.

## Estimated time savings and setup price

At 200 files per week and an estimated 15 seconds of manual sorting per file,
sorting by hand takes about 50 minutes. Allowing a few minutes for automated
sorting and review, the firm could save roughly **45 minutes per week**. Actual
savings depend on the firm's file volume and workflow.

I would charge **KSh 15,000 once** to configure, test, and set up the sorter
for one client. Ongoing support or additional workflow changes would be quoted
separately.
