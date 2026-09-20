from flask import render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from planning.sip import calculate_sip
from planning.emi import calculate_emi
from planning.insights import generate_planning_insight
from utils.finance import build_financial_periods

@app_bp.route('/planning')
@jwt_required()
def planning():
    return render_template('app/planning.html')

def get_current_savings(user_id):
    periods = build_financial_periods(user_id, months=1)
    if periods:
        return periods[0].savings
    return None

@app_bp.route('/api/planning/calculate_sip', methods=['POST'])
@jwt_required()
def api_calculate_sip():
    user_id = int(get_jwt_identity())
    data = request.json
    try:
        if 'monthly_investment' not in data or 'annual_rate' not in data or 'years' not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        monthly_investment = float(data.get('monthly_investment', 0))
        annual_rate = float(data.get('annual_rate', 0))
        years = int(data.get('years', 0))
        
        if monthly_investment < 0 or annual_rate < 0 or years < 0:
            return jsonify({"error": "Values cannot be negative"}), 400
            
        result = calculate_sip(monthly_investment, annual_rate, years)
        
        savings = get_current_savings(user_id)
        if savings is not None:
            insight = generate_planning_insight(monthly_investment, savings, "SIP")
            result["insight"] = insight
        
        return jsonify(result), 200
    except ValueError:
        return jsonify({"error": "Invalid numeric input"}), 400
    except Exception as e:
        return jsonify({"error": "Failed to calculate SIP"}), 400

@app_bp.route('/api/planning/calculate_emi', methods=['POST'])
@jwt_required()
def api_calculate_emi():
    user_id = int(get_jwt_identity())
    data = request.json
    try:
        if 'principal' not in data or 'annual_rate' not in data or 'years' not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        principal = float(data.get('principal', 0))
        annual_rate = float(data.get('annual_rate', 0))
        years = int(data.get('years', 0))
        
        if principal < 0 or annual_rate < 0 or years < 0:
            return jsonify({"error": "Values cannot be negative"}), 400
            
        result = calculate_emi(principal, annual_rate, years)
        
        savings = get_current_savings(user_id)
        if savings is not None:
            insight = generate_planning_insight(result.get("monthly_emi", 0), savings, "EMI")
            result["insight"] = insight
        
        return jsonify(result), 200
    except ValueError:
        return jsonify({"error": "Invalid numeric input"}), 400
    except Exception as e:
        return jsonify({"error": "Failed to calculate EMI"}), 400
