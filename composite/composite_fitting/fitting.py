from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS
from flasgger import Swagger
import pika
import json

app = Flask(__name__)
CORS(app)

app.config['SWAGGER'] = {
    'title': 'Fitting Service API',
    'openapi': '3.0.2',
    'uiversion': 3
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "openapi": "3.0.2",
    "info": {
        "title": "Fitting Service API",
        "version": "1.0.0",
        "description": "Composite microservice for browsing dresses and scheduling or cancelling fitting appointments."
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

INVENTORY_URL    = os.environ.get('INVENTORY_URL',    'http://inventory_service:5001')
BOOKING_URL      = os.environ.get('BOOKING_URL',      'http://booking_service:5002')
CUSTOMER_URL     = os.environ.get('CUSTOMER_URL',     'http://customer_service:5000')
NOTIFICATION_URL = os.environ.get('NOTIFICATION_URL', 'https://personal-oqeeivkb.outsystemscloud.com/NotificationsAtomicMicroservice/rest/Notifications/SendNotification')


@app.route("/fitting/dresses", methods=['GET'])
def get_all_dresses():
    """
    Get all dresses for fitting
    ---
    tags:
      - Fitting
    responses:
      200:
        description: List of dresses retrieved successfully
      500:
        description: Failed to reach inventory service
    """
    try:
        response = requests.get(f"{INVENTORY_URL}/inventory", timeout=5)
        data = response.json()
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Failed to reach inventory service: {str(e)}"
        }), 500

    if response.status_code != 200:
        return jsonify({
            "code": response.status_code,
            "message": data.get("message", "Could not retrieve dresses.")
        }), response.status_code

    return jsonify({
        "code": 200,
        "data": data.get("data", {})
    }), 200


@app.route("/fitting/dresses/<int:dress_id>", methods=['GET'])
def get_dress_by_id(dress_id):
    """
    Get dress details by dress ID
    ---
    tags:
      - Fitting
    parameters:
      - name: dress_id
        in: path
        required: true
        schema:
          type: integer
        example: 101
    responses:
      200:
        description: Dress retrieved successfully
      404:
        description: Dress not found
      500:
        description: Failed to reach inventory service
    """
    try:
        response = requests.get(f"{INVENTORY_URL}/inventory/{dress_id}", timeout=5)
        data = response.json()
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Failed to reach inventory service: {str(e)}"
        }), 500

    if response.status_code != 200:
        return jsonify({
            "code": response.status_code,
            "message": data.get("message", f"Dress {dress_id} not found.")
        }), response.status_code

    return jsonify({
        "code": 200,
        "data": data.get("data", {})
    }), 200


@app.route("/fitting/available", methods=['GET'])
def get_available_dresses():
    """
    Get all available dresses for fitting
    ---
    tags:
      - Fitting
    responses:
      200:
        description: Available dresses retrieved successfully
      404:
        description: No available dresses found
      500:
        description: Failed to reach inventory service
    """
    try:
        response = requests.get(f"{INVENTORY_URL}/inventory/available", timeout=5)
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
        "data": data.get("data", {})
    }), 200


