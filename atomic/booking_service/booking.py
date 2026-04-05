from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DBURI', 'mysql+mysqlconnector://root:root@localhost:3306/dress_rental'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
app.config['TRUSTED_HOSTS'] = None

db = SQLAlchemy(app)


class Booking(db.Model):
    __tablename__ = 'bookings'

    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, nullable=False)
    dress_id = db.Column(db.Integer, nullable=False)
    slot_datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum('CONFIRMED', 'CANCELLED'), default='CONFIRMED')

    def __init__(self, customer_id, dress_id, slot_datetime, status='CONFIRMED'):
        self.customer_id = customer_id
        self.dress_id = dress_id
        self.slot_datetime = slot_datetime
        self.status = status

    def json(self):
        return {
            "booking_id": self.booking_id,
            "customer_id": self.customer_id,
            "dress_id": self.dress_id,
            "slot_datetime": self.slot_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status
        }


# ─── GET ALL BOOKINGS ─────────────────────────────────────────────────────────

@app.route("/bookings")
def get_all():
    bookings = db.session.scalars(db.select(Booking)).all()

    if len(bookings):
        return jsonify({
            "code": 200,
            "data": {
                "bookings": [booking.json() for booking in bookings]
            }
        })
    return jsonify({
        "code": 404,
        "message": "No bookings found."
    }), 404


# ─── GET BY BOOKING ID ────────────────────────────────────────────────────────

@app.route("/bookings/<int:booking_id>")
def get_by_booking_id(booking_id):
    booking = db.session.scalar(
        db.select(Booking).filter_by(booking_id=booking_id)
    )

    if booking:
        return jsonify({
            "code": 200,
            "data": booking.json()
        })
    return jsonify({
        "code": 404,
        "message": f"Booking {booking_id} not found."
    }), 404


# ─── GET BY CUSTOMER ID ───────────────────────────────────────────────────────

@app.route("/bookings/customer/<int:customer_id>")
def get_by_customer_id(customer_id):
    bookings = db.session.scalars(
        db.select(Booking).filter_by(customer_id=customer_id)
    ).all()

    if bookings:
        return jsonify({
            "code": 200,
            "data": {
                "bookings": [booking.json() for booking in bookings]
            }
        })
    return jsonify({
        "code": 404,
        "message": f"No bookings found for customer {customer_id}."
    }), 404


# ─── CREATE BOOKING ───────────────────────────────────────────────────────────
# Used by: Fitting Service (UC2) step 4
# Receives: { customer_id, dress_id, slot_datetime }
# Returns:  { booking_id, slot_datetime }

@app.route("/bookings", methods=['POST'])
def create_booking():
    data = request.get_json()

    for field in ['customer_id', 'dress_id', 'slot_datetime']:
        if field not in data:
            return jsonify({
                "code": 400,
                "message": f"Missing required field: {field}"
            }), 400

    slot_dt = datetime.strptime(data['slot_datetime'], "%Y-%m-%d %H:%M:%S")
    booking = Booking(
        customer_id=data['customer_id'],
        dress_id=data['dress_id'],
        slot_datetime=slot_dt,
        status='CONFIRMED'
    )

    try:
        db.session.add(booking)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred creating the booking."
        }), 500

    return jsonify({
        "code": 201,
        "data": booking.json()
    }), 201


# ─── CANCEL BOOKING ───────────────────────────────────────────────────────────
# Used by: Fitting Service if customer cancels appointment

@app.route("/bookings/<int:booking_id>/cancel", methods=['PUT'])
def cancel_booking(booking_id):
    booking = db.session.scalar(
        db.select(Booking).filter_by(booking_id=booking_id)
    )

    if not booking:
        return jsonify({
            "code": 404,
            "message": f"Booking {booking_id} not found."
        }), 404

    if booking.status == 'CANCELLED':
        return jsonify({
            "code": 400,
            "message": f"Booking {booking_id} is already cancelled."
        }), 400

    try:
        booking.status = 'CANCELLED'
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred cancelling the booking."
        }), 500

    return jsonify({
        "code": 200,
        "data": booking.json()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)