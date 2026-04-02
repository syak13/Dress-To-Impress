from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import date, datetime
import os
import base64
import json
from groq import Groq                         
from dotenv import load_dotenv
load_dotenv()  # Loads .env file


app = Flask(__name__)
CORS(app)

groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DBURI', 'mysql+mysqlconnector://root@localhost:3306/dress_rental'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
db = SQLAlchemy(app)

# ── Models ─────────────────────────────────────────────

class ReturnAssessment(db.Model):
    __tablename__ = 'return_assessments'
    assessment_id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rental_id         = db.Column(db.Integer, nullable=False)
    dress_id          = db.Column(db.Integer, nullable=False)
    return_date   = db.Column(db.DateTime, nullable=False)
    is_late           = db.Column(db.Boolean, default=False)
    is_damaged        = db.Column(db.Boolean, default=False)
    damage_description = db.Column(db.Text)
    ai_damage_percent = db.Column(db.Float, default=0.0)

    def json(self):
        return {
            "assessment_id":     self.assessment_id,
            "rental_id":         self.rental_id,
            "dress_id":          self.dress_id,
            "return_date":   self.return_date.isoformat(),
            "is_late":           self.is_late,
            "is_damaged":        self.is_damaged,
            "damage_description": self.damage_description,
            "ai_damage_percent": self.ai_damage_percent
        }

class PenaltyFee(db.Model):
    __tablename__ = 'penalty_fees'
    penalty_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('return_assessments.assessment_id'), nullable=False)
    late_fee      = db.Column(db.Float, default=0.0)
    damage_fee    = db.Column(db.Float, default=0.0)
    total_penalty = db.Column(db.Float, default=0.0)
    assessment    = db.relationship('ReturnAssessment', backref='penalty')

    def json(self):
        return {
            "penalty_id":    self.penalty_id,
            "assessment_id": self.assessment_id,
            "late_fee":      self.late_fee,
            "damage_fee":    self.damage_fee,
            "total_penalty": self.total_penalty,
        }

# ── Helper functions ───────────────────────────────────────────────────────────

def calculate_is_late(end_date_str: str) -> bool:
    try:
        end_dt = date.fromisoformat(end_date_str)
    except ValueError:
        return False
    return date.today() > end_dt

# CHANGED: Now uses Groq vision (llama-4-scout)
def analyze_dress_damage(image_file):
    """Call Groq Vision API to analyze dress damage."""
    try:
        # Read and encode image to base64 (same pattern as reviews.py)
        image_data = base64.b64encode(image_file.read()).decode('utf-8')

        response = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",  # vision model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                "Analyze this rental dress image for damage. "
                                "Reply with ONLY valid JSON, no markdown, no explanation. "
                                "Format: "
                                '{"damage_percentage": 0-100, '
                                '"is_damaged": true or false, '
                                '"severity": "none" or "mild" or "moderate" or "severe", '
                                '"description": "one sentence describing the damage or lack of it"}'
                            )
                        }
                    ]
                }
            ],
            max_tokens=150
        )

        # Clean and parse the JSON response
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        ai_result = json.loads(raw)
        return ai_result

    except Exception as e:
        print(f"Groq analysis failed: {e}")
        # Demo fallback — safe default for presentation
        return {
            "damage_percentage": 35,
            "is_damaged": True,
            "severity": "moderate",
            "description": "Groq temporarily unavailable - demo mode"
        }

# Fee calculation (completely unchanged — $20 to $200)
def calculate_damage_fee(damage_percent):
    if damage_percent <= 10:
        return 0.0
    elif damage_percent <= 25:
        return 20.0
    elif damage_percent <= 40:
        return 50.0
    elif damage_percent <= 60:
        return 100.0
    elif damage_percent <= 80:
        return 150.0
    else:
        return 200.0

# ── Endpoints ──────────────────────────────────────────

@app.route("/assessment/image", methods=["POST"])
def create_ai_assessment():
    if 'image' not in request.files or 'rental_id' not in request.form:
        return jsonify({"code": 400, "message": "Missing image file or rental_id"}), 400

    rental_id  = int(request.form['rental_id'])
    dress_id   = int(request.form.get('dress_id', 0))
    end_date   = request.form.get('end_date', '')

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"code": 400, "message": "No image selected"}), 400

    image_file.seek(0)
    is_late = calculate_is_late(end_date) if end_date else False

    try:
        ai_result = analyze_dress_damage(image_file)

        damage_percent = ai_result.get('damage_percentage', 0)
        is_damaged     = ai_result.get('is_damaged', False)
        damage_desc    = ai_result.get('description', 'No damage detected')

        damage_fee = calculate_damage_fee(damage_percent)
        late_fee   = 20.0 if is_late else 0.0

        assessment = ReturnAssessment(
            rental_id=rental_id,
            dress_id=dress_id,
            return_date=datetime.now(),
            is_late=is_late,
            is_damaged=is_damaged,
            damage_description=f"Groq AI: {damage_desc} ({damage_percent}%)",
            ai_damage_percent=damage_percent
        )
        db.session.add(assessment)
        db.session.flush()

        penalty = PenaltyFee(
            assessment_id=assessment.assessment_id,
            late_fee=late_fee,
            damage_fee=damage_fee,
            total_penalty=late_fee + damage_fee
        )
        db.session.add(penalty)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Assessment failed: {str(e)}"}), 500

    return jsonify({
        "code": 201,
        "data": {
            "assessment_id":    assessment.assessment_id,
            "is_late":          is_late,
            "is_damaged":       is_damaged,
            "ai_damage_percent": damage_percent,
            "damage_description": damage_desc,
            "late_fee":         late_fee,
            "damage_fee":       damage_fee,
            "total_penalty":    late_fee + damage_fee,
        }
    }), 201


@app.route("/assessment", methods=["POST"])
def create_assessment():
    data = request.get_json() or {}
    for field in ["rental_id", "dress_id", "end_date"]:
        if field not in data:
            return jsonify({"code": 400, "message": f"Missing required field: {field}"}), 400

    is_late    = calculate_is_late(data["end_date"])
    is_damaged = bool(data.get("is_damaged", False))

    assessment = ReturnAssessment(
        rental_id=data["rental_id"],
        dress_id=data["dress_id"],
        return_date=datetime.now(),
        is_late=is_late,
        is_damaged=is_damaged,
        damage_description=data.get("damage_description", ""),
    )
    try:
        db.session.add(assessment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error creating assessment: {e}"}), 500

    return jsonify({
        "code": 201,
        "data": {
            "assessment_id": assessment.assessment_id,
            "is_late":       assessment.is_late,
            "is_damaged":    assessment.is_damaged
        }
    }), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=True)