from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flasgger import Swagger
from datetime import date, datetime
import os
import base64
import json
from groq import Groq                         
from dotenv import load_dotenv
load_dotenv()  # Loads .env file


app = Flask(__name__)
CORS(app)

app.config['SWAGGER'] = {
    'title': 'Return Assessment Service API',
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
        "title": "Return Assessment Service API",
        "version": "1.0.0",
        "description": "Atomic microservice for assessing returned dresses, detecting damage, and calculating penalty fees."
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DBURI', 'mysql+mysqlconnector://root:root@mysql:3306/dress_rental'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
app.config['TRUSTED_HOSTS'] = None
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

def is_dress_image(image_data: str, mime_type: str) -> bool:
    """Quick pre-check: is the uploaded image actually a dress/garment?"""
    try:
        response = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_data}"}
                    },
                    {
                        "type": "text",
                        "text": (
                            "Is this image showing a dress, gown, or clothing garment? "
                            "Reply with ONLY the word YES or NO."
                        )
                    }
                ]
            }],
            max_tokens=5
        )
        answer = response.choices[0].message.content.strip().upper()
        return answer.startswith("YES")
    except Exception as e:
        print(f"Image validation failed: {e}", flush=True)
        return True  # fail open — don't block if validation itself errors

def analyze_dress_damage(image_file, original_image_file=None):
    """Call Groq Vision API to analyze dress damage.
    If original_image_file is provided, compares returned dress against original.
    """
    try:
        return_mime = image_file.content_type or 'image/jpeg'
        return_data = base64.b64encode(image_file.read()).decode('utf-8')

        if original_image_file:
            # ── Two-image comparison mode ──────────────────────────────────────
            orig_mime     = original_image_file.content_type or 'image/jpeg'
            original_data = base64.b64encode(original_image_file.read()).decode('utf-8')
            content = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{orig_mime};base64,{original_data}"}
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{return_mime};base64,{return_data}"}
                },
                {
                    "type": "text",
                    "text": (
                        "You are a strict professional dress rental damage inspector. "
                        "IMAGE 1 is the ORIGINAL dress as it was when rented out. "
                        "IMAGE 2 is the dress as returned by the customer. "
                        "\n\n"
                        "Your job: carefully compare the two images and identify NEW damage on the returned dress "
                        "that was NOT present in the original. Look specifically for:\n"
                        "- Stains (food, drink, makeup, dirt)\n"
                        "- Tears or rips in the fabric\n"
                        "- Holes (new ones not part of the original design)\n"
                        "- Missing embellishments (sequins, beads, buttons, straps)\n"
                        "- Burns or scorch marks\n"
                        "- Fading or discolouration not in the original\n"
                        "- Structural damage (broken boning, collapsed shape)\n"
                        "\n"
                        "IMPORTANT RULES:\n"
                        "- Cutouts, fringe, feathers, sheer panels, or decorative holes that appear in the ORIGINAL are part of the design — do NOT flag these as damage.\n"
                        "- Only flag differences that are clearly NEW damage not present in the original.\n"
                        "- Be strict: if in doubt whether something is design or damage, compare closely with the original.\n"
                        "- damage_percentage represents how much of the dress surface is affected (0 = none, 100 = total loss).\n"
                        "\n"
                        "Reply with ONLY valid JSON — no markdown, no preamble. "
                        'Format: {"damage_percentage": 0-100, "is_damaged": true or false, '
                        '"severity": "none" or "mild" or "moderate" or "severe", '
                        '"description": "2-3 sentences: list each type of damage found and where on the dress it appears, or state no new damage found compared to original"}'
                    )
                }
            ]
        else:
            # ── Single-image fallback mode ─────────────────────────────────────
            content = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{return_mime};base64,{return_data}"}
                },
                {
                    "type": "text",
                    "text": (
                        "You are a strict professional dress rental damage inspector. "
                        "Analyze this returned rental dress image for damage. Look specifically for:\n"
                        "- Stains (food, drink, makeup, dirt)\n"
                        "- Tears or rips in the fabric\n"
                        "- Holes not part of the original design\n"
                        "- Missing embellishments (sequins, beads, buttons)\n"
                        "- Burns, fading, or discolouration\n"
                        "- Structural damage\n"
                        "\n"
                        "damage_percentage represents how much of the dress surface is affected (0 = none, 100 = total loss). "
                        "Reply with ONLY valid JSON — no markdown, no preamble. "
                        'Format: {"damage_percentage": 0-100, "is_damaged": true or false, '
                        '"severity": "none" or "mild" or "moderate" or "severe", '
                        '"description": "2-3 sentences describing the damage found and where on the dress, or state no damage detected"}'
                    )
                }
            ]

        response = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": content}],
            max_tokens=400
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        ai_result = json.loads(raw)
        return ai_result

    except Exception as e:
        print(f"Groq analysis failed: {e}")
        return {
            "damage_percentage": 35,
            "is_damaged": True,
            "severity": "moderate",
            "description": "Groq temporarily unavailable - demo mode"
        }

# Fee calculation
def calculate_damage_fee(damage_percent):
    if damage_percent <= 5:
        return 0.0
    elif damage_percent <= 25:
        return 100.0
    elif damage_percent <= 50:
        return 150.0
    elif damage_percent <= 75:
        return 175.0
    else:
        return 200.0

# ── Endpoints ──────────────────────────────────────────

@app.route("/assessment/image", methods=["POST"])
def create_ai_assessment():
    """
    Create an AI-based return assessment from uploaded dress images
    ---
    tags:
      - Return Assessment
    requestBody:
      required: true
      content:
        multipart/form-data:
          schema:
            type: object
            required:
              - image
              - rental_id
            properties:
              image:
                type: string
                format: binary
                description: Image of the returned dress
              original_image:
                type: string
                format: binary
                description: Optional original dress image for comparison
              rental_id:
                type: integer
                example: 1001
              dress_id:
                type: integer
                example: 101
              end_date:
                type: string
                format: date
                example: "2026-04-07"
    responses:
      201:
        description: Assessment created successfully
      400:
        description: Missing file or rental ID, no image selected, or uploaded image is not a dress
      500:
        description: Assessment failed
    """
    if 'image' not in request.files or 'rental_id' not in request.form:
        return jsonify({"code": 400, "message": "Missing image file or rental_id"}), 400

    rental_id  = int(request.form['rental_id'])
    dress_id   = int(request.form.get('dress_id', 0))
    end_date   = request.form.get('end_date', '')

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"code": 400, "message": "No image selected"}), 400

    original_image_file = request.files.get('original_image')  # optional

    # ── Pre-check: is the uploaded image actually a dress? ────────────────────
    image_file.seek(0)
    return_mime       = image_file.content_type or 'image/jpeg'
    return_data_check = base64.b64encode(image_file.read()).decode('utf-8')
    image_file.seek(0)  # reset for full analysis below

    if not is_dress_image(return_data_check, return_mime):
        return jsonify({
            "code": 400,
            "message": "not_a_dress",
            "detail": "The uploaded image does not appear to be a dress. Please upload a photo of the dress."
        }), 400

    if original_image_file:
        original_image_file.seek(0)
    is_late = calculate_is_late(end_date) if end_date else False

    try:
        ai_result = analyze_dress_damage(image_file, original_image_file)

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=False)