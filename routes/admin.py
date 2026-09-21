from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from extensions import db
from models.user import User
from models.review import Review
from models.feedback import Feedback

admin_bp = Blueprint('admin', __name__)

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception as e:
                import traceback
                print(f"JWT Verification Failed in admin_required: {e}")
                traceback.print_exc()
                if request.path.startswith('/api/'):
                    return jsonify(message=f"Token error: {str(e)}"), 401
                return redirect(url_for('public.login'))
            
            user_id = int(get_jwt_identity())
            user = db.session.get(User, int(user_id))
            
            if not user or user.role != 'admin':
                if request.path.startswith('/api/'):
                    return jsonify(message="Admin privilege required"), 403
                return render_template('403.html'), 403
                
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# ==========================================
# UI ROUTES
# ==========================================

@admin_bp.route('/admin')
@admin_required()
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/admin/users')
@admin_required()
def users():
    return render_template('admin/users.html')

@admin_bp.route('/admin/reviews')
@admin_required()
def reviews():
    return render_template('admin/reviews.html')

@admin_bp.route('/admin/feedback')
@admin_required()
def feedback():
    return render_template('admin/feedback.html')

@admin_bp.route('/admin/profile')
@admin_required()
def profile():
    return render_template('admin/profile.html')

@admin_bp.route('/admin/settings')
@admin_required()
def settings_redirect():
    return redirect(url_for('admin.profile'))

# ==========================================
# API ROUTES
# ==========================================

@admin_bp.route('/api/admin/stats', methods=['GET'])
@admin_required()
def get_stats():
    from datetime import datetime, timedelta, timezone
    from models.activity import UserActivity
    from sqlalchemy import func

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    fifteen_mins_ago = now - timedelta(minutes=15)

    total_users = User.query.count()

    # Calculate active/online users
    active_user_ids = db.session.query(UserActivity.user_id).filter(UserActivity.created_at >= seven_days_ago).distinct().all()
    active_users = len(active_user_ids)
    inactive_users = total_users - active_users
    
    online_user_ids = db.session.query(UserActivity.user_id).filter(UserActivity.created_at >= fifteen_mins_ago).distinct().all()
    online_users = len(online_user_ids)

    # Fetch recent activities for trending/grouping
    # Explicitly filter out 'login' and 'logout' as they are not product modules
    recent_product_activities = UserActivity.query.filter(
        UserActivity.created_at >= seven_days_ago,
        UserActivity.action.notin_(['login', 'logout'])
    ).all()
    
    # Group by date for engagement trend
    trend = {}
    for act in recent_product_activities:
        date_str = act.created_at.strftime('%Y-%m-%d')
        trend[date_str] = trend.get(date_str, 0) + 1
        
    engagement_trend = [{"date": k, "count": v} for k, v in sorted(trend.items())]

    # Module usage
    modules = {}
    for act in recent_product_activities:
        modules[act.action] = modules.get(act.action, 0) + 1
    module_usage = [{"module": k, "count": v} for k, v in sorted(modules.items(), key=lambda item: item[1], reverse=True)]

    # Recent activity list (last 10 non-sensitive)
    latest_activities = UserActivity.query.order_by(UserActivity.created_at.desc()).limit(10).all()
    recent_activity_list = []
    for a in latest_activities:
        recent_activity_list.append({
            "action": a.action,
            "username": a.user.username if a.user else "Unknown",
            "time": a.created_at.isoformat()
        })

    # Recent Feedback
    recent_feedbacks = Feedback.query.filter(Feedback.status != 'deleted').order_by(Feedback.created_at.desc()).limit(5).all()
    recent_feedback_list = []
    for f in recent_feedbacks:
        recent_feedback_list.append({
            "username": f.user.username if f.user else "Unknown",
            "content": f.content,
            "status": f.status,
            "time": f.created_at.isoformat() if f.created_at else None
        })

    # Recent Reviews
    recent_reviews = Review.query.filter(Review.status != 'deleted').order_by(Review.created_at.desc()).limit(5).all()
    recent_review_list = []
    for r in recent_reviews:
        recent_review_list.append({
            "username": r.user.username if r.user else "Anonymous",
            "rating": r.rating,
            "content": r.content,
            "status": r.status,
            "time": r.created_at.isoformat() if r.created_at else None
        })

    # Generate User Insights
    insights = []
    if module_usage:
        insights.append(f"'{module_usage[0]['module'].replace('_', ' ').title()}' is currently the most-used FinZave module.")
    
    if active_users > 0:
        insights.append(f"{active_users} users were active in the last 7 days.")
    else:
        insights.append("User engagement has been quiet over the last 7 days.")

    if recent_feedback_list:
        insights.append(f"{recent_feedback_list[0]['username']} submitted feedback recently.")
        
    if recent_review_list:
        insights.append(f"A new review was submitted by {recent_review_list[0]['username']}.")
        
    if not insights or len(recent_product_activities) == 0:
        insights = ["Not enough activity data to generate engagement insights yet."]

    return jsonify({
        "kpis": {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "online_users": online_users
        },
        "engagement_trend": engagement_trend,
        "module_usage": module_usage,
        "recent_activity": recent_activity_list,
        "recent_feedback": recent_feedback_list,
        "recent_reviews": recent_review_list,
        "user_insights": insights
    }), 200

