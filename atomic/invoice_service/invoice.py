from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import stripe
import os

app = Flask(__name__)
CORS(app)

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DBURI', 'mysql+mysqlconnector://root:root@localhost:3306/dress_rental'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)


class Invoice(db.Model):
    __tablename__ = 'invoices'

    invoice_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rental_id  = db.Column(db.Integer, nullable=False)
    amount     = db.Column(db.Numeric(10, 2), nullable=False)
    type       = db.Column(db.Enum('RENTAL', 'PENALTY'), nullable=False)
    stripe_id  = db.Column(db.String(100))
    status     = db.Column(db.Enum('PENDING', 'PAID', 'FAILED', 'REFUNDED'), default='PENDING')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

    def __init__(self, rental_id, amount, type, stripe_id=None, status='PENDING'):
        self.rental_id = rental_id
        self.amount    = amount
        self.type      = type
        self.stripe_id = stripe_id
        self.status    = status

    def json(self):
        return {
            "invoice_id": self.invoice_id,
            "rental_id":  self.rental_id,
            "amount":     float(self.amount),
            "type":       self.type,
            "stripe_id":  self.stripe_id,
            "status":     self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── GET ALL INVOICES ─────────────────────────────────────────────────────────

@app.route("/invoice")
def get_all():
    invoices = db.session.scalars(db.select(Invoice)).all()

    if len(invoices):
        return jsonify({
            "code": 200,
            "data": {"invoices": [i.json() for i in invoices]}
        })
    return jsonify({"code": 404, "message": "No invoices found."}), 404


# ─── GET BY INVOICE ID ────────────────────────────────────────────────────────

@app.route("/invoice/<int:invoice_id>")
def get_by_invoice_id(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)

    if invoice:
        return jsonify({"code": 200, "data": invoice.json()})
    return jsonify({"code": 404, "message": f"Invoice {invoice_id} not found."}), 404


# ─── GET BY RENTAL ID ─────────────────────────────────────────────────────────
# Used by: Returning Service (UC4) to check existing invoices for a rental

@app.route("/invoice/rental/<int:rental_id>")
def get_by_rental_id(rental_id):
    invoices = db.session.scalars(
        db.select(Invoice).filter_by(rental_id=rental_id)
    ).all()

    if invoices:
        return jsonify({
            "code": 200,
            "data": {"invoices": [i.json() for i in invoices]}
        })
    return jsonify({"code": 404, "message": f"No invoices found for rental {rental_id}."}), 404


# ─── CREATE INVOICE ───────────────────────────────────────────────────────────
# Used by: Place Rental Order (UC3) step 6 → create RENTAL invoice
#          Returning Service  (UC4) step 6 → create PENALTY invoice

@app.route("/invoice", methods=['POST'])
def create_invoice():
    data = request.get_json()

    for field in ['rental_id', 'amount', 'type']:
        if field not in data:
            return jsonify({
                "code": 400,
                "message": f"Missing required field: {field}"
            }), 400

    if data['type'] not in ['RENTAL', 'PENALTY']:
        return jsonify({
            "code": 400,
            "message": "type must be either RENTAL or PENALTY"
        }), 400

    invoice = Invoice(
        rental_id=data['rental_id'],
        amount=data['amount'],
        type=data['type'],
        stripe_id=data.get('stripe_id', None),
        status='PENDING'
    )

    try:
        db.session.add(invoice)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": "An error occurred creating the invoice."}), 500

    # ── Stripe: create PaymentIntent ──────────────────────────────────────────
    client_secret = None
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(float(data['amount']) * 100),  # Stripe uses cents
            currency='sgd',
            metadata={"rental_id": data['rental_id'], "invoice_id": invoice.invoice_id}
        )
        invoice.stripe_id = payment_intent['id']
        db.session.commit()
        client_secret = payment_intent['client_secret']
    except Exception as e:
        print(f"[WARNING] Stripe PaymentIntent error: {str(e)}")
    # ─────────────────────────────────────────────────────────────────────────

    response = invoice.json()
    response['client_secret'] = client_secret
    return jsonify({"code": 201, "data": response}), 201


# ─── UPDATE INVOICE STATUS ────────────────────────────────────────────────────
# Used by: Stripe webhook later to update payment status (PAID, FAILED, REFUNDED)

@app.route("/invoice/<int:invoice_id>", methods=['PUT'])
def update_invoice_status(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)

    if not invoice:
        return jsonify({"code": 404, "message": f"Invoice {invoice_id} not found."}), 404

    data = request.get_json()

    if 'status' not in data:
        return jsonify({"code": 400, "message": "Missing required field: status"}), 400

    if data['status'] not in ['PENDING', 'PAID', 'FAILED', 'REFUNDED']:
        return jsonify({"code": 400, "message": "Invalid status value."}), 400

    try:
        invoice.status = data['status']
        if 'stripe_id' in data:
            invoice.stripe_id = data['stripe_id']
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": "An error occurred updating the invoice."}), 500

    return jsonify({"code": 200, "data": invoice.json()})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=False)
