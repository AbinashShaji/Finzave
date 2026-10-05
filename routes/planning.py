from flask import render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from planning.sip import calculate_sip
from planning.emi import calculate_emi
from planning.insights import generate_planning_insight
from utils.finance import build_financial_periods
from utils.activity import log_activity

@app_bp.route('/planning')
@jwt_required()
def planning():
    log_activity('planning_view')
    return render_template('app/planning.html')

def get_current_savings(user_id):
    periods = build_financial_periods(user_id, months=1)
    if periods:
        return periods[0].savings
    return None

@app_bp.route('/api/planning/capacity', methods=['GET'])
@jwt_required()
def api_planning_capacity():
    user_id = int(get_jwt_identity())
    periods = build_financial_periods(user_id, months=1)
    if not periods:
        return jsonify({"savings": 0, "income": 0, "suggested_sip_min": 0, "suggested_sip_max": 0}), 200
    
    savings = periods[0].savings
    income = periods[0].total_income
    
    suggested_min = savings * 0.30 if savings > 0 else 0
    suggested_max = savings * 0.50 if savings > 0 else 0
    
    return jsonify({
        "savings": savings,
        "income": income,
        "suggested_sip_min": suggested_min,
        "suggested_sip_max": suggested_max
    }), 200

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
        
        log_activity('plan_created')
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
            
        loan_type = data.get('loan_type', 'Personal')
        years = int(data.get('years', 0))
        annual_rate = float(data.get('annual_rate', 0))
        
        if loan_type in ['Car', 'Bike']:
            vehicle_price = float(data.get('vehicle_price', 0))
            down_payment = float(data.get('down_payment', 0))
            principal = max(0, vehicle_price - down_payment)
        else:
            principal = float(data.get('principal', 0))
        
        if principal < 0 or annual_rate < 0 or years < 0:
            return jsonify({"error": "Values cannot be negative"}), 400
            
        result = calculate_emi(principal, annual_rate, years)
        
        savings = get_current_savings(user_id)
        if savings is not None:
            insight = generate_planning_insight(result.get("monthly_emi", 0), savings, "EMI")
            result["insight"] = insight
        
        log_activity('plan_created')
        return jsonify(result), 200
    except ValueError:
        return jsonify({"error": "Invalid numeric input"}), 400
    except Exception as e:
        return jsonify({"error": "Failed to calculate EMI"}), 400