@admin_bp.route('/api/admin/users', methods=['GET'])
@admin_required()
def get_users():
    users_list = User.query.order_by(User.created_at.desc()).all()
    result = []
    for u in users_list:
        result.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_blocked": u.is_blocked,
            "is_online": u.is_online,
            "last_active": u.last_active.isoformat() if u.last_active else None,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })
    return jsonify(result), 200

@admin_bp.route('/api/admin/users/<int:user_id>/block', methods=['POST'])
@admin_required()
def block_user(user_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id == user_id:
        return jsonify(message="Cannot block yourself"), 400
        
    user = db.session.get(User, user_id)
    if not user:
        return jsonify(message="User not found"), 404
        
    user.is_blocked = True
    db.session.commit()
    return jsonify(message="User blocked successfully"), 200

@admin_bp.route('/api/admin/users/<int:user_id>/unblock', methods=['POST'])
@admin_required()
def unblock_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify(message="User not found"), 404
        
    user.is_blocked = False
    db.session.commit()
    return jsonify(message="User unblocked successfully"), 200


@admin_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required()
def delete_user(user_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id == user_id:
        return jsonify(message="Cannot delete yourself"), 400
        
    user = db.session.get(User, user_id)
    if not user:
        return jsonify(message="User not found"), 404
        
    db.session.delete(user)
    db.session.commit()
    return jsonify(message="User deleted successfully"), 200

@admin_bp.route('/api/admin/reviews', methods=['GET'])
@admin_required()
def get_reviews():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status')
    
    from sqlalchemy.orm import joinedload
    query = Review.query.options(joinedload(Review.user))
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    paginated = query.order_by(Review.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "items": [r.to_dict() for r in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total
    }), 200

@admin_bp.route('/api/admin/reviews/<int:review_id>/status', methods=['PATCH'])
@admin_required()
def update_review_status(review_id):
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['pending', 'accepted', 'live']:
        return jsonify(message="Invalid status"), 400
        
    review = db.session.get(Review, review_id)
    if not review:
        return jsonify(message="Review not found"), 404
        
    review.status = new_status
    db.session.commit()
    return jsonify(message="Review status updated successfully"), 200

@admin_bp.route('/api/admin/reviews/<int:review_id>', methods=['DELETE'])
@admin_required()
def delete_review(review_id):
    review = db.session.get(Review, review_id)
    if not review:
        return jsonify(message="Review not found"), 404
        
    review.status = 'deleted'
    db.session.commit()
    return jsonify(message="Review deleted successfully"), 200

@admin_bp.route('/api/admin/feedback', methods=['GET'])
@admin_required()
def get_feedbacks():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status')
    
    from sqlalchemy.orm import joinedload
    query = Feedback.query.options(joinedload(Feedback.user))
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    paginated = query.order_by(Feedback.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "items": [f.to_dict() for f in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total
    }), 200

@admin_bp.route('/api/admin/feedback/<int:feedback_id>/status', methods=['PATCH'])
@admin_required()
def update_feedback_status(feedback_id):
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['pending', 'in_progress', 'resolved']:
        return jsonify(message="Invalid status"), 400
        
    feedback = db.session.get(Feedback, feedback_id)
    if not feedback:
        return jsonify(message="Feedback not found"), 404
        
    feedback.status = new_status
    db.session.commit()
    return jsonify(message="Feedback status updated successfully"), 200

@admin_bp.route('/api/admin/feedback/<int:feedback_id>', methods=['DELETE'])
@admin_required()
def delete_feedback(feedback_id):
    feedback = db.session.get(Feedback, feedback_id)
    if not feedback:
        return jsonify(message="Feedback not found"), 404
        
    feedback.status = 'deleted'
    db.session.commit()
    return jsonify(message="Feedback deleted successfully"), 200

@admin_bp.route('/api/admin/system', methods=['GET'])
@admin_required()
def get_system_info():
    import os
    import sys
    import flask
    
    # Try to get alembic head version securely
    try:
        from alembic.migration import MigrationContext
        context = MigrationContext.configure(db.engine.connect())
        current_rev = context.get_current_revision()
    except Exception:
        current_rev = "Unknown"

    return jsonify({
        "app_version": "1.0.0 (Admin Phase)",
        "flask_env": os.environ.get("FLASK_ENV", "production"),
        "flask_version": flask.__version__,
        "python_version": sys.version.split(' ')[0],
        "database_status": "Connected" if db.engine else "Disconnected",
        "migration_version": current_rev
    }), 200
