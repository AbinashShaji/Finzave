"""
Module: routes/planning.py

Purpose:
Handles HTTP requests, route definitions, and view controllers.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
from flask import render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from planning.sip import calculate_sip
from planning.emi import calculate_emi
from planning.insights import generate_planning_insight
from planning.services import calculate_planning_capacity, calculate_loan_affordability
from utils.finance import build_financial_periods
from utils.activity import log_activity

@app_bp.route('/planning')
@jwt_required()
def planning():
    user_id = int(get_jwt_identity())
    log_activity('planning_view')
    try:
        periods = build_financial_periods(user_id, 12, for_analysis=True)
    except TypeError:
        periods = build_financial_periods(user_id, 12)
    capacity = calculate_planning_capacity(periods)
    return render_template('app/planning.html', capacity=capacity)

def get_current_savings(user_id):
    try:
        periods = build_financial_periods(user_id, 12, for_analysis=True)
    except TypeError:
        periods = build_financial_periods(user_id, 12)
    capacity = calculate_planning_capacity(periods)
    if capacity.get("has_history"):
        return capacity.get("average_savings_capacity", 0.0)
    return None

@app_bp.route('/api/planning/capacity', methods=['GET'])
@jwt_required()
def api_planning_capacity():
    user_id = int(get_jwt_identity())
    try:
        periods = build_financial_periods(user_id, 12, for_analysis=True)
    except TypeError:
        periods = build_financial_periods(user_id, 12)
    
    capacity_data = calculate_planning_capacity(periods)
    return jsonify(capacity_data), 200

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
        
        try:
            periods = build_financial_periods(user_id, 12, for_analysis=True)
        except TypeError:
            periods = build_financial_periods(user_id, 12)
        capacity = calculate_planning_capacity(periods)
        
        if capacity.get("has_history"):
            monthly_income = float(capacity.get("average_monthly_income", 0.0) or capacity.get("income", 0.0) or 0.0)
            monthly_savings = float(capacity.get("average_savings_capacity", 0.0))
            affordability = calculate_loan_affordability(
                monthly_income=monthly_income,
                monthly_emi=result.get("monthly_emi", 0.0),
                monthly_savings=monthly_savings
            )
            result["loan_affordability"] = affordability
            result["insight"] = affordability
        
        log_activity('plan_created')
        return jsonify(result), 200
    except ValueError:
        return jsonify({"error": "Invalid numeric input"}), 400
    except Exception as e:
        return jsonify({"error": "Failed to calculate EMI"}), 400
