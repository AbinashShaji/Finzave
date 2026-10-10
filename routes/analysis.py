"""
Module: routes/analysis.py

Purpose:
Handles HTTP requests, route definitions, and view controllers.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
from flask import render_template, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from utils.finance import build_financial_periods
from utils.financial_metrics import calculate_period_metrics
from utils.rule_engine import evaluate_rules
from analysis.scoring import calculate_health_score
from analysis.services import build_overview, build_monthly_analysis, build_yearly_analysis
from extensions import db, cache
from models.analysis import Analysis
from models.goal import Goal
from utils.cache_keys import user_analysis_key, user_analysis_monthly_key, user_analysis_yearly_key
from routes.goals import prepare_goals_data
from recommendations import generate_recommendations
from utils.activity import log_activity
import json


@app_bp.route('/analysis')
@jwt_required()
@cache.cached(timeout=86400, key_prefix=lambda: user_analysis_key(get_jwt_identity()))
def analysis():
    user_id = int(get_jwt_identity())
    log_activity('analysis_view')

    # 1. Fetch Financial Data
    periods = build_financial_periods(user_id, months=12)

    # 2. Pipeline Calculations
    metrics = calculate_period_metrics(periods)
    insights = evaluate_rules(periods)
    health_score = calculate_health_score(periods, metrics.get("has_data", False), insights)

    # 3. Build overview data from services
    overview = build_overview(periods)

    # 4. Database Persistence
    current_period_id = periods[-1].period_id if periods else "NO_DATA"
    if current_period_id != "NO_DATA":
        analysis_record = Analysis.query.filter_by(user_id=user_id, period=current_period_id).first()
        if not analysis_record:
            analysis_record = Analysis(user_id=user_id, period=current_period_id)
            db.session.add(analysis_record)

        analysis_record.metrics = metrics
        analysis_record.insights = insights
        analysis_record.health_score = health_score
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Error saving analysis record: {e}")

    # 5. Generate Recommendations
    user_goals = db.session.query(Goal).filter_by(user_id=user_id).all()
    active_goals, completed_goals = prepare_goals_data(user_goals)

    prepared_goals = []
    for g in active_goals:
        prepared_goals.append({
            "goal_name": g.get("goal_name") if isinstance(g, dict) else getattr(g, "goal_name", ""),
            "status": g.get("status") if isinstance(g, dict) else getattr(g, "status", ""),
            "req_monthly": g.get("req_monthly") if isinstance(g, dict) else getattr(g, "req_monthly", 0)
        })

    if metrics.get('has_data'):
        recommendations = generate_recommendations(insights, prepared_goals, metrics, health_score)
    else:
        recommendations = []

    # 6. Chart data for template
    chart_data = {
        "labels": [p.period_id for p in periods],
        "income": [p.total_income for p in periods],
        "expenses": [p.total_expenses for p in periods],
    }

    # 7. Render Template
    return render_template(
        'app/analysis.html',
        overview=overview,
        metrics=metrics,
        insights=insights,
        health_score=health_score,
        recommendations=recommendations,
        chart_data=chart_data,
    )


@app_bp.route('/analysis/monthly')
@jwt_required()
@cache.cached(timeout=86400, key_prefix=lambda: user_analysis_monthly_key(get_jwt_identity()))
def analysis_monthly():
    user_id = int(get_jwt_identity())

    periods = build_financial_periods(user_id, months=12)
    monthly = build_monthly_analysis(periods)
    insights = evaluate_rules(periods)

    return render_template(
        'app/analysis_monthly.html',
        monthly=monthly,
        insights=insights,
        chart_data=monthly.get("chart_data", {}),
    )


@app_bp.route('/analysis/yearly')
@jwt_required()
@cache.cached(timeout=86400, key_prefix=lambda: user_analysis_yearly_key(get_jwt_identity()))
def analysis_yearly():
    user_id = int(get_jwt_identity())

    periods = build_financial_periods(user_id, months=12)
    yearly = build_yearly_analysis(periods)

    return render_template(
        'app/analysis_yearly.html',
        yearly=yearly,
        chart_data=yearly.get("chart_data", {}),
    )
