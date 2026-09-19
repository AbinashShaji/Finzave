from flask import render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from extensions import db
from models.goal import Goal
from datetime import datetime

@app_bp.route('/goals')
@jwt_required()
def goals():
    user_id = int(get_jwt_identity())
    user_goals = db.session.query(Goal).filter_by(user_id=user_id).order_by(Goal.target_date.asc()).all()
    
    active_goals = [g for g in user_goals if g.current_saved < g.target_amount]
    completed_goals = [g for g in user_goals if g.current_saved >= g.target_amount]
    total_saved = sum(g.current_saved for g in user_goals)
    
    from datetime import date
    today = date.today()
    for g in active_goals:
        months_left = max(1, (g.target_date.year - today.year) * 12 + g.target_date.month - today.month)
        g.req_monthly = (g.target_amount - g.current_saved) / months_left
        g.completion_pct = (g.current_saved / g.target_amount * 100) if g.target_amount > 0 else 0
        
    for g in completed_goals:
        g.completion_pct = 100
    
    return render_template(
        'app/goals.html',
        active_goals=active_goals,
        completed_goals=completed_goals,
        total_saved=total_saved
    )

@app_bp.route('/api/goals', methods=['POST'])
@jwt_required()
def create_goal():
    user_id = int(get_jwt_identity())
    data = request.json
    
    try:
        new_goal = Goal(
            user_id=user_id,
            goal_name=data['goal_name'],
            target_amount=float(data['target_amount']),
            current_saved=float(data.get('current_saved', 0.0)),
            target_date=datetime.strptime(data['target_date'], '%Y-%m-%d').date()
        )
        db.session.add(new_goal)
        db.session.commit()
        return jsonify({"msg": "Goal created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create goal", "msg": str(e)}), 400

@app_bp.route('/api/goals/<int:goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    user_id = int(get_jwt_identity())
    goal = db.session.get(Goal, goal_id)
    
    if not goal or goal.user_id != user_id:
        return jsonify({"error": "Goal not found"}), 404
        
    data = request.json
    try:
        if 'goal_name' in data:
            goal.goal_name = data['goal_name']
        if 'target_amount' in data:
            goal.target_amount = float(data['target_amount'])
        if 'current_saved' in data:
            goal.current_saved = float(data['current_saved'])
        if 'target_date' in data:
            goal.target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
            
        db.session.commit()
        return jsonify({"msg": "Goal updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update goal", "msg": str(e)}), 400

@app_bp.route('/api/goals/<int:goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    user_id = int(get_jwt_identity())
    goal = db.session.get(Goal, goal_id)
    
    if not goal or goal.user_id != user_id:
        return jsonify({"error": "Goal not found"}), 404
        
    try:
        db.session.delete(goal)
        db.session.commit()
        return jsonify({"msg": "Goal deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete goal", "msg": str(e)}), 400
