from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import date

app = Flask(__name__)
CORS(app)
app.config['TRUSTED_HOSTS'] = None

# ─── ATOMIC SERVICE URLS ──────────────────────────────────────────────────────
RENTAL_URL            = os.environ.get('RENTAL_URL',            'http://localhost:5004')
INVENTORY_URL         = os.environ.get('INVENTORY_URL',         'http://localhost:5001')
RETURN_ASSESSMENT_URL = os.environ.get('RETURN_ASSESSMENT_URL', 'http://localhost:5006')
INVOICE_URL           = os.environ.get('INVOICE_URL',           'http://localhost:5005')


# ─── UC4: LOG RETURN WITH AI DAMAGE ASSESSMENT ───────────────────────────────
#
# Flow:
#   1. GET   rental info                  → Rental Service
#   2. Calculate late fee ($15/day)
#   3. POST  image to AI assessment       → Return Assessment Service
#   4. POST  penalty invoice (if any)     → Invoice Service
#   5. PUT   dress available              → Inventory Service
#   6. PUT   rental status → COMPLETED   → Rental Service
#   7. Return invoice data to UI

@app.route("/return/rental/<int:rental_id>", methods=['GET'])
def get_rental(rental_id):
    try:
        response = requests.get(f"{RENTAL_URL}/rental/{rental_id}", timeout=5)
        data = response.json()
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Failed to reach rental service: {str(e)}"
        }), 500

    if response.status_code != 200:
        return jsonify({
            "code": response.status_code,
            "message": data.get("message", f"Rental {rental_id} not found.")
        }), response.status_code

    return jsonify({
        "code": 200,
        "data": data.get("data", {})
    }), 200


@app.route("/return/image", methods=['POST'])
def log_return_with_image():
    """
    Expected multipart/form-data:
    - rental_id:   int  (form field)
    - return_date: str  YYYY-MM-DD (form field)
    - image:       file
    """
    rental_id_str = request.form.get('rental_id')
    return_date_str = request.form.get('return_date')
    image_file = request.files.get('image')

    if not rental_id_str or not image_file:
        return jsonify({"code": 400, "message": "Missing rental_id or image"}), 400

    rental_id = int(rental_id_str)

    # ── Step 1: Get rental info ───────────────────────────────────────────────
    try:
        rental_resp = requests.get(f"{RENTAL_URL}/rental/{rental_id}")
        rental_data = rental_resp.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Rental service error: {str(e)}"}), 500

    if rental_resp.status_code != 200:
        return jsonify({"code": 404, "message": f"Rental {rental_id} not found."}), 404

    rental   = rental_data["data"]
    dress_id = rental["dress_id"]
    end_date = rental["end_date"]   # "YYYY-MM-DD"

    # ── Step 2: Calculate late fee ($15/day) ──────────────────────────────────
    return_dt = date.fromisoformat(return_date_str) if return_date_str else date.today()
    end_dt    = date.fromisoformat(end_date)
    days_late = max(0, (return_dt - end_dt).days)
    late_fee  = days_late * 15.0

    # ── Step 2b: Load original dress image from mounted volume ────────────────
    original_image_bytes  = None
    original_content_type = 'image/jpeg'
    try:
        inv_resp = requests.get(f"{INVENTORY_URL}/inventory/{dress_id}")
        if inv_resp.status_code == 200:
            img_path = inv_resp.json()["data"].get("img", "")  # e.g. /images/dress_blue.jpeg
            if img_path:
                # img_path is like "/images/dress_blue.jpeg" — mounted at /images inside container
                local_path = img_path  # already maps to the mounted volume path
                with open(local_path, 'rb') as f:
                    original_image_bytes = f.read()
    except Exception:
        pass  # proceed without original; AI will fall back to single-image analysis

    # ── Step 3: Forward image(s) to Return Assessment Service ─────────────────
    image_bytes = image_file.read()
    files = {'image': (image_file.filename, image_bytes, image_file.content_type)}
    if original_image_bytes:
        files['original_image'] = ('original.jpg', original_image_bytes, original_content_type)

    try:
        assessment_resp = requests.post(
            f"{RETURN_ASSESSMENT_URL}/assessment/image",
            data={
                'rental_id': str(rental_id),
                'dress_id':  str(dress_id),
                'end_date':  end_date,
            },
            files=files
        )
        assessment_data = assessment_resp.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Assessment service error: {str(e)}"}), 500

    if assessment_resp.status_code != 201:
        # Pass through not_a_dress error directly to the frontend
        msg = assessment_data.get("message", "Failed to create return assessment.")
        return jsonify({"code": 400, "message": msg}), 400

    assess             = assessment_data["data"]
    is_damaged         = assess["is_damaged"]
    damage_fee         = assess["damage_fee"]
    damage_description = assess.get("damage_description", "No damage detected")
    total_penalty      = late_fee + damage_fee

    # ── Step 4: Create penalty invoice if needed ──────────────────────────────
    if total_penalty > 0:
        try:
            requests.post(
                f"{INVOICE_URL}/invoice",
                json={"rental_id": rental_id, "amount": total_penalty, "type": "PENALTY"}
            )
        except Exception as e:
            pass  # non-critical for the return flow

    # ── Step 5: Update dress availability ────────────────────────────────────
    try:
        requests.put(
            f"{INVENTORY_URL}/inventory/{dress_id}",
            json={"is_available": True}
        )
    except Exception:
        pass

    # ── Step 6: Mark rental COMPLETED ────────────────────────────────────────
    try:
        requests.put(
            f"{RENTAL_URL}/rental/{rental_id}",
            json={"status": "COMPLETED"}
        )
    except Exception as e:
        return jsonify({"code": 500, "message": f"Failed to update rental: {str(e)}"}), 500

    # ── Step 7: Return invoice data to UI ────────────────────────────────────
    return jsonify({
        "code": 200,
        "data": {
            "rental_id":          rental_id,
            "dress_id":           dress_id,
            "is_damaged":         is_damaged,
            "damage_fee":         damage_fee,
            "days_late":          days_late,
            "late_fee":           late_fee,
            "total_penalty":      total_penalty,
            "damage_description": damage_description,
            "status":             "COMPLETED"
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5012, debug=False)