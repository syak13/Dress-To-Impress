from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# ─── ATOMIC SERVICE URLS ──────────────────────────────────────────────────────
INVENTORY_URL    = os.environ.get('INVENTORY_URL',    'http://localhost:5001')
CUSTOMER_URL     = os.environ.get('CUSTOMER_URL',     'http://localhost:5000')
RENTAL_URL       = os.environ.get('RENTAL_URL',       'http://localhost:5004')
INVOICE_URL      = os.environ.get('INVOICE_URL',      'http://localhost:5005')
NOTIFICATION_URL = os.environ.get('NOTIFICATION_URL', 'http://localhost:5003')


# ─── UC3: PLACE A RENTAL ORDER ───────────────────────────────────────────────
#
# Flow:
#   1. POST  place rental order      → received from UI
#   2. POST  create rental record    → Rental Service
#   3. GET   rental confirmation     → Rental Service  (returns rental_id)
#   4. PUT   update inventory        → Inventory Service (is_available: False)
#   5. GET   dress price             → Inventory Service (returns dressPrice)
#   6. POST  create rental invoice   → Invoice Service  (amount = dressPrice)
#   7. GET   customer information    → Customer Service
#   8. POST  send confirmation       → Notification Service
#   9. Return rental + payment info  → UI

@app.route("/rental-order", methods=['POST'])
def place_rental_order():
    """
    Expected JSON:
    {
        "customer_id": 1,
        "dress_id": 201,
        "start_date": "2026-06-01",
        "end_date": "2026-06-05"
    }
    """
    data = request.get_json()

    for field in ['customer_id', 'dress_id', 'start_date', 'end_date']:
        if field not in data:
            return jsonify({
                "code": 400,
                "message": f"Missing required field: {field}"
            }), 400

    customer_id = data['customer_id']
    dress_id    = data['dress_id']
    start_date  = data['start_date']
    end_date    = data['end_date']

    # ── Step 2: Create rental record via Rental Service ───────────────────────
    try:
        rental_response = requests.post(
            f"{RENTAL_URL}/rental",
            json={
                "customer_id": customer_id,
                "dress_id":    dress_id,
                "start_date":  start_date,
                "end_date":    end_date,
                "status":      "PENDING"
            }
        )
    except Exception as e:
        return jsonify({"code": 500, "message": f"Rental service error: {str(e)}"}), 500

    if rental_response.status_code != 201:
        return jsonify({
            "code": 500,
            "message": f"Failed to create rental record. Status: {rental_response.status_code}, Response: {rental_response.text}"
        }), 500
    
    rental_data = rental_response.json()

    # ── Step 3: Get rental_id back ────────────────────────────────────────────
    rental    = rental_data["data"]
    rental_id = rental["rental_id"]

    # ── Step 4+5: Update inventory availability + get dress price ─────────────
    try:
        inventory_response = requests.put(
            f"{INVENTORY_URL}/inventory/{dress_id}",
            json={"is_available": False}
        )
        inventory_data = inventory_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Inventory service error: {str(e)}"}), 500

    if inventory_response.status_code != 200:
        return jsonify({
            "code": 500,
            "message": f"Failed to update inventory for dress {dress_id}."
        }), 500

    # Step 5: dress price comes from the inventory response
    dress_price = inventory_data["data"]["price"]
    dress_size  = inventory_data["data"]["size"]

    # ── Step 6: Create rental invoice via Invoice Service ─────────────────────
    try:
        invoice_response = requests.post(
            f"{INVOICE_URL}/invoice",
            json={
                "rental_id": rental_id,
                "amount":    dress_price,
                "type":      "RENTAL"
            }
        )
        invoice_data = invoice_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Invoice service error: {str(e)}"}), 500

    if invoice_response.status_code != 201:
        return jsonify({
            "code": 500,
            "message": "Failed to create invoice."
        }), 500

    invoice = invoice_data["data"]
    client_secret = invoice.get("client_secret")

    # ── Step 7: Get customer information from Customer Service ────────────────
    try:
        customer_response = requests.get(f"{CUSTOMER_URL}/customer/{customer_id}")
        customer_data = customer_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Customer service error: {str(e)}"}), 500

    if customer_response.status_code != 200:
        return jsonify({
            "code": 404,
            "message": f"Customer {customer_id} not found."
        }), 404

    customer = customer_data["data"]

    # ── Step 8: Send confirmation via Notification Service (AMQP) ─────────────
    try:
        requests.post(
            f"{NOTIFICATION_URL}/notifications",
            json={
                "customer_id": customer_id,
                "phone":       customer["phone"],
                "message": (
                    f"Hi {customer['name']}, your rental order has been confirmed! "
                    f"Dress ID: {dress_id} (Size: {dress_size}), "
                    f"Rental period: {start_date} to {end_date}. "
                    f"Amount charged: ${dress_price}. "
                    f"Rental ID: {rental_id}, Invoice ID: {invoice['invoice_id']}."
                )
            }
        )
    except Exception as e:
        # notification failure should not block the rental confirmation
        print(f"[WARNING] Notification service error: {str(e)}")

    # ── Step 9: Return rental order confirmation to UI ────────────────────────
    return jsonify({
        "code": 201,
        "data": {
            "rental_id":     rental_id,
            "invoice_id":    invoice["invoice_id"],
            "customer_id":   customer_id,
            "customer_name": customer["name"],
            "dress_id":      dress_id,
            "dress_size":    dress_size,
            "start_date":    start_date,
            "end_date":      end_date,
            "amount":        dress_price,
            "status":        rental["status"],
            "client_secret": client_secret
        }
    }), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5011, debug=False)
