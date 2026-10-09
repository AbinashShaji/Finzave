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
from utils.finance import build_financial_periods
from utils.rule_engine import evaluate_rules
from analysis.scoring import calculate_health_score
from utils.pdf_generator import generate_financial_report_pdf
from models.expense import Expense
import csv
import io
from utils.activity import log_activity

@app_bp.route('/reports')
@jwt_required()
def reports():
    user_id = int(get_jwt_identity())
    log_activity('reports_view')
    periods = build_financial_periods(user_id, months=6)
    
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
        writer.writerow([ex.date.strftime('%Y-%m-%d'), ex.category, f"{ex.amount:.2f}", ex.description or ''])
        
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
    periods = build_financial_periods(user_id, months=6)
    
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
    
    pdf_bytes = generate_financial_report_pdf(current_period, health_data)
    
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-disposition": f"attachment; filename=finzave_report_{current_period.period_id}.pdf"}
    )