@app.route("/fitting/schedule", methods=['POST'])
def schedule_fitting():
    """
    Schedule a fitting appointment
    ---
    tags:
      - Fitting
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - customer_id
              - dress_id
              - slot_datetime
            properties:
              customer_id:
                type: integer
                example: 1
              dress_id:
                type: integer
                example: 101
              slot_datetime:
                type: string
                example: "2026-04-12 14:00:00"
    responses:
      201:
        description: Fitting appointment scheduled successfully
      400:
        description: Invalid JSON, missing required fields, or dress unavailable on selected date
      404:
        description: Customer or dress not found
      500:
        description: Downstream service error or booking creation failed
    """
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"Invalid JSON: {str(e)}"
        }), 400

    if not data:
        return jsonify({
            "code": 400,
            "message": "Request body must be valid JSON."
        }), 400

    for field in ['customer_id', 'dress_id', 'slot_datetime']:
        if field not in data:
            return jsonify({
                "code": 400,
                "message": f"Missing required field: {field}"
            }), 400

    customer_id = data['customer_id']
    dress_id = data['dress_id']
    slot_datetime = data['slot_datetime']

    try:
        inventory_response = requests.get(f"{INVENTORY_URL}/inventory/{dress_id}", timeout=5)
        inventory_data = inventory_response.json()
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Inventory error: {str(e)}"
        }), 500

    if inventory_response.status_code != 200:
        return jsonify({
            "code": inventory_response.status_code,
            "message": inventory_data.get("message", f"Dress {dress_id} not found in inventory.")
        }), inventory_response.status_code

    dress = inventory_data.get("data")
    if not dress:
        return jsonify({
            "code": 500,
            "message": "Inventory response missing dress data."
        }), 500

    unavailable_dates = dress.get("unavailable_dates", [])
    if unavailable_dates is None:
        unavailable_dates = []

    date_only = slot_datetime.split(' ')[0]
    if date_only in unavailable_dates:
        return jsonify({
            "code": 400,
            "message": f"Dress {dress_id} is already booked for {date_only}."
        }), 400

    if not dress.get("is_available", False):
        return jsonify({
            "code": 400,
            "message": f"Dress {dress_id} is not available for fitting."
        }), 400

    try:
        customer_response = requests.get(f"{CUSTOMER_URL}/customer/{customer_id}", timeout=5)
        customer_data = customer_response.json()
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Customer error: {str(e)}"
        }), 500

    if customer_response.status_code != 200:
        return jsonify({
            "code": customer_response.status_code,
            "message": customer_data.get("message", f"Customer {customer_id} not found.")
        }), customer_response.status_code

    customer = customer_data.get("data")
    if not customer:
        return jsonify({
            "code": 500,
            "message": "Customer response missing customer data."
        }), 500

    try:
        booking_response = requests.post(
            f"{BOOKING_URL}/bookings",
            json={
                "customer_id": customer_id,
                "dress_id": dress_id,
                "slot_datetime": slot_datetime
            },
            timeout=5
        )
        booking_data = booking_response.json()
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Booking error: {str(e)}"
        }), 500

    if booking_response.status_code != 201:
        return jsonify({
            "code": booking_response.status_code,
            "message": booking_data.get("message", "Failed to create booking.")
        }), booking_response.status_code

    booking = booking_data.get("data")
    if not booking:
        return jsonify({
            "code": 500,
            "message": "Booking response missing booking data."
        }), 500

    try:
        updated_dates = list(unavailable_dates)
        if date_only not in updated_dates:
            updated_dates.append(date_only)

        inventory_update_response = requests.put(
            f"{INVENTORY_URL}/inventory/{dress_id}",
            json={
                "is_available": True,
                "unavailable_dates": updated_dates
            },
            timeout=5
        )
        inventory_update_data = inventory_update_response.json()

        if inventory_update_response.status_code != 200:
            return jsonify({
                "code": inventory_update_response.status_code,
                "message": inventory_update_data.get("message", "Booking succeeded but inventory update failed.")
            }), inventory_update_response.status_code
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Inventory update error: {str(e)}"
        }), 500

    try:
    # 1. Prepare the exact same data
        notification_data = {
                "customer_id": customer_id,
                "email": customer["email"],
                "message": (
                    f"Hi {customer['name']}, your fitting appointment for dress "
                    f"(ID: {dress_id}, Size: {dress['size']}) is confirmed on "
                    f"{slot_datetime}. Booking ID: {booking['booking_id']}."
                ),
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

    return jsonify({
        "code": 201,
        "data": {
            "booking_id": booking["booking_id"],
            "slot_datetime": booking["slot_datetime"],
            "dress_id": dress_id,
            "dress_size": dress["size"],
            "customer_id": customer_id,
            "customer_name": customer["name"],
            "customer_email": customer["email"]
        }
    }), 201


@app.route("/fitting/cancel/<int:booking_id>", methods=['PUT'])
def cancel_fitting(booking_id):
    """
    Cancel a fitting appointment
    ---
    tags:
      - Fitting
    parameters:
      - name: booking_id
        in: path
        required: true
        schema:
          type: integer
        example: 1
    responses:
      200:
        description: Fitting appointment cancelled successfully
      404:
        description: Booking not found
      500:
        description: Booking cancellation failed or downstream service error
    """
    # ── Step: Fetch Customer & Send Notification via RabbitMQ ────────────────
    try:
        # 1. Fetch the customer data so we know who to text!
        customer_id = booking.get("customer_id")
        customer = {}
        if customer_id:
            cust_resp = requests.get(f"{CUSTOMER_URL}/customer/{customer_id}", timeout=5)
            if cust_resp.status_code == 200:
                customer = cust_resp.json().get("data", {})

        # 2. Prepare the notification data using .get() to prevent crashes
        notification_data = {
            "customer_id": customer_id,
            "email": customer.get("email", ""),
            "message": (
                f"Hi {customer.get('name', 'Customer')}, your fitting appointment "
                f"(Booking ID: {booking_id}) has been successfully cancelled."
            ),
            "phone": customer.get("phone", "+18777804236")
        }

        # 3. Connect to RabbitMQ (the "Post Office")
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # 4. Ensure the queue exists
        channel.queue_declare(queue='notifications_queue', durable=True)

        # 5. Drop the message in the queue
        channel.basic_publish(
            exchange='',
            routing_key='notifications_queue',
            body=json.dumps(notification_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )
        connection.close()
        print(f"[DEBUG] Cancel notification for booking {booking_id} dropped into RabbitMQ!", flush=True)

    except Exception as e:
        print(f"[ERROR] Failed to send cancel notification to RabbitMQ: {str(e)}", flush=True)

    if booking_response.status_code != 200:
        return jsonify({
            "code": booking_response.status_code,
            "message": booking_data.get("message", "Failed to cancel booking.")
        }), booking_response.status_code

    booking = booking_data.get("data")
    if not booking:
        return jsonify({
            "code": 500,
            "message": "Booking response missing booking data."
        }), 500

    dress_id = booking.get("dress_id")
    slot_datetime = booking.get("slot_datetime")

    if dress_id is not None and slot_datetime is not None:
        try:
            # Get current inventory state
            inventory_response = requests.get(
                f"{INVENTORY_URL}/inventory/{dress_id}",
                timeout=5
            )
            inventory_data = inventory_response.json()

            if inventory_response.status_code == 200:
                dress = inventory_data.get("data", {})
                current_dates = dress.get("unavailable_dates", [])
                if current_dates is None:
                    current_dates = []

                date_only = slot_datetime.split(' ')[0]

                updated_dates = [d for d in current_dates if d != date_only]

                requests.put(
                    f"{INVENTORY_URL}/inventory/{dress_id}",
                    json={
                        "is_available": True,
                        "unavailable_dates": updated_dates
                    },
                    timeout=5
                )
        except Exception:
            pass

    try:
    # 1. Prepare the exact same data
        notification_data = {
                    "customer_id": booking["customer_id"],
                    "email": customer["email"],
                    "message": (
                        f"Hi {customer['name']}, your fitting appointment "
                        f"(Booking ID: {booking_id}) has been successfully cancelled."
                    ),
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

    return jsonify({
        "code": 200,
        "data": {
            "booking_id": booking_id,
            "status": "CANCELLED"
        }
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=False)