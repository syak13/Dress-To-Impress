from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
import os

app = Flask(__name__)

# Uses your database: dress_rental
# If MySQL runs as a container in Docker Compose, change host.docker.internal → mysql
DB_HOST = os.getenv('DB_HOST', 'localhost')
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'mysql+mysqlconnector://root:root@{DB_HOST}:3306/dress_rental'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)


class ReturnAssessment(db.Model):
    __tablename__ = 'return_assessments'

    assessment_id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rental_id          = db.Column(db.Integer, nullable=False)
    dress_id           = db.Column(db.Integer, nullable=False)
    assessment_date    = db.Column(db.DateTime, nullable=False)  # DATETIME in SQL
    is_late            = db.Column(db.Boolean, default=False)
    is_damaged         = db.Column(db.Boolean, default=False)
    damage_description = db.Column(db.Text)
    assessed_by        = db.Column(db.Integer, nullable=False)

    def json(self):
        return {
            "assessment_id": self.assessment_id,
            "rental_id": self.rental_id,
            "dress_id": self.dress_id,
            "assessment_date": self.assessment_date.isoformat(),
            "is_late": self.is_late,
            "is_damaged": self.is_damaged,
            "damage_description": self.damage_description,
            "assessed_by": self.assessed_by,
        }


class PenaltyFee(db.Model):
    __tablename__ = 'penalty_fees'

    penalty_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    assessment_id = db.Column(
        db.Integer,
        db.ForeignKey('return_assessments.assessment_id'),
        nullable=False
    )
    late_fee      = db.Column(db.Float, default=0.0)   # DECIMAL(10,2) in SQL
    damage_fee    = db.Column(db.Float, default=0.0)
    total_penalty = db.Column(db.Float, default=0.0)

    assessment = db.relationship('ReturnAssessment', backref='penalty')

    def json(self):
        return {
            "penalty_id": self.penalty_id,
            "assessment_id": self.assessment_id,
            "late_fee": self.late_fee,
            "damage_fee": self.damage_fee,
            "total_penalty": self.total_penalty,
        }


def calculate_is_late(end_date_str: str) -> bool:
    """Compare today with the rental end_date (YYYY-MM-DD)."""
    try:
        end_dt = date.fromisoformat(end_date_str)
    except ValueError:
        return False
    return date.today() > end_dt


# ---------- API endpoints ----------

# UC4 Step 4 + 5: create assessment, return flags + assessment_id
@app.route("/assessment", methods=["POST"])
def create_assessment():
    """
    Expected JSON:
    {
      "rental_id": 1,
      "dress_id": 201,
      "end_date": "2026-03-14",
      "is_damaged": true/false,
      "damage_description": "...",
      "assessed_by": 991
    }
    """
    data = request.get_json() or {}

    required = ["rental_id", "dress_id", "end_date", "assessed_by"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({
            "code": 400,
            "message": f"Missing fields: {', '.join(missing)}"
        }), 400

    is_late = calculate_is_late(data["end_date"])
    is_damaged = bool(data.get("is_damaged", False))

    assessment = ReturnAssessment(
        rental_id=data["rental_id"],
        dress_id=data["dress_id"],
        assessment_date=datetime.now(),
        is_late=is_late,
        is_damaged=is_damaged,
        damage_description=data.get("damage_description", ""),
        assessed_by=data["assessed_by"],
    )

    try:
        db.session.add(assessment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": f"Error creating assessment: {e}"
        }), 500

    return jsonify({
        "code": 201,
        "data": {
            "assessment_id": assessment.assessment_id,
            "is_late": assessment.is_late,
            "is_damaged": assessment.is_damaged
        }
    }), 201


# Optional: create penalty row after composite service computes fees
@app.route("/penalty", methods=["POST"])
def create_penalty():
    """
    Expected JSON:
    {
      "assessment_id": 2,
      "late_fee": 50.00,
      "damage_fee": 150.00
    }
    """
    data = request.get_json() or {}
    required = ["assessment_id", "late_fee", "damage_fee"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({
            "code": 400,
            "message": f"Missing fields: {', '.join(missing)}"
        }), 400

    assessment = db.session.get(ReturnAssessment, data["assessment_id"])
    if not assessment:
        return jsonify({
            "code": 404,
            "message": "Assessment not found"
        }), 404

    late_fee = float(data["late_fee"])
    damage_fee = float(data["damage_fee"])
    total = late_fee + damage_fee

    penalty = PenaltyFee(
        assessment_id=assessment.assessment_id,
        late_fee=late_fee,
        damage_fee=damage_fee,
        total_penalty=total
    )

    try:
        db.session.add(penalty)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": f"Error creating penalty: {e}"
        }), 500

    return jsonify({
        "code": 201,
        "data": penalty.json()
    }), 201


@app.route("/assessment/<int:assessment_id>", methods=["GET"])
def get_assessment(assessment_id):
    assessment = db.session.get(ReturnAssessment, assessment_id)
    if not assessment:
        return jsonify({
            "code": 404,
            "message": "Assessment not found"
        }), 404
    return jsonify({
        "code": 200,
        "data": assessment.json()
    }), 200


@app.route("/penalty/<int:penalty_id>", methods=["GET"])
def get_penalty(penalty_id):
    penalty = db.session.get(PenaltyFee, penalty_id)
    if not penalty:
        return jsonify({
            "code": 404,
            "message": "Penalty not found"
        }), 404
    return jsonify({
        "code": 200,
        "data": penalty.json()
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
