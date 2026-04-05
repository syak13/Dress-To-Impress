from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging
import threading
import time
from datetime import datetime
import pika
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── LOGGING SETUP ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('rental_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ─── ATOMIC SERVICE URLS ──────────────────────────────────────────────────────
INVENTORY_URL    = os.environ.get('INVENTORY_URL',    'http://localhost:5001')
CUSTOMER_URL     = os.environ.get('CUSTOMER_URL',     'http://localhost:5000')
RENTAL_URL       = os.environ.get('RENTAL_URL',       'http://localhost:5004')
INVOICE_URL      = os.environ.get('INVOICE_URL',      'http://localhost:5005')
NOTIFICATION_URL = os.environ.get('NOTIFICATION_URL', 'http://localhost:5003')

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
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"Invalid JSON: {str(e)}"
        }), 400

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

    # ── Step 1: Get current dress inventory state ─────────────────────────────
    try:
        inventory_response = requests.get(f"{INVENTORY_URL}/inventory/{dress_id}", timeout=5)
        inventory_data = inventory_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Inventory error: {str(e)}"}), 500

    if inventory_response.status_code != 200:
        return jsonify({
            "code": inventory_response.status_code,
            "message": inventory_data.get("message", f"Dress {dress_id} not found.")
        }), inventory_response.status_code

    dress = inventory_data.get("data")
    if not dress:
        return jsonify({"code": 500, "message": "Inventory response missing dress data."}), 500

    unavailable_dates = dress.get("unavailable_dates", [])
    if unavailable_dates is None:
        unavailable_dates = []

    # ── Step 2: Check date overlap and add rental dates ──────────────────────
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    current_date = start_date_obj
    while current_date <= end_date_obj:
        date_str = current_date.strftime('%Y-%m-%d')
        if date_str in unavailable_dates:
            return jsonify({
                "code": 400,
                "message": f"Dress {dress_id} is already unavailable on {date_str}."
            }), 400
        current_date = current_date.replace(day=current_date.day + 1)

    # Add all rental dates to unavailable_dates
    rental_dates = []
    current_date = start_date_obj
    while current_date <= end_date_obj:
        date_str = current_date.strftime('%Y-%m-%d')
        if date_str not in unavailable_dates:
            rental_dates.append(date_str)
        current_date = current_date.replace(day=current_date.day + 1)

    updated_dates = unavailable_dates + rental_dates

    # ── Step 3: Update inventory with new unavailable dates ──────────────────
    try:
        inventory_update_response = requests.put(
            f"{INVENTORY_URL}/inventory/{dress_id}",
            json={
                "is_available": True,  # Keep available for fittings
                "unavailable_dates": updated_dates
            },
            timeout=5
        )
        inventory_update_data = inventory_update_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Inventory update error: {str(e)}"}), 500

    if inventory_update_response.status_code != 200:
        return jsonify({
            "code": 500,
            "message": "Failed to update inventory dates."
        }), 500

    dress_price = dress["price"]
    dress_size  = dress["size"]

    # ── Step 4: Create rental record ─────────────────────────────────────────
    try:
        rental_response = requests.post(
            f"{RENTAL_URL}/rental",
            json={
                "customer_id": customer_id,
                "dress_id":    dress_id,
                "start_date":  start_date,
                "end_date":    end_date,
                "status":      "PENDING"
            },
            timeout=5
        )
        rental_data = rental_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Rental service error: {str(e)}"}), 500

    if rental_response.status_code != 201:
        return jsonify({
            "code": 500,
            "message": f"Failed to create rental record."
        }), 500

    rental = rental_data["data"]
    rental_id = rental["rental_id"]

    # ── Step 5: Create rental invoice ────────────────────────────────────────
    try:
        invoice_response = requests.post(
            f"{INVOICE_URL}/invoice",
            json={
                "rental_id": rental_id,
                "amount":    dress_price,
                "type":      "RENTAL"
            },
            timeout=5
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

    # ── Step 6: Get customer information ─────────────────────────────────────
    try:
        customer_response = requests.get(f"{CUSTOMER_URL}/customer/{customer_id}", timeout=5)
        customer_data = customer_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Customer service error: {str(e)}"}), 500

    if customer_response.status_code != 200:
        return jsonify({
            "code": 404,
            "message": f"Customer {customer_id} not found."
        }), 404

    customer = customer_data["data"]

    # ── Step 7: Send confirmation SMS ────────────────────────────────────────

    try:
    # 1. Prepare the exact same data
        notification_data = {
            "customer_id": customer_id,
            "email": customer.get("email", ""),
            "message": (
                    f"Hi {customer['name']}, your rental order (ID: {rental_id}) "
                    f"for dress {dress_id} (Size: {dress_size}) from "
                    f"{start_date} to {end_date} is confirmed! "
                    f"Total: ${dress_price}. Invoice: {invoice['invoice_id']}."),
            "phone": customer.get("phone", "+18777804236")
        }

        # 2. Connect to RabbitMQ (the "Post Office")
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # 3. Ensure the queue exists
        channel.queue_declare(queue='notifications_queue', durable=True)

        # 4. Drop the message in the queue
        channel.basic_publish(
            exchange='',
            routing_key='notifications_queue',
            body=json.dumps(notification_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent so it survives restarts
            )
        )
        connection.close()
        print("[DEBUG] Message dropped into RabbitMQ successfully!", flush=True)

    except Exception as e:
        print(f"[ERROR] Failed to send to RabbitMQ: {str(e)}", flush=True)

    # ── Step 8: Return rental order confirmation ─────────────────────────────
    return jsonify({
        "code": 201,
        "data": {
            "rental_id":      rental_id,
            "invoice_id":     invoice["invoice_id"],
            "customer_id":    customer_id,
            "customer_name":  customer["name"],
            "customer_phone": customer["phone"],
            "dress_id":       dress_id,
            "dress_size":     dress_size,
            "start_date":     start_date,
            "end_date":       end_date,
            "amount":         dress_price,
            "status":         rental["status"],
            "client_secret":  client_secret
        }
    }), 201


# ─── UC3 CONFIRM: Fan-out after payment succeeds ──────────────────────────────
@app.route("/rental-order/confirm", methods=['POST'])
def confirm_rental_order():
    """
    Called by frontend after Stripe payment succeeds.
    Fan-out: update rental ACTIVE + update invoice PAID + send notification (parallel).
    Expected JSON: { rental_id, invoice_id, stripe_id, customer_id,
                     customer_name, customer_phone, dress_id, dress_size,
                     start_date, end_date, amount }
    """
    data = request.get_json()
    rental_id      = data['rental_id']
    invoice_id     = data['invoice_id']
    stripe_id      = data['stripe_id']
    customer_id    = data['customer_id']
    customer_name  = data.get('customer_name', '')
    customer_phone = data.get('customer_phone', '')
    dress_id       = data.get('dress_id', '')
    dress_size     = data.get('dress_size', '')
    start_date     = data.get('start_date', '')
    end_date       = data.get('end_date', '')
    amount         = data.get('amount', 0)

    fanout_errors = []

    def update_rental_active():
        r = requests.put(f"{RENTAL_URL}/rental/{rental_id}", json={"status": "ACTIVE"}, timeout=5)
        if r.status_code != 200:
            raise Exception(f"Rental update failed: {r.text}")
        return "rental_active"

    def update_invoice_paid():
        r = requests.put(f"{INVOICE_URL}/invoice/{invoice_id}",
                         json={"status": "PAID", "stripe_id": stripe_id}, timeout=5)
        if r.status_code != 200:
            raise Exception(f"Invoice update failed: {r.text}")
        return "invoice_paid"

    def send_success_notification():
        r = requests.post(f"{NOTIFICATION_URL}/notifications", json={
            "customer_id": customer_id,
            "phone": customer_phone,
            "message": (
                f"Hi {customer_name}, your rental (ID: {rental_id}) for dress {dress_id} "
                f"(Size: {dress_size}) from {start_date} to {end_date} is confirmed! "
                f"Total paid: ${amount}. Please return on time and in good condition."
            )
        }, timeout=5)
        if r.status_code not in (200, 201):
            raise Exception(f"Notification failed: {r.text}")
        return "notification_sent"

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(update_rental_active):      "update_rental",
            executor.submit(update_invoice_paid):       "update_invoice",
            executor.submit(send_success_notification): "send_notification",
        }
        for future in as_completed(futures):
            task = futures[future]
            try:
                future.result()
                logger.info(f"[CONFIRM] rental_id={rental_id} task={task} OK")
            except Exception as e:
                fanout_errors.append(f"{task}: {str(e)}")
                logger.error(f"[CONFIRM] rental_id={rental_id} task={task} FAILED: {e}")

    return jsonify({
        "code": 200,
        "data": {"rental_id": rental_id, "status": "ACTIVE"},
        "warnings": fanout_errors
    })


