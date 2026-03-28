from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DBURI', 'mysql+mysqlconnector://root:root@localhost:3306/dress_rental'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)


class Inventory(db.Model):
    __tablename__ = 'inventory'

    dress_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    size = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    color = db.Column(db.String(255), nullable=False)
    img = db.Column(db.String(255), nullable=False)
    all_available_dates = db.Column(db.JSON)
    is_available = db.Column(db.Boolean, default=True)

    def __init__(self, dress_id, name, size, price, color, img, all_available_dates=None, is_available=True):
        self.dress_id = dress_id
        self.name = name
        self.size = size
        self.price = price
        self.color = color
        self.img = img
        self.all_available_dates = all_available_dates or []
        self.is_available = is_available

    def json(self):
        return {
            "dress_id": self.dress_id,
            "name": self.name,
            "size": self.size,
            "price": float(self.price),
            "color": self.color,
            "img": self.img,
            "all_available_dates": self.all_available_dates,
            "is_available": self.is_available
        }


# ─── GET ALL ─────────────────────────────────────────────────────────────────

@app.route("/inventory")
def get_all():
    dresses = db.session.scalars(db.select(Inventory)).all()

    if len(dresses):
        return jsonify({
            "code": 200,
            "data": {
                "dresses": [dress.json() for dress in dresses]
            }
        })
    return jsonify({
        "code": 404,
        "message": "No dresses found in inventory."
    }), 404


# ─── GET BY DRESS ID ──────────────────────────────────────────────────────────
# Used by: Fitting Service (UC2) step 2-3
#          Place Rental Order (UC3) step 4-5  → also returns price
#          Returning Service (UC4) step 2-3

@app.route("/inventory/<int:dress_id>")
def get_by_dress_id(dress_id):
    dress = db.session.scalar(
        db.select(Inventory).filter_by(dress_id=dress_id)
    )

    if dress:
        return jsonify({
            "code": 200,
            "data": dress.json()
        })
    return jsonify({
        "code": 404,
        "message": f"Dress {dress_id} not found."
    }), 404


# ─── GET AVAILABLE DRESSES ────────────────────────────────────────────────────
# Used by: Fitting Service (UC2) step 1 → get available fitting slots

@app.route("/inventory/available")
def get_available():
    dresses = db.session.scalars(
        db.select(Inventory).filter_by(is_available=True)
    ).all()

    if dresses:
        return jsonify({
            "code": 200,
            "data": {
                "dresses": [dress.json() for dress in dresses]
            }
        })
    return jsonify({
        "code": 404,
        "message": "No available dresses found."
    }), 404


# ─── UPDATE AVAILABILITY ──────────────────────────────────────────────────────
# Used by: Place Rental Order (UC3) step 4 → is_available: False (dress rented)
#          Returning Service  (UC4) step 8 → is_available: True  (dress returned)

@app.route("/inventory/<int:dress_id>", methods=['PUT'])
def update_inventory(dress_id):
    dress = db.session.scalar(
        db.select(Inventory).filter_by(dress_id=dress_id)
    )

    if not dress:
        return jsonify({
            "code": 404,
            "message": f"Dress {dress_id} not found."
        }), 404

    data = request.get_json()

    if 'is_available' not in data:
        return jsonify({
            "code": 400,
            "message": "Missing required field: is_available"
        }), 400

    try:
        dress.is_available = data['is_available']

        # also update available dates if provided
        if 'all_available_dates' in data:
            dress.all_available_dates = data['all_available_dates']

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred updating the inventory."
        }), 500

    return jsonify({
        "code": 200,
        "data": dress.json()
    })


# ─── CREATE NEW DRESS ─────────────────────────────────────────────────────────

@app.route("/inventory", methods=['POST'])
def create_dress():
    data = request.get_json()

    for field in ['dress_id', 'name', 'size', 'price', 'color', 'img']:
        if field not in data:
            return jsonify({
                "code": 400,
                "message": f"Missing required field: {field}"
            }), 400

    if db.session.scalar(db.select(Inventory).filter_by(dress_id=data['dress_id'])):
        return jsonify({
            "code": 400,
            "message": f"Dress {data['dress_id']} already exists."
        }), 400

    dress = Inventory(
        dress_id=data['dress_id'],
        name=data['name'],
        size=data['size'],
        price=data['price'],
        color=data['color'],
        img=data['img'],
        all_available_dates=data.get('all_available_dates', []),
        is_available=data.get('is_available', True)
    )

    try:
        db.session.add(dress)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred creating the dress."
        }), 500

    return jsonify({
        "code": 201,
        "data": dress.json()
    }), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)