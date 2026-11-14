# Hardware Credit Application

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

customer_balances = {
    "Amina Wanjiku": 12500,
    "Brian Kiptoo": 8300,
    "Chebet Jepkosgei": 15750,
    "David Mwangi": 4200,
    "Eunice Naliaka": 9900,
}


@app.route("/")
def home():
    return render_template("hardware_credit.html")


@app.route("/api/balance")
def get_balance():
    customer = request.args.get("customer", "").strip()
    if not customer:
        return jsonify({"error": "Provide a customer name"}), 400

    matching_customer = next(
        (name for name in customer_balances if name.casefold() == customer.casefold()),
        None,
    )
    if matching_customer is None:
        return jsonify({"error": "Customer not found", "customer": customer}), 404

    return jsonify(
        {
            "customer": matching_customer,
            "balance": customer_balances[matching_customer],
            "currency": "KES",
        }
    )


if __name__ == "__main__":
    app.run(debug=False)
