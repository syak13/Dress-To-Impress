from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DBURI', 'mysql+mysqlconnector://root:root@localhost:3306/dress_rental'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
app.config['TRUSTED_HOSTS'] = None

db = SQLAlchemy(app)


class Inventory(db.Model):
    __tablename__ = 'inventory'

    dress_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    size = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    color = db.Column(db.String(255), nullable=False)
    img = db.Column(db.String(255), nullable=False)
    unavailable_dates = db.Column(db.JSON)
    is_available = db.Column(db.Boolean, default=True)

    def __init__(self, dress_id, name, size, price, color, img, unavailable_dates=None, is_available=True):
        self.dress_id = dress_id
        self.name = name
        self.size = size
        self.price = price
        self.color = color
        self.img = img
        self.unavailable_dates = unavailable_dates or []
        self.is_available = is_available

    def json(self):
        return {
            "dress_id": self.dress_id,
            "name": self.name,
            "size": self.size,
            "price": float(self.price),
            "color": self.color,
            "img": self.img,
            "unavailable_dates": self.unavailable_dates or [],
            "is_available": self.is_available
        }


@app.route("/inventory", methods=['GET'])
def get_all():
    dresses = db.session.scalars(db.select(Inventory)).all()

    if dresses:
        return jsonify({
            "code": 200,
            "data": {
                "dresses": [dress.json() for dress in dresses]
            }
        }), 200

    return jsonify({
        "code": 404,
        "message": "No dresses found in inventory."
    }), 404


@app.route("/inventory/<int:dress_id>", methods=['GET'])
def get_by_dress_id(dress_id):
    dress = db.session.scalar(
        db.select(Inventory).filter_by(dress_id=dress_id)
    )

    if dress:
        return jsonify({
            "code": 200,
            "data": dress.json()
        }), 200

    return jsonify({
        "code": 404,
        "message": f"Dress {dress_id} not found."
    }), 404


@app.route("/inventory/available", methods=['GET'])
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
        }), 200

    return jsonify({
        "code": 404,
        "message": "No available dresses found."
    }), 404


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

    if 'is_available' not in data:
        return jsonify({
            "code": 400,
            "message": "Missing required field: is_available"
        }), 400

    try:
        dress.is_available = data['is_available']

        if 'unavailable_dates' in data:
            dress.unavailable_dates = data['unavailable_dates']

        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred updating the inventory."
        }), 500

    return jsonify({
        "code": 200,
        "data": dress.json()
    }), 200


@app.route("/inventory", methods=['POST'])
def create_dress():
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

    for field in ['dress_id', 'name', 'size', 'price', 'color', 'img']:
        if field not in data:
            return jsonify({
                "code": 400,
                "message": f"Missing required field: {field}"
            }), 400

    existing_dress = db.session.scalar(
        db.select(Inventory).filter_by(dress_id=data['dress_id'])
    )
    if existing_dress:
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
        unavailable_dates=data.get('unavailable_dates', []),
        is_available=data.get('is_available', True)
    )

    try:
        db.session.add(dress)
        db.session.commit()
    except Exception:
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
    app.run(host='0.0.0.0', port=5001, debug=False)