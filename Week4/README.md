# Daily Egg Production Tracker

A small Flask app for recording daily egg counts by poultry shed. Open its
browser page to submit a collection and see all records and running totals
update without reloading. The app stores records in memory, so all records are
lost when the server stops or restarts. Do not use this version as the only
copy of production records.

## Requirements and setup

- Python 3.10 or later

From the `Week4` folder, install Flask and start the API:

```powershell
python -m pip install -r requirements.txt
python wk4-day2.1-building-a-REST-API.py
```

Open `http://127.0.0.1:5000` in a browser. Enter the shed name, collection
date, and non-negative whole-number egg count, then select **Submit**. The
records table and overall total refresh automatically. The page uses the
`POST /api/eggs` and `GET /api/eggs` endpoints described below.

## API

### `POST /api/eggs`

Submit a JSON object with a non-empty shed name, an ISO date, and a
non-negative integer egg count:

```json
{
  "shed": "Shed A",
  "date": "2026-11-02",
  "count": 120
}
```

A successful request returns `201 Created` and the saved record, including its
ID. Invalid JSON or fields return `400 Bad Request`.

### `GET /api/eggs`

Returns all records sorted by date (and then ID for entries on the same date).
Each record includes a `running_total`, which accumulates counts in that order.
The response's `total_eggs` is the overall count across all records.

## Test with curl

With the server running, use `curl.exe` in PowerShell. Writing each JSON body
to a temporary file avoids PowerShell's native-command quote handling:

```powershell
$payloadPath = Join-Path $env:TEMP "egg-record.json"
function Send-EggRecord($body) {
  [IO.File]::WriteAllText($payloadPath, $body, (New-Object System.Text.UTF8Encoding -ArgumentList $false))
  curl.exe -X POST http://127.0.0.1:5000/api/eggs -H "Content-Type: application/json" --data-binary "@$payloadPath"
}
Send-EggRecord '{"shed":"Shed A","date":"2026-11-02","count":120}'
Send-EggRecord '{"shed":"Shed B","date":"2026-11-02","count":95}'
Send-EggRecord '{"shed":"Shed A","date":"2026-11-03","count":125}'
Send-EggRecord '{"shed":"Shed B","date":"2026-11-03","count":100}'
Remove-Item -LiteralPath $payloadPath
curl.exe http://127.0.0.1:5000/api/eggs
```

The four sample records should produce `total_eggs: 440` and cumulative
`running_total` values of 120, 215, 340, and 440. These sample dates are
illustrative; use the actual collection dates for farm records.

## Potential small-business customers in Kenya

The tracker may suit small poultry farms and layer-egg producers that record
collections by shed, egg aggregators or collection centres that combine daily
deliveries, and small egg retailers or groceries that want a simple daily
intake record. The current version is most useful as a low-cost prototype or
for trying the workflow; in-memory records are not suitable as a permanent
business record.

## Indicative service pricing

- **Small farm or retailer: KSh 20,000 once** for setup and first deployment,
  then **KSh 2,500 per month** for basic uptime checks and routine maintenance.
- **Aggregator or collection centre: from KSh 20,000 once** for a trial of the
  same basic tracker; multi-user access, persistent storage, backups, and
  reporting should be scoped and priced separately before production use.

These are indicative starting prices, not a binding quote. Any paid hosting,
domain, or usage charges are billed separately.

This in-memory version loses its data on restart and has no authentication or
backups. Before relying on it for farm records, quote a follow-up upgrade for
persistent database storage, backups, and access control.
