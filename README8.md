# Public listings scraper: practice and HR-board adaptation

The practice script in `Week5_File_Automation/scrape_a_public_jobs_listing.py`
visits [Quotes to Scrape](https://quotes.toscrape.com/), follows its pagination,
and saves one row per listing to `HR.CSV` in the project root. The sample target
is not a jobs board: the CSV contains author, tags, tag count, author profile
URL, and source page URL. It deliberately omits the quote text; the purpose is
to demonstrate respectful page retrieval, HTML parsing, pagination, and CSV
cleanup without republishing the site's expressive text.

## Run

The script uses `requests` and `beautifulsoup4`, already included in the
project's Python environment. From the project root:

```powershell
python Week5_File_Automation\scrape_a_public_jobs_listing.py
```

It makes sequential requests with a one-second pause between pages, checks
HTTP errors, and reports a clear error if the expected listings are missing.
The output is UTF-8 with a byte-order mark for spreadsheet compatibility.

## Adapting it for a client-authorized jobs board

First agree with the client on the exact board, search filters, reporting
frequency, permitted fields, and where the report may be stored or shared.
Prefer an official API, export, or client-provided feed when available. If
HTML retrieval is authorized, inspect the board's structure and replace the
practice selectors with stable selectors for each job card and its fields.
Map the cards into a consistent schema such as job title, employer, location,
salary range and currency, skills, posting date, and source URL. Handle
pagination or client-approved filters, normalize salary values without
guessing missing amounts, deduplicate by a stable job ID or URL, and flag
missing or changed fields for review. Keep requests slow and bounded, log run
time and record counts, and validate a sample against the source before
delivering the weekly CSV/report.

Do not work around logins, paywalls, CAPTCHAs, access controls, or rate limits.
If access is withdrawn or the site returns a denial or throttling response,
stop and contact the client rather than retrying aggressively.

## Ethical and legal checks before launch

- Confirm in writing that the client is authorized to collect the selected
  public fields and that the board's terms, robots guidance, API terms, and
  license permit the planned collection and commercial reuse. Publicly visible
  does not automatically mean unrestricted.
- Check applicable Kenyan law, including the Data Protection Act, 2019, and
  any other jurisdictions implicated by the board, client, or data subjects.
  Establish the parties' data-protection roles and lawful basis where personal
  data is involved; collect only necessary information, set retention/access
  controls, and protect the report.
- Check copyright, database rights, contractual restrictions, and any limits
  on redistribution. Keep factual job details and source links; avoid copying
  full descriptions or other protected text unless the client has a clear
  right to use and share it.
- Assess harm and fairness: do not infer protected characteristics or use
  candidate/applicant data. Make salary comparisons transparent about
  currency, pay period, location, and missing values.
- Set a conservative request rate, identify the scraper honestly, avoid
  burdening the service, and provide a contact path if the site operator
  objects.

Get qualified Kenyan legal/privacy advice for the specific deployment; this
checklist is not a legal opinion.

## Suggested consultancy pricing

- **Setup fee: KSh 30,000 once** for one client-authorized board, field mapping,
  initial data-quality checks, and delivery setup.
- **Monthly retainer: KSh 20,000 per month** for a weekly run and cleaned CSV
  plus a concise trend summary, assuming one board and an agreed scope.

These are proposed starting prices, not a market quote. Confirm volumes,
number of boards, report depth, support expectations, and any paid data/API
costs before agreeing; price expanded scope separately.