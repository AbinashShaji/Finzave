from flask import render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from utils.finance import build_financial_periods
from utils.rule_engine import evaluate_rules
from analysis.scoring import calculate_health_score
import json

@app_bp.route('/analysis')
@jwt_required()
def analysis():
    user_id = int(get_jwt_identity())
    
    # Get last 6 months of data
    periods = build_financial_periods(user_id, months=6)
    
    insights = evaluate_rules(periods)
    
    current_period = periods[-1] if periods else None
    
    health_data = calculate_health_score(current_period, insights)
    
    # Prepare data for Chart.js
    chart_labels = [p.period_id for p in periods]
    chart_income = [p.total_income for p in periods]
    chart_expenses = [p.total_expenses for p in periods]
    chart_savings = [p.savings for p in periods]
    
    # Current month category distribution for Doughnut chart
    category_labels = []
    category_data = []
    if current_period:
        for cat, amt in current_period.categories.items():
            category_labels.append(cat)
            category_data.append(amt)
            
    # Calculate prev month changes
    income_change = 0
    expense_change = 0
    savings_change = 0
    if len(periods) >= 2:
        prev = periods[-2]
        curr = periods[-1]
        if prev.total_income > 0:
            income_change = ((curr.total_income - prev.total_income) / prev.total_income) * 100
        if prev.total_expenses > 0:
            expense_change = ((curr.total_expenses - prev.total_expenses) / prev.total_expenses) * 100
        if prev.savings > 0: # Note: savings could be negative
            savings_change = ((curr.savings - prev.savings) / abs(prev.savings)) * 100

    has_data = len(periods) > 0 and any(p.total_income > 0 or p.total_expenses > 0 for p in periods)

    return render_template(
        'app/analysis.html',
        has_data=has_data,
        current_period=current_period,
        health_data=health_data,
        insights=insights,
        income_change=round(income_change, 1),
        expense_change=round(expense_change, 1),
        savings_change=round(savings_change, 1),
        chart_data=json.dumps({
            'labels': chart_labels,
            'income': chart_income,
            'expenses': chart_expenses,
            'savings': chart_savings,
            'cat_labels': category_labels,
            'cat_data': category_data
        })
    )