# ─── UC3 CANCEL: Clean up after payment fails ────────────────────────────────
@app.route("/rental-order/cancel", methods=['POST'])
def cancel_rental_order():
    """
    Called by frontend when Stripe payment fails.
    Cancels rental + sends failure notification.
    Expected JSON: { rental_id, customer_id, customer_name, customer_phone, reason }
    """
    data           = request.get_json()
    rental_id      = data['rental_id']
    customer_id    = data.get('customer_id')
    customer_name  = data.get('customer_name', '')
    customer_phone = data.get('customer_phone', '')
    reason         = data.get('reason', 'Payment failed')

    logger.error(f"[CANCEL] rental_id={rental_id} customer_id={customer_id} reason={reason}")

    # Cancel rental
    try:
        r = requests.put(f"{RENTAL_URL}/rental/{rental_id}", json={"status": "CANCELLED"}, timeout=5)
        if r.status_code != 200:
            logger.error(f"[CANCEL] Failed to cancel rental {rental_id}: {r.text}")
    except Exception as e:
        logger.error(f"[CANCEL] Rental cancellation error: {e}")

    # Notify customer of failure
    try:
        requests.post(f"{NOTIFICATION_URL}/notifications", json={
            "customer_id": customer_id,
            "phone": customer_phone,
            "message": (
                f"Hi {customer_name}, unfortunately your rental order (ID: {rental_id}) "
                f"could not be processed. Reason: {reason}. Please try again."
            )
        }, timeout=5)
    except Exception as e:
        logger.error(f"[CANCEL] Notification error for rental {rental_id}: {e}")

    return jsonify({"code": 200, "data": {"rental_id": rental_id, "status": "CANCELLED"}})


# ─── BACKGROUND CLEANUP: Cancel stuck PENDING rentals ────────────────────────
STALE_MINUTES    = 5    # cancel PENDING rentals older than this
CLEANUP_INTERVAL = 120  # run every 2 minutes

def cleanup_stale_rentals():
    while True:
        time.sleep(CLEANUP_INTERVAL)
        try:
            resp = requests.get(
                f"{RENTAL_URL}/rentals/stale-pending",
                params={"minutes": STALE_MINUTES},
                timeout=5
            )
            stale = resp.json().get("data", [])
            for rental in stale:
                rid = rental["rental_id"]
                try:
                    requests.put(
                        f"{RENTAL_URL}/rental/{rid}",
                        json={"status": "CANCELLED"},
                        timeout=5
                    )
                    logger.warning(f"[CLEANUP] Auto-cancelled stale PENDING rental_id={rid}")
                except Exception as e:
                    logger.error(f"[CLEANUP] Failed to cancel rental_id={rid}: {e}")
        except Exception as e:
            logger.error(f"[CLEANUP] Stale check failed: {e}")

cleanup_thread = threading.Thread(target=cleanup_stale_rentals, daemon=True)
cleanup_thread.start()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5011, debug=False)