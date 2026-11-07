from datetime import date
from typing import Any

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

egg_records: list[dict[str, Any]] = []


@app.route("/")
def egg_tracker():
    return render_template("egg_tracker.html")


@app.route("/api/eggs", methods=["POST"])
def create_egg_record():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    shed = data.get("shed")
    record_date = data.get("date")
    count = data.get("count")

    if not isinstance(shed, str) or not shed.strip():
        return jsonify({"error": "'shed' must be a non-empty string"}), 400
    if not isinstance(record_date, str):
        return jsonify({"error": "'date' must be a valid YYYY-MM-DD date"}), 400
    try:
        parsed_date = date.fromisoformat(record_date)
    except ValueError:
        return jsonify({"error": "'date' must be a valid YYYY-MM-DD date"}), 400
    if parsed_date.isoformat() != record_date:
        return jsonify({"error": "'date' must use YYYY-MM-DD format"}), 400
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return jsonify({"error": "'count' must be a non-negative integer"}), 400

    record = {
        "id": len(egg_records) + 1,
        "shed": shed.strip(),
        "date": record_date,
        "count": count,
    }
    egg_records.append(record)
    return jsonify(record), 201


@app.route("/api/eggs", methods=["GET"])
def get_egg_records():
    records = sorted(egg_records, key=lambda record: (record["date"], record["id"]))
    running_total = 0
    records_with_totals = []

    for record in records:
        running_total += record["count"]
        records_with_totals.append({**record, "running_total": running_total})

    return jsonify({"records": records_with_totals, "total_eggs": running_total})


if __name__ == "__main__":
    app.run(debug=False)