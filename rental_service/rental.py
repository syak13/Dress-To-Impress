from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:syakira13@localhost:3306/dress_rental'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
db = SQLAlchemy(app)

class Rental(db.Model):
    __tablename__ = 'rentals'
    rental_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, nullable=False)
    dress_id    = db.Column(db.Integer, nullable=False)
    start_date  = db.Column(db.Date, nullable=False)
    end_date    = db.Column(db.Date, nullable=False)
    status      = db.Column(db.String(20), default='ACTIVE')

    def json(self):
        return {
            "rental_id": self.rental_id,
            "customer_id": self.customer_id,
            "dress_id": self.dress_id,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
            "status": self.status
        }

# UC3 Step 2 — POST create a new rental
@app.route("/rental", methods=['POST'])
def create_rental():
    data = request.get_json()
    rental = Rental(
        customer_id=data['customer_id'],
        dress_id=data['dress_id'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        status='ACTIVE'
    )
    db.session.add(rental)
    db.session.commit()
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
    # safe updates
    if 'status' in data:
        rental.status = data['status']
    if 'late_fee' in data and hasattr(rental, 'late_fee'):
        rental.late_fee = data['late_fee']
    if 'damage_fee' in data and hasattr(rental, 'damage_fee'):
        rental.damage_fee = data['damage_fee']
    if 'total_penalty' in data and hasattr(rental, 'total_penalty'):
        rental.total_penalty = data['total_penalty']

    db.session.commit()
    return jsonify({"code": 200, "data": rental.json()}), 200

if __name__ == '__main__':
    app.run(port=5002, debug=True)