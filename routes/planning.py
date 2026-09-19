from flask import render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from planning.sip import calculate_sip
from planning.emi import calculate_emi

@app_bp.route('/planning')
@jwt_required()
def planning():
    return render_template('app/planning.html')

@app_bp.route('/api/planning/calculate_sip', methods=['POST'])
@jwt_required()
def api_calculate_sip():
    data = request.json
    try:
        monthly_investment = float(data.get('monthly_investment', 0))
        annual_rate = float(data.get('annual_rate', 0))
        years = int(data.get('years', 0))
        
        result = calculate_sip(monthly_investment, annual_rate, years)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Invalid input", "msg": str(e)}), 400

@app_bp.route('/api/planning/calculate_emi', methods=['POST'])
@jwt_required()
def api_calculate_emi():
    data = request.json
    try:
        principal = float(data.get('principal', 0))
        annual_rate = float(data.get('annual_rate', 0))
        years = int(data.get('years', 0))
        
        result = calculate_emi(principal, annual_rate, years)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Invalid input", "msg": str(e)}), 400
