from flask import render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from extensions import db
from models.goal import Goal
from datetime import datetime, date

def prepare_goals_data(user_goals):
    today = date.today()
    active_goals = []
    completed_goals = []
    
    for g_model in user_goals:
        try:
            target_amount = float(g_model.target_amount) if g_model.target_amount is not None else -1
            current_saved = float(g_model.current_saved) if g_model.current_saved is not None else -1
            target_date = g_model.target_date
            
            if target_amount <= 0 or current_saved < 0 or target_date is None:
                raise ValueError("Invalid goal data")
                
            # valid, create a dict to avoid modifying the model
            g = {
                "id": g_model.id,
                "goal_name": g_model.goal_name,
                "target_amount": target_amount,
                "current_saved": current_saved,
                "target_date": target_date,
                "completion_pct": min(100.0, (current_saved / target_amount) * 100),
                "remaining_amount": max(0.0, target_amount - current_saved)
            }
            
            if current_saved >= target_amount:
                g["status"] = "COMPLETED"
                g["months_left"] = 0
                g["req_monthly"] = 0
                completed_goals.append(g)
            else:
                if today > target_date:
                    g["status"] = "OVERDUE"
                    g["months_left"] = 0
                    g["req_monthly"] = 0
                else:
                    g["status"] = "ACTIVE"
                    months = (target_date.year - today.year) * 12 + target_date.month - today.month
                    g["months_left"] = max(0, months)
                    if g["months_left"] == 0 and target_date >= today:
                        g["months_left"] = 1
                        
                    if g["months_left"] > 0:
                        g["req_monthly"] = g["remaining_amount"] / g["months_left"]
                    else:
                        g["req_monthly"] = 0
                active_goals.append(g)
        except (ValueError, TypeError):
            # Invalid goal state
            g = {
                "id": g_model.id,
                "goal_name": g_model.goal_name,
                "target_amount": getattr(g_model, 'target_amount', 0),
                "current_saved": getattr(g_model, 'current_saved', 0),
                "target_date": getattr(g_model, 'target_date', None),
                "status": "INVALID",
                "completion_pct": 0,
                "remaining_amount": 0,
                "months_left": 0,
                "req_monthly": 0
            }
            active_goals.append(g)
            
    return active_goals, completed_goals

@app_bp.route('/goals')
@jwt_required()
def goals():
    user_id = int(get_jwt_identity())
    user_goals = db.session.query(Goal).filter_by(user_id=user_id).order_by(Goal.target_date.asc()).all()
    
    total_saved = sum(g.current_saved for g in user_goals if g.current_saved is not None and g.current_saved >= 0)
    active_goals, completed_goals = prepare_goals_data(user_goals)
            
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
        target_amount = float(data.get('target_amount', 0))
        current_saved = float(data.get('current_saved', 0.0))
        
        if target_amount <= 0:
            return jsonify({"error": "Target amount must be greater than 0"}), 400
        if current_saved < 0:
            return jsonify({"error": "Current saved cannot be negative"}), 400
            
        target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
        if target_date < date.today():
            return jsonify({"error": "Target date cannot be in the past"}), 400
            
        new_goal = Goal(
            user_id=user_id,
            goal_name=data['goal_name'],
            target_amount=target_amount,
            current_saved=current_saved,
            target_date=target_date
        )
        db.session.add(new_goal)
        db.session.commit()
        return jsonify({"msg": "Goal created successfully"}), 201
    except ValueError as e:
        return jsonify({"error": "Invalid input format"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create goal"}), 400

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
            val = float(data['target_amount'])
            if val <= 0: return jsonify({"error": "Target amount must be > 0"}), 400
            goal.target_amount = val
        if 'current_saved' in data:
            val = float(data['current_saved'])
            if val < 0: return jsonify({"error": "Current saved cannot be negative"}), 400
            goal.current_saved = val
        if 'target_date' in data:
            goal.target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
            
        db.session.commit()
        return jsonify({"msg": "Goal updated successfully"}), 200
    except ValueError as e:
        return jsonify({"error": "Invalid input format"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update goal"}), 400

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
        return jsonify({"error": "Failed to delete goal"}), 400

