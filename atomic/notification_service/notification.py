from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DBURI', 'mysql+mysqlconnector://root:root@localhost:3306/dress_rental'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)


class Notification(db.Model):
    __tablename__ = 'notifications'

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('PENDING', 'SENT', 'FAILED'), default='PENDING')

    def __init__(self, customer_id, email, message, status='PENDING'):
        self.customer_id = customer_id
        self.email = email
        self.message = message
        self.status = status

    def json(self):
        return {
            "notification_id": self.notification_id,
            "customer_id": self.customer_id,
            "email": self.email,
            "message": self.message,
            "status": self.status
        }


# ─── GET ALL NOTIFICATIONS ────────────────────────────────────────────────────

@app.route("/notifications")
def get_all():
    notifications = db.session.scalars(db.select(Notification)).all()

    if len(notifications):
        return jsonify({
            "code": 200,
            "data": {
                "notifications": [n.json() for n in notifications]
            }
        })
    return jsonify({
        "code": 404,
        "message": "No notifications found."
    }), 404


# ─── GET BY NOTIFICATION ID ───────────────────────────────────────────────────

@app.route("/notifications/<int:notification_id>")
def get_by_notification_id(notification_id):
    notification = db.session.scalar(
        db.select(Notification).filter_by(notification_id=notification_id)
    )

    if notification:
        return jsonify({
            "code": 200,
            "data": notification.json()
        })
    return jsonify({
        "code": 404,
        "message": f"Notification {notification_id} not found."
    }), 404


# ─── GET BY CUSTOMER ID ───────────────────────────────────────────────────────

@app.route("/notifications/customer/<int:customer_id>")
def get_by_customer_id(customer_id):
    notifications = db.session.scalars(
        db.select(Notification).filter_by(customer_id=customer_id)
    ).all()

    if notifications:
        return jsonify({
            "code": 200,
            "data": {
                "notifications": [n.json() for n in notifications]
            }
        })
    return jsonify({
        "code": 404,
        "message": f"No notifications found for customer {customer_id}."
    }), 404


# ─── SEND NOTIFICATION ────────────────────────────────────────────────────────
# Used by: Fitting Service (UC2) step 7 → confirm fitting appointment
#          Place Rental Order (UC3) step 9 → confirm rental order
# Receives: { customer_id, email, message }
# Returns:  { notification_id, status }
# Note: Twilio integration to be added here later

@app.route("/notifications", methods=['POST'])
def send_notification():
    data = request.get_json()

    for field in ['customer_id', 'email', 'message']:
        if field not in data:
            return jsonify({
                "code": 400,
                "message": f"Missing required field: {field}"
            }), 400

    notification = Notification(
        customer_id=data['customer_id'],
        email=data['email'],
        message=data['message'],
        status='PENDING'
    )

    try:
        db.session.add(notification)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred saving the notification."
        }), 500

    # ── Twilio integration placeholder ────────────────────────────────────────
    # When ready, replace this block with actual Twilio API call:
    #
    # from twilio.rest import Client
    # client = Client(os.environ.get('TWILIO_ACCOUNT_SID'),
    #                 os.environ.get('TWILIO_AUTH_TOKEN'))
    # client.messages.create(
    #     to=data['phone'],           # add phone field when integrating
    #     from_=os.environ.get('TWILIO_PHONE'),
    #     body=data['message']
    # )
    #
    # On success → update status to 'SENT'
    # On failure → update status to 'FAILED'
    # ─────────────────────────────────────────────────────────────────────────

    # for now mark as SENT to simulate success
    try:
        notification.status = 'SENT'
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        notification.status = 'FAILED'

    return jsonify({
        "code": 201,
        "data": notification.json()
    }), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)