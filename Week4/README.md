# Daily Egg Production API

A small Flask REST API for recording daily egg counts by poultry shed. The
current version stores records in an in-memory list, so all records are lost
when the server stops or restarts. Do not use this version as the only copy of
production records.

## Requirements and setup

- Python 3.10 or later

From the `Week4` folder, install Flask and start the API:

```powershell
python -m pip install -r requirements.txt
python wk4-day2.1-building-a-REST-API.py
```

The server listens on `http://127.0.0.1:5000`.

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

## Indicative service pricing

- **Build and first deployment: KSh 20,000 once.** This covers this small API,
  basic request validation, and deployment setup.
- **Keep it running: KSh 2,500 per month.** This covers basic uptime checks and
  routine maintenance for a low-traffic deployment. Any paid hosting, domain,
  or usage charges are billed separately.

These are indicative prices, not a binding quote. This in-memory version loses
its data on restart and has no authentication or backups. Before relying on it
for farm records, quote a follow-up upgrade for persistent database storage,
backups, and access control.