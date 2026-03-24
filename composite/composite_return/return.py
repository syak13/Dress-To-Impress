from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ─── ATOMIC SERVICE URLS ──────────────────────────────────────────────────────
RENTAL_URL            = os.environ.get('RENTAL_URL',            'http://localhost:5004')
INVENTORY_URL         = os.environ.get('INVENTORY_URL',         'http://localhost:5001')
RETURN_ASSESSMENT_URL = os.environ.get('RETURN_ASSESSMENT_URL', 'http://localhost:5006')
INVOICE_URL           = os.environ.get('INVOICE_URL',           'http://localhost:5005')


# ─── UC4: LOG RETURN OF DRESS ─────────────────────────────────────────────────
#
# Flow:
#   1. GET   rental information          → Rental Service
#   2. GET   dress information           → Rental Service  (dressID, size, endDate)
#   3. POST  upload return details       → Return Assessment Service
#   4. GET   back is_late + is_damaged   → Return Assessment Service
#   5. POST  calculate penalty fees      → Return Assessment Service
#   6. GET   back total penalty          → Return Assessment Service
#   7. POST  create penalty invoice      → Invoice Service  (if penalty > 0)
#   8. PUT   update dress availability   → Inventory Service (is_available: True)
#   9. PUT   update rental status        → Rental Service   (status: COMPLETED)
#   10. Return updated order to UI

@app.route("/return", methods=['POST'])
def log_return():
    """
    Expected JSON:
    {
        "rental_id": 1,
        "dress_id": 201,
        "is_damaged": true/false,
        "damage_description": "Wine stain on hem"   (optional)
    }
    """
    data = request.get_json()

    for field in ['rental_id', 'dress_id', 'is_damaged']:
        if field not in data:
            return jsonify({
                "code": 400,
                "message": f"Missing required field: {field}"
            }), 400

    rental_id         = data['rental_id']
    dress_id          = data['dress_id']
    is_damaged        = data['is_damaged']
    damage_description = data.get('damage_description', '')

    # ── Step 1+2: Get rental information + dress end_date ─────────────────────
    try:
        rental_response = requests.get(f"{RENTAL_URL}/rental/{rental_id}")
        rental_data = rental_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Rental service error: {str(e)}"}), 500

    if rental_response.status_code != 200:
        return jsonify({
            "code": 404,
            "message": f"Rental {rental_id} not found."
        }), 404

    rental   = rental_data["data"]
    end_date = rental["end_date"]

    # ── Step 3+4: Upload return details, get is_late + is_damaged ─────────────
    try:
        assessment_response = requests.post(
            f"{RETURN_ASSESSMENT_URL}/assessment",
            json={
                "rental_id":          rental_id,
                "dress_id":           dress_id,
                "end_date":           end_date,
                "is_damaged":         is_damaged,
                "damage_description": damage_description
            }
        )
        assessment_data = assessment_response.json()
    except Exception as e:
        return jsonify({"code": 500, "message": f"Assessment service error: {str(e)}"}), 500

    if assessment_response.status_code != 201:
        return jsonify({
            "code": 500,
            "message": "Failed to create return assessment."
        }), 500

    assessment    = assessment_data["data"]
    assessment_id = assessment["assessment_id"]
    is_late       = assessment["is_late"]
    is_damaged    = assessment["is_damaged"]

    # ── Step 5+6: Calculate penalty fees ──────────────────────────────────────
    # Fee rules:
    #   Late fee   → $50 flat if returned after end_date
    #   Damage fee → $150 flat if dress is damaged
    late_fee   = 50.00  if is_late    else 0.00
    damage_fee = 150.00 if is_damaged else 0.00
    total_penalty = late_fee + damage_fee

    penalty_id = None

    if total_penalty > 0:
        try:
            penalty_response = requests.post(
                f"{RETURN_ASSESSMENT_URL}/penalty",
                json={
                    "assessment_id": assessment_id,
                    "late_fee":      late_fee,
                    "damage_fee":    damage_fee
                }
            )
            penalty_data = penalty_response.json()
        except Exception as e:
            return jsonify({"code": 500, "message": f"Penalty service error: {str(e)}"}), 500

        if penalty_response.status_code != 201:
            return jsonify({
                "code": 500,
                "message": "Failed to create penalty record."
            }), 500

        penalty_id = penalty_data["data"]["penalty_id"]

        # ── Step 7: Create penalty invoice via Invoice Service ─────────────────
        try:
            invoice_response = requests.post(
                f"{INVOICE_URL}/invoice",
                json={
                    "rental_id": rental_id,
                    "amount":    total_penalty,
                    "type":      "PENALTY"
                }
            )
        except Exception as e:
            return jsonify({"code": 500, "message": f"Invoice service error: {str(e)}"}), 500

        if invoice_response.status_code != 201:
            return jsonify({
                "code": 500,
                "message": "Failed to create penalty invoice."
            }), 500

    # ── Step 8: Update dress availability in Inventory Service ────────────────
    try:
        inventory_response = requests.put(
            f"{INVENTORY_URL}/inventory/{dress_id}",
            json={"is_available": True}
        )
    except Exception as e:
        return jsonify({"code": 500, "message": f"Inventory service error: {str(e)}"}), 500

    if inventory_response.status_code != 200:
        return jsonify({
            "code": 500,
            "message": f"Failed to update inventory for dress {dress_id}."
        }), 500

    # ── Step 9: Update rental status to COMPLETED ─────────────────────────────
    try:
        update_rental_response = requests.put(
            f"{RENTAL_URL}/rental/{rental_id}",
            json={"status": "COMPLETED"}
        )
    except Exception as e:
        return jsonify({"code": 500, "message": f"Rental service error: {str(e)}"}), 500

    if update_rental_response.status_code != 200:
        return jsonify({
            "code": 500,
            "message": f"Failed to update rental {rental_id} status."
        }), 500

    # ── Step 10: Return updated order summary to UI ───────────────────────────
    return jsonify({
        "code": 200,
        "data": {
            "rental_id":     rental_id,
            "dress_id":      dress_id,
            "status":        "COMPLETED",
            "is_late":       is_late,
            "is_damaged":    is_damaged,
            "late_fee":      late_fee,
            "damage_fee":    damage_fee,
            "total_penalty": total_penalty,
            "penalty_id":    penalty_id
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5012, debug=True)