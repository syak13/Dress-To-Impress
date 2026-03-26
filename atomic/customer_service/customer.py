from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

import os

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DBURI', 'mysql+mysqlconnector://root:root@localhost:3306/dress_rental'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SQLALCHEMY_ENGINE_OPTIONS']={'pool_recycle':299}

db = SQLAlchemy(app)

class Customer(db.Model):
    __tablename__ = 'customers'

    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def json(self):
        return {"customer_id": self.customer_id, "name": self.name, "email": self.email}


@app.route("/customer")
def get_all():
    customers = db.session.scalars(db.select(Customer)).all()

    if len(customers):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "customers": [customer.json() for customer in customers]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no customers."
        }
    ), 404

@app.route("/customer/<int:customer_id>")
def find_by_customer_id(customer_id):
    customer = db.session.scalar(
        db.select(Customer).filter_by(customer_id=customer_id)
    )

    if customer:
        return jsonify(
            {
                "code": 200,
                "data": customer.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Customer not found."
        }
    ), 404

@app.route("/customer", methods=['POST'])
def create_customer():
    data = request.get_json()
    
    if not data or 'name' not in data or 'email' not in data:
        return jsonify(
            {
                "code": 400,
                "message": "Missing required fields: name, email"
            }
        ), 400

    if db.session.scalar(db.select(Customer).filter_by(email=data['email'])):
        return jsonify(
            {
                "code": 400,
                "data": {
                    "email": data['email']
                },
                "message": "Customer with this email already exists."
            }
        ), 400

    customer = Customer(data['name'], data['email'])

    try:
        db.session.add(customer)
        db.session.commit()
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred creating the customer."
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": customer.json()
        }
    ), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)