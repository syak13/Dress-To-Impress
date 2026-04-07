from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from flasgger import Swagger

app = Flask(__name__)

app.config['SWAGGER'] = {
    'title': 'Inventory Service API',
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
        "title": "Inventory Service API",
        "version": "1.0.0",
        "description": "Atomic microservice for managing dress inventory and availability."
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

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
    """
    Get all dresses in inventory
    ---
    tags:
      - Inventory
    responses:
      200:
        description: List of all dresses
      404:
        description: No dresses found in inventory
    """
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
    """
    Get dress by dress ID
    ---
    tags:
      - Inventory
    parameters:
      - name: dress_id
        in: path
        required: true
        schema:
          type: integer
        example: 101
    responses:
      200:
        description: Dress found
      404:
        description: Dress not found
    """
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
    """
    Get all available dresses
    ---
    tags:
      - Inventory
    responses:
      200:
        description: List of available dresses
      404:
        description: No available dresses found
    """
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
    """
    Update dress availability and unavailable dates
    ---
    tags:
      - Inventory
    parameters:
      - name: dress_id
        in: path
        required: true
        schema:
          type: integer
        example: 101
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - is_available
            properties:
              is_available:
                type: boolean
                example: true
              unavailable_dates:
                type: array
                items:
                  type: string
                example:
                  - "2026-04-16"
                  - "2026-04-17"
    responses:
      200:
        description: Inventory updated successfully
      400:
        description: Invalid JSON or missing required field
      404:
        description: Dress not found
      500:
        description: Inventory update failed
    """
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
    """
    Create a new dress in inventory
    ---
    tags:
      - Inventory
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - dress_id
              - name
              - size
              - price
              - color
              - img
            properties:
              dress_id:
                type: integer
                example: 101
              name:
                type: string
                example: "Pink Satin Gown"
              size:
                type: string
                example: "M"
              price:
                type: number
                example: 89.90
              color:
                type: string
                example: "Pink"
              img:
                type: string
                example: "images/pink-dress.jpg"
              unavailable_dates:
                type: array
                items:
                  type: string
                example: []
              is_available:
                type: boolean
                example: true
    responses:
      201:
        description: Dress created successfully
      400:
        description: Invalid JSON, missing fields, or duplicate dress ID
      500:
        description: Dress creation failed
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