from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ─── ATOMIC SERVICE URLS ──────────────────────────────────────────────────────
# In Docker, these use container names defined in docker-compose.yml
# Locally, use localhost with the respective ports

INVENTORY_URL     = os.environ.get('INVENTORY_URL',     'http://localhost:5001')
BOOKING_URL       = os.environ.get('BOOKING_URL',       'http://localhost:5002')
CUSTOMER_URL      = os.environ.get('CUSTOMER_URL',      'http://localhost:5000')
NOTIFICATION_URL  = os.environ.get('NOTIFICATION_URL',  'http://localhost:5003')


# ─── UC2: SCHEDULE A DRESS FITTING APPOINTMENT ───────────────────────────────
#
# Flow:
#   1. GET  available dresses        → Inventory Service
#   2. GET  dress information        → Inventory Service
#   3. GET  customer information     → Customer Service
#   4. POST book timeslot            → Booking Service
#   5. POST send confirmation        → Notification Service
#   6. Return booking confirmation   → UI


# Step 1 — Get all available dresses (for UI to display fitting slots)
@app.route("/fitting/available", methods=['GET'])
def get_available_dresses():
    try:
        response = requests.get(f"{INVENTORY_URL}/inventory/available")
        data = response.json()
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Failed to reach inventory service: {str(e)}"
        }), 500

    if response.status_code != 200:
        return jsonify({
            "code": response.status_code,
            "message": data.get("message", "Could not retrieve available dresses.")
        }), response.status_code

    return jsonify({
        "code": 200,
        "data": data["data"]
    })


# Main UC2 endpoint — schedule a fitting appointment
@app.route("/fitting/schedule", methods=['POST'])
def schedule_fitting():
    """
    Expected JSON:
    {
        "customer_id": 1,
        "dress_id": 101,
        "slot_datetime": "2026-04-16 10:00:00"
    }
    """
    data = request.get_json()

    for field in ['customer_id', 'dress_id', 'slot_datetime']:
        if field not in data:
            return jsonify({
                "code": 400,
                "message": f"Missing required field: {field}"
            }), 400

    customer_id   = data['customer_id']
    dress_id      = data['dress_id']
    slot_datetime = data['slot_datetime']

    # ── Step 2: Get dress information from Inventory Service ──────────────────
    try:
        inventory_response = requests.get(f"{INVENTORY_URL}/inventory/{dress_id}")
        inventory_data = inventory_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Inventory service error: {str(e)}"}), 500

    if inventory_response.status_code != 200:
        return jsonify({
            "code": 404,
            "message": f"Dress {dress_id} not found in inventory."
        }), 404

    dress = inventory_data["data"]

    # check dress is available before booking
    if not dress["is_available"]:
        return jsonify({
            "code": 400,
            "message": f"Dress {dress_id} is not available for fitting."
        }), 400

    # ── Step 3: Get customer information from Customer Service ────────────────
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

    # ── Step 4: Book the timeslot via Booking Service ─────────────────────────
    try:
        booking_response = requests.post(
            f"{BOOKING_URL}/bookings",
            json={
                "customer_id": customer_id,
                "dress_id": dress_id,
                "slot_datetime": slot_datetime
                # calendar_event_id: add when Google Calendar is integrated
            }
        )
        booking_data = booking_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Booking service error: {str(e)}"}), 500

    if booking_response.status_code != 201:
        return jsonify({
            "code": 500,
            "message": "Failed to create booking."
        }), 500

    booking = booking_data["data"]

    # ── Step 5: Send confirmation via Notification Service (AMQP/HTTP) ────────
    try:
        notification_response = requests.post(
            f"{NOTIFICATION_URL}/notifications",
            json={
                "customer_id": customer_id,
                "email": customer["email"],
                "message": (
                    f"Hi {customer['name']}, your fitting appointment for dress "
                    f"(ID: {dress_id}, Size: {dress['size']}) is confirmed on "
                    f"{slot_datetime}. Booking ID: {booking['booking_id']}."
                )
            }
        )
    except Exception as e:
        # notification failure should not block the booking confirmation
        print(f"[WARNING] Notification service error: {str(e)}")

    # ── Step 6: Return booking confirmation to UI ─────────────────────────────
    return jsonify({
        "code": 201,
        "data": {
            "booking_id":    booking["booking_id"],
            "slot_datetime": booking["slot_datetime"],
            "dress_id":      dress_id,
            "dress_size":    dress["size"],
            "customer_id":   customer_id,
            "customer_name": customer["name"],
            "customer_email": customer["email"]
        }
    }), 201


# ─── CANCEL A FITTING APPOINTMENT ────────────────────────────────────────────

@app.route("/fitting/cancel/<int:booking_id>", methods=['PUT'])
def cancel_fitting(booking_id):
    """
    Cancels a confirmed fitting appointment.
    Notifies the customer via notification service.
    """

    # cancel booking
    try:
        booking_response = requests.put(
            f"{BOOKING_URL}/bookings/{booking_id}/cancel"
        )
        booking_data = booking_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Booking service error: {str(e)}"}), 500

    if booking_response.status_code != 200:
        return jsonify({
            "code": booking_response.status_code,
            "message": booking_data.get("message", "Failed to cancel booking.")
        }), booking_response.status_code

    booking = booking_data["data"]

    # get customer info to send notification
    try:
        customer_response = requests.get(
            f"{CUSTOMER_URL}/customer/{booking['customer_id']}"
        )
        customer_data = customer_response.json()
        customer = customer_data["data"]

        # notify customer of cancellation
        requests.post(
            f"{NOTIFICATION_URL}/notifications",
            json={
                "customer_id": booking["customer_id"],
                "email": customer["email"],
                "message": (
                    f"Hi {customer['name']}, your fitting appointment "
                    f"(Booking ID: {booking_id}) has been successfully cancelled."
                )
            }
        )
    except Exception as e:
        print(f"[WARNING] Notification service error: {str(e)}")

    return jsonify({
        "code": 200,
        "data": {
            "booking_id": booking_id,
            "status": "CANCELLED"
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)