"""
Module: routes/reports.py

Purpose:
Handles HTTP requests, route definitions, and view controllers.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
from flask import render_template, request, Response, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from extensions import db
from utils.finance import build_financial_periods, get_active_fixed_incomes
from utils.rule_engine import evaluate_rules
from analysis.scoring import calculate_health_score
from utils.pdf_generator import generate_financial_report_pdf
from models.expense import Expense
from models.income import Income
from models.goal import Goal
from routes.goals import prepare_goals_data
from recommendations import generate_recommendations
from utils.financial_metrics import calculate_period_metrics
from analysis.services import build_overview
from sqlalchemy import func
from datetime import date
import calendar
import csv
import io
from utils.activity import log_activity
from utils.hash_utils import sanitize_csv_value

@app_bp.route('/reports')
@jwt_required()
def reports():
    user_id = int(get_jwt_identity())
    log_activity('reports_view')
    periods = build_financial_periods(user_id, months=12)
    
    # We need global has_data to know if user has ANY data ever
    has_data = any((p.total_income > 0 or p.total_expenses > 0) for p in periods)
    
    selected_period = request.args.get('period')
    current_period = None
    
    if selected_period:
        for p in periods:
            if p.period_id == selected_period:
                current_period = p
                break
        if not current_period:
            return "Invalid period selected", 400
                
    if not current_period:
        current_period = periods[-1] if periods else None
        
    current_has_data = False
    if current_period:
        current_has_data = (current_period.total_income > 0 or current_period.total_expenses > 0)
        
    # Get historical periods up to the current period for accurate rule engine evaluation
    historical_periods = []
    if current_period:
        idx = periods.index(current_period)
        historical_periods = periods[:idx+1]
        
    insights = evaluate_rules(historical_periods)
    health_data = calculate_health_score(historical_periods, current_has_data, insights)
    
    return render_template(
        'app/reports.html',
        has_data=has_data,
        current_has_data=current_has_data,
        current_period=current_period,
        health_data=health_data,
        periods=periods
    )

@app_bp.route('/api/reports/export/csv', methods=['GET'])
@jwt_required()
def export_csv():
    user_id = int(get_jwt_identity())
    log_activity('report_generated')
    
    expenses = db.session.query(Expense).filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Category', 'Amount', 'Description'])
    
    for ex in expenses:
        writer.writerow([
            sanitize_csv_value(ex.date.strftime('%Y-%m-%d')),
            sanitize_csv_value(ex.category),
            f"{ex.amount:.2f}",
            sanitize_csv_value(ex.description or '')
        ])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=transactions_export.csv"}
    )

@app_bp.route('/api/reports/export/pdf', methods=['GET'])
@jwt_required()
def export_pdf():
    user_id = int(get_jwt_identity())
    log_activity('report_generated')
    periods = build_financial_periods(user_id, months=12)
    
    selected_period = request.args.get('period')
    current_period = None
    
    if selected_period:
        for p in periods:
            if p.period_id == selected_period:
                current_period = p
                break
        if not current_period:
            return "Invalid period selected", 400
            
    if not current_period:
        current_period = periods[-1] if periods else None
        
    if not current_period:
        return "No financial data available to generate report", 400
        
    current_has_data = (current_period.total_income > 0 or current_period.total_expenses > 0)
    
    idx = periods.index(current_period)
    historical_periods = periods[:idx+1]
        
    insights = evaluate_rules(historical_periods)
    health_data = calculate_health_score(historical_periods, current_has_data, insights)
    
    # 1. Overview and savings insights
    overview = build_overview(historical_periods)
    
    # 2. Financial Goals
    user_goals = db.session.query(Goal).filter_by(user_id=user_id).order_by(Goal.created_at.desc()).all()
    active_goals, completed_goals = prepare_goals_data(user_goals)
    all_goals = active_goals + completed_goals
    
    # 3. Recommendations
    metrics = calculate_period_metrics(historical_periods)
    prepared_goals = [
        {
            "goal_name": g.get("goal_name", ""),
            "status": g.get("status", ""),
            "req_monthly": g.get("req_monthly", 0)
        }
        for g in active_goals
    ]
    if metrics.get('has_data'):
        recommendations = generate_recommendations(insights, prepared_goals, metrics, health_data)
    else:
        recommendations = []
        
    # 4. Income Sources breakdown
    income_sources = []
    try:
        p_parts = current_period.period_id.split('-')
        p_year, p_month = int(p_parts[0]), int(p_parts[1])
        
        var_incomes = db.session.query(Income).filter(
            Income.user_id == user_id,
            Income.income_type == 'Variable',
            func.extract('year', Income.date) == p_year,
            func.extract('month', Income.date) == p_month
        ).all()
        
        last_day = calendar.monthrange(p_year, p_month)[1]
        end_of_month_date = date(p_year, p_month, last_day)
        active_fixed = get_active_fixed_incomes(user_id, end_of_month_date).get('active_records', [])
        
        for f in active_fixed:
            desc = f.get('description') or "Fixed Salary / Income"
            amt = float(f.get('amount') or 0.0)
            if amt > 0:
                income_sources.append({
                    "source": desc,
                    "type": "Fixed",
                    "amount": amt
                })
        for v in var_incomes:
            desc = v.description or "Variable Inflow"
            amt = float(v.amount or 0.0)
            if amt > 0:
                income_sources.append({
                    "source": desc,
                    "type": "Variable",
                    "amount": amt
                })
    except Exception:
        income_sources = []
        
    # 5. Historical Health Scores
    historical_scores = {}
    for i, p in enumerate(historical_periods):
        sub_periods = historical_periods[:i+1]
        sub_has_data = (p.total_income > 0 or p.total_expenses > 0)
        sub_insights = evaluate_rules(sub_periods)
        historical_scores[p.period_id] = calculate_health_score(sub_periods, sub_has_data, sub_insights)
    
    pdf_bytes = generate_financial_report_pdf(
        period=current_period,
        health_data=health_data,
        historical_periods=historical_periods,
        overview=overview,
        goals=all_goals,
        recommendations=recommendations,
        income_sources=income_sources,
        historical_scores=historical_scores
    )
    
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-disposition": f"attachment; filename=finzave_report_{current_period.period_id}.pdf"}
    )

