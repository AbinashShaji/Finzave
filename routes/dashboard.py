from flask import render_template, redirect, url_for, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from extensions import db, cache
from models.user import User
from models.income import Income
from models.expense import Expense
from sqlalchemy import func
from datetime import datetime
import json
from utils.finance import get_monthly_income

@app_bp.route('/')
@jwt_required()
def dashboard():
    return render_template('app/dashboard.html')

@app_bp.route('/dashboard/data', methods=['GET'])
@jwt_required()
def dashboard_data():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    # Get current month data
    now = datetime.utcnow()
    current_year = now.year
    current_month = now.month
    
    total_income = get_monthly_income(user_id, current_year, current_month)
    
    total_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        func.extract('year', Expense.date) == current_year,
        func.extract('month', Expense.date) == current_month
    ).scalar() or 0.0
    
    savings = total_income - total_expenses
    savings_rate = (savings / total_income * 100) if total_income > 0 else None
    
    return jsonify({
        "total_income": total_income,
        "total_expenses": total_expenses,
        "savings": savings,
        "savings_rate": savings_rate
    }), 200
