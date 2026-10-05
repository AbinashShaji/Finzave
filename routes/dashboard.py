from flask import render_template, redirect, url_for, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from extensions import db
from models.user import User
from models.expense import Expense
from utils.finance import build_financial_periods
from utils.rule_engine import evaluate_rules
from analysis.scoring import calculate_health_score
import json

from utils.activity import log_activity

@app_bp.route('/')
@jwt_required()
def dashboard():
    user_id = int(get_jwt_identity())
    log_activity('dashboard_view')
    
    # Use the same data adapter
    periods = build_financial_periods(user_id, months=6)
    
    # We need has_data for scoring calculation
    has_data = any((p.total_income > 0 or p.total_expenses > 0) for p in periods)
    
    insights = evaluate_rules(periods)
    current_period = periods[-1] if periods else None
    
    # Fix P0 Bug: Update signature to match analysis.py
    health_data = calculate_health_score(periods, has_data, insights)
    
    # Recent transactions
    recent_expenses = db.session.query(Expense).filter_by(user_id=user_id).order_by(Expense.date.desc()).limit(5).all()
    
    # Chart data
    category_labels = []
    category_data = []
    if current_period:
        for cat, amt in current_period.categories.items():
            category_labels.append(cat)
            category_data.append(amt)
            
    return render_template(
        'app/dashboard.html',
        has_data=has_data,
        current_period=current_period,
        health_data=health_data,
        insights=insights,
        recent_expenses=recent_expenses,
        chart_data=json.dumps({
            'cat_labels': category_labels,
            'cat_data': category_data
        })
    )


