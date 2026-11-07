from functools import wraps

from flask import Flask, jsonify, request

app = Flask(__name__)

VALID_KEY = "Kamau-store-secrit-2024"

# Build a GET endpoint that returns all orders and a POST endpoint that accepts a new order:
orders = [
    {"id": 1, "customer": "Karaniya Trading", "product": "PVC Carpets"},
    {"id": 2, "customer": "Snoopy ltd", "product": "Wooden Floors"},
    {"id": 3, "customer": "Ebeneza enterprise", "product": "Tile Flooring"}
]


def require_api_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('x-api-key')
        if key != VALID_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)

    return decorated_function


# Routes
@app.route('/api/orders', methods=['GET'])
def get_orders():
    return jsonify(orders)


@app.route('/api/orders', methods=['POST'])
@require_api_key
def create_order():
    data = request.get_json()
    if not data or 'customer' not in data or 'product' not in data:
        return jsonify({"error": "Invalid input"}), 400

    new_order = {
        'id': len(orders) + 1,
        'customer': data['customer'],
        'product': data['product'],
        'qty': data.get('qty', 1),
        'status': 'pending'
    }
    orders.append(new_order)
    return jsonify(new_order), 201


# Add a GET single order:
@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = next((order for order in orders if order['id'] == order_id), None)
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order)


# status update endpoint:
@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@require_api_key
def update_order_status(order_id):
    order = next((order for order in orders if order['id'] == order_id), None)
    if order is None:
        return jsonify({"error": "Order not found"}), 404

    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Invalid input"}), 400

    order['status'] = data['status']
    return jsonify(order)


@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
@require_api_key
def delete_order(order_id):
    order = next((order for order in orders if order['id'] == order_id), None)
    if order is None:
        return jsonify({"error": "Order not found"}), 404

    orders.remove(order)
    return jsonify({"message": "Order deleted successfully"}), 200


if __name__ == '__main__':
    app.run(debug=True)