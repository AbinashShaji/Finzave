from flask import render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from utils.finance import build_financial_periods
from utils.financial_metrics import calculate_period_metrics
from utils.rule_engine import evaluate_rules
from analysis.scoring import calculate_health_score
from extensions import db, cache
from models.analysis import Analysis
from models.goal import Goal
from utils.cache_keys import user_analysis_key
from routes.goals import prepare_goals_data
from recommendations import generate_recommendations

@app_bp.route('/analysis')
@jwt_required()
@cache.cached(timeout=86400, key_prefix=lambda: user_analysis_key(get_jwt_identity()))
def analysis():
    user_id = int(get_jwt_identity())
    
    # 1. Fetch Financial Data
    periods = build_financial_periods(user_id, months=6)
    
    # 2. Pipeline Calculations
    metrics = calculate_period_metrics(periods)
    insights = evaluate_rules(periods)
    health_score = calculate_health_score(periods, metrics.get("has_data", False), insights)
    
    # 3. Database Persistence
    current_period_id = periods[-1].period_id if periods else "NO_DATA"
    if current_period_id != "NO_DATA":
        analysis_record = Analysis.query.filter_by(user_id=user_id, period=current_period_id).first()
        if not analysis_record:
            analysis_record = Analysis(user_id=user_id, period=current_period_id)
            db.session.add(analysis_record)
            
        analysis_record.metrics = metrics
        analysis_record.insights = insights
        analysis_record.health_score = health_score
        db.session.commit()
        
    # 4. Generate Recommendations (Phase 9)
    # Fetch user goals to pass into recommendation engine
    user_goals = db.session.query(Goal).filter_by(user_id=user_id).all()
    active_goals, completed_goals = prepare_goals_data(user_goals)
    
    # Convert active goals to simple dicts for the pure function engine
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
    
    # 5. Render Template
    return render_template(
        'app/analysis.html',
        metrics=metrics,
        insights=insights,
        health_score=health_score,
        recommendations=recommendations
    )
