from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DBURI', 'mysql+mysqlconnector://root:root@localhost:3306/dress_rental'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
app.config['TRUSTED_HOSTS'] = None
db = SQLAlchemy(app)

class Rental(db.Model):
    __tablename__ = 'rentals'
    rental_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, nullable=False)
    dress_id    = db.Column(db.Integer, nullable=False)
    start_date  = db.Column(db.Date, nullable=False)
    end_date    = db.Column(db.Date, nullable=False)
    status      = db.Column(db.String(30), default='PENDING')
    created_at  = db.Column(db.DateTime, default=datetime.now)

    def json(self):
        return {
            "rental_id":  self.rental_id,
            "customer_id": self.customer_id,
            "dress_id":   self.dress_id,
            "start_date": str(self.start_date),
            "end_date":   str(self.end_date),
            "status":     self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# UC3 Step 2 — POST create a new rental
@app.route("/rental", methods=['POST'])
def create_rental():
    data = request.get_json()
    for field in ['customer_id', 'dress_id', 'start_date', 'end_date']:
        if field not in data:
            return jsonify({"code": 400, "message": f"Missing required field: {field}"}), 400
            
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date   = datetime.strptime(data['end_date'],   '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"code": 400, "message": "Invalid date format. Use YYYY-MM-DD."}), 400
                
    rental = Rental(
        customer_id=data['customer_id'],
        dress_id=data['dress_id'],
        start_date=start_date,
        end_date=end_date,
        status='PENDING'
    )

    try:
        db.session.add(rental)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": "An error occurred creating the rental."}), 500
    
    return jsonify({"code": 201, "data": rental.json()}), 201

# UC3 Step 3 / UC4 Step 1 — GET one rental by ID
@app.route("/rental/<int:rental_id>")
def get_rental(rental_id):
    rental = db.session.scalar(db.select(Rental).filter_by(rental_id=rental_id))
    if rental:
        return jsonify({"code": 200, "data": rental.json()})
    return jsonify({"code": 404, "message": "Rental not found."}), 404

# UC4 Step 9 — PUT update rental (status → CLOSED, add fees)
@app.route("/rental/<int:rental_id>", methods=['PUT'])
def update_rental(rental_id):
    rental = db.session.scalar(db.select(Rental).filter_by(rental_id=rental_id))
    if not rental:
        return jsonify({"code": 404, "message": "Rental not found"}), 404

    data = request.get_json()

    if 'status' not in data:
        return jsonify({"code": 400, "message": "Missing required field: status"}), 400
        
    try:
        rental.status = data['status']
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": "An error occurred updating the rental."}), 500

    return jsonify({"code": 200, "data": rental.json()}), 200

# Cleanup — GET rentals stuck in PENDING beyond N minutes
@app.route("/rentals/stale-pending", methods=['GET'])
def get_stale_pending():
    minutes = int(request.args.get('minutes', 15))
    cutoff  = datetime.now() - timedelta(minutes=minutes)
    stale   = db.session.scalars(
        db.select(Rental).where(
            Rental.status == 'PENDING',
            Rental.created_at <= cutoff
        )
    ).all()
    return jsonify({"code": 200, "data": [r.json() for r in stale]})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)