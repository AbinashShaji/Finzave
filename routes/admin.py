"""
Module: routes/admin.py

Purpose:
Handles HTTP requests, route definitions, and view controllers.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from extensions import db
from models.user import User
from models.review import Review
from models.feedback import Feedback
from sqlalchemy import func

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
    from models.income import Income
    from models.expense import Expense
    from models.goal import Goal
    from sqlalchemy import func, cast, Date
    from sqlalchemy.orm import joinedload

    now = datetime.now(timezone.utc)
    twenty_four_hours_ago = now - timedelta(hours=24)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    fifteen_mins_ago = now - timedelta(minutes=15)

    # ──────────────────────────────────────────────
    # SECTION 1 — EXECUTIVE OVERVIEW
    # ──────────────────────────────────────────────

    total_users = User.query.filter(User.role != 'admin').count()

    # Active users by period
    active_24h_ids = db.session.query(UserActivity.user_id).filter(
        UserActivity.created_at >= twenty_four_hours_ago
    ).distinct().count()

    active_7d_ids = db.session.query(UserActivity.user_id).filter(
        UserActivity.created_at >= seven_days_ago
    ).distinct().count()

    active_30d_ids = db.session.query(UserActivity.user_id).filter(
        UserActivity.created_at >= thirty_days_ago
    ).distinct().count()

    online_users = db.session.query(UserActivity.user_id).filter(
        UserActivity.created_at >= fifteen_mins_ago
    ).distinct().count()

    # User growth — compare this month vs last month
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    users_this_month = User.query.filter(User.created_at >= this_month_start, User.role != 'admin').count()
    users_last_month = User.query.filter(
        User.created_at >= last_month_start,
        User.created_at < this_month_start,
        User.role != 'admin'
    ).count()
    user_growth_pct = 0
    if users_last_month > 0:
        user_growth_pct = round(((users_this_month - users_last_month) / users_last_month) * 100, 1)
    elif users_this_month > 0:
        user_growth_pct = 100.0

    # Privacy-safe product counts only — no financial amounts
    total_income_txns = db.session.query(func.count(Income.id)).scalar()
    total_expense_txns = db.session.query(func.count(Expense.id)).scalar()
    total_transactions = total_income_txns + total_expense_txns
    total_goals = Goal.query.count()

    # Platform health — check DB connectivity and basic status
    db_status = "Operational"
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception:
        db_status = "Error"

    # ──────────────────────────────────────────────
    # SECTION 2 — USER ANALYTICS
    # ──────────────────────────────────────────────

    # User growth over last 30 days (registrations per day)
    user_growth_data = db.session.query(
        cast(User.created_at, Date).label('reg_date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= thirty_days_ago,
        User.role != 'admin'
    ).group_by(cast(User.created_at, Date)).order_by(cast(User.created_at, Date)).all()

    user_growth_chart = [{"date": str(row.reg_date), "count": row.count} for row in user_growth_data]

    # Fill in missing days with 0
    if user_growth_chart:
        filled = {}
        for i in range(30):
            d = (now - timedelta(days=29-i)).strftime('%Y-%m-%d')
            filled[d] = 0
        for item in user_growth_chart:
            if item['date'] in filled:
                filled[item['date']] = item['count']
        user_growth_chart = [{"date": k, "count": v} for k, v in filled.items()]

    # Engagement trend — daily activity counts over last 14 days (database aggregation)
    daily_act_counts = db.session.query(
        cast(UserActivity.created_at, Date).label('act_date'),
        func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.created_at >= now - timedelta(days=14),
        UserActivity.action.notin_(['login', 'logout'])
    ).group_by(cast(UserActivity.created_at, Date)).all()

    act_counts_map = {str(row.act_date): row.count for row in daily_act_counts}
    trend = {}
    for i in range(14):
        d = (now - timedelta(days=13-i)).strftime('%Y-%m-%d')
        trend[d] = act_counts_map.get(d, 0)

    engagement_trend = [{"date": k, "count": v} for k, v in trend.items()]

    # Most active users (by activity count in last 30 days)
    most_active_users = db.session.query(
        User.username,
        func.count(UserActivity.id).label('activity_count')
    ).join(UserActivity, User.id == UserActivity.user_id).filter(
        UserActivity.created_at >= thirty_days_ago,
        User.role != 'admin'
    ).group_by(User.username).order_by(func.count(UserActivity.id).desc()).limit(5).all()

    most_active_list = [{"username": row.username, "count": row.activity_count} for row in most_active_users]

    # ──────────────────────────────────────────────
    # SECTION 3 — FEATURE USAGE (privacy-safe counts)
    # ──────────────────────────────────────────────

    # Module usage from activity tracking (database aggregation)
    feature_counts = db.session.query(
        UserActivity.action,
        func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.created_at >= thirty_days_ago,
        UserActivity.action.notin_(['login', 'logout'])
    ).group_by(UserActivity.action).all()

    modules = {row.action: row.count for row in feature_counts}

    total_module_events = sum(modules.values()) if modules else 1
    feature_usage = [{
        "feature": k.replace('_', ' ').title(),
        "count": v,
        "percentage": round((v / total_module_events) * 100, 1)
    } for k, v in sorted(modules.items(), key=lambda item: item[1], reverse=True)]

    # ──────────────────────────────────────────────
    # SECTION 4 — USER MANAGEMENT INSIGHTS
    # ──────────────────────────────────────────────

    # New users (registered in last 7 days)
    new_users = User.query.filter(
        User.created_at >= seven_days_ago,
        User.role != 'admin'
    ).order_by(User.created_at.desc()).limit(5).all()
    new_users_list = [{
        "username": u.username,
        "email": u.email,
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in new_users]

    # Recently active users
    recently_active = db.session.query(
        User.username,
        func.max(UserActivity.created_at).label('last_active')
    ).join(UserActivity, User.id == UserActivity.user_id).filter(
        User.role != 'admin'
    ).group_by(User.username).order_by(func.max(UserActivity.created_at).desc()).limit(5).all()

    recently_active_list = [{
        "username": row.username,
        "last_active": row.last_active.isoformat() if row.last_active else None
    } for row in recently_active]

    # Inactive users — no activity in last 30 days
    active_user_ids_30d = [row[0] for row in db.session.query(UserActivity.user_id).filter(
        UserActivity.created_at >= thirty_days_ago
    ).distinct().all()]

    inactive_users_list = User.query.filter(
        User.role != 'admin',
        ~User.id.in_(active_user_ids_30d) if active_user_ids_30d else True
    ).order_by(User.created_at.desc()).limit(5).all()

    inactive_list = [{
        "username": u.username,
        "email": u.email,
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in inactive_users_list]

    # Recent activity timeline removed for privacy — not returned to frontend

    # ──────────────────────────────────────────────
    # SECTION 5 — FEEDBACK AND REVIEWS
    # ──────────────────────────────────────────────

    recent_feedbacks = Feedback.query.options(
        joinedload(Feedback.user)
    ).filter(Feedback.status != 'deleted').order_by(Feedback.created_at.desc()).limit(5).all()

    recent_feedback_list = [{
        "username": f.user.username if f.user else "Unknown",
        "type": f.feedback_type,
        "content": f.content,
        "status": f.status,
        "time": f.created_at.isoformat() if f.created_at else None
    } for f in recent_feedbacks]

    recent_reviews = Review.query.options(
        joinedload(Review.user)
    ).filter(Review.status != 'deleted').order_by(Review.created_at.desc()).limit(5).all()

    recent_review_list = [{
        "username": r.user.username if r.user else "Anonymous",
        "rating": r.rating,
        "content": r.content,
        "status": r.status,
        "time": r.created_at.isoformat() if r.created_at else None
    } for r in recent_reviews]

    # Feedback/review summary counts
    total_feedback = Feedback.query.filter(Feedback.status != 'deleted').count()
    pending_feedback = Feedback.query.filter_by(status='pending').count()
    total_reviews = Review.query.filter(Review.status != 'deleted').count()
    avg_rating = db.session.query(func.avg(Review.rating)).filter(Review.status != 'deleted').scalar()
    avg_rating = round(float(avg_rating), 1) if avg_rating else None


    return jsonify({
        # Section 1 — Executive Overview (privacy-safe product metrics only)
        "executive": {
            "total_users": total_users,
            "user_growth_pct": user_growth_pct,
            "users_this_month": users_this_month,
            "active_24h": active_24h_ids,
            "active_7d": active_7d_ids,
            "active_30d": active_30d_ids,
            "online_users": online_users,
            "total_transactions": total_transactions,
            "income_txns": total_income_txns,
            "expense_txns": total_expense_txns,
            "total_goals": total_goals,
            "db_status": db_status,
        },
        # Section 2 — User Analytics
        "user_growth_chart": user_growth_chart,
        "engagement_trend": engagement_trend,
        "most_active_users": most_active_list,
        # Section 3 — Feature Usage
        "feature_usage": feature_usage,
        # Section 4 — User Management
        "new_users": new_users_list,
        "recently_active": recently_active_list,
        "inactive_users": inactive_list,
        # Section 5 — Feedback & Reviews
        "recent_feedback": recent_feedback_list,
        "recent_reviews": recent_review_list,
        "feedback_summary": {
            "total": total_feedback,
            "pending": pending_feedback,
        },
        "review_summary": {
            "total": total_reviews,
            "avg_rating": avg_rating,
        },
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
        
    try:
        user.is_blocked = True
        db.session.commit()
        return jsonify(message="User blocked successfully"), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error blocking user {user_id}: {e}")
        return jsonify(message="Failed to block user. Please try again."), 500

@admin_bp.route('/api/admin/users/<int:user_id>/unblock', methods=['POST'])
@admin_required()
def unblock_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify(message="User not found"), 404
        
    try:
        user.is_blocked = False
        db.session.commit()
        return jsonify(message="User unblocked successfully"), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error unblocking user {user_id}: {e}")
        return jsonify(message="Failed to unblock user. Please try again."), 500

@admin_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required()
def delete_user(user_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id == user_id:
        return jsonify(message="Cannot delete yourself"), 400
        
    user = db.session.get(User, user_id)
    if not user:
        return jsonify(message="User not found"), 404
        
    if user.role == 'admin':
        return jsonify(message="Cannot delete an administrator account"), 403
        
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify(message="User deleted successfully"), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error deleting user {user_id}: {e}")
        return jsonify(message="Failed to delete user. Please try again."), 500

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
        
    try:
        review.status = new_status
        db.session.commit()
        return jsonify(message="Review status updated successfully"), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error updating review status {review_id}: {e}")
        return jsonify(message="Failed to update review status."), 500

@admin_bp.route('/api/admin/reviews/<int:review_id>', methods=['DELETE'])
@admin_required()
def delete_review(review_id):
    review = db.session.get(Review, review_id)
    if not review:
        return jsonify(message="Review not found"), 404
        
    try:
        review.status = 'deleted'
        db.session.commit()
        return jsonify(message="Review deleted successfully"), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error deleting review {review_id}: {e}")
        return jsonify(message="Failed to delete review."), 500

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
        
    try:
        feedback.status = new_status
        db.session.commit()
        return jsonify(message="Feedback status updated successfully"), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error updating feedback status {feedback_id}: {e}")
        return jsonify(message="Failed to update feedback status."), 500

@admin_bp.route('/api/admin/feedback/<int:feedback_id>', methods=['DELETE'])
@admin_required()
def delete_feedback(feedback_id):
    feedback = db.session.get(Feedback, feedback_id)
    if not feedback:
        return jsonify(message="Feedback not found"), 404
        
    try:
        feedback.status = 'deleted'
        db.session.commit()
        return jsonify(message="Feedback deleted successfully"), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error deleting feedback {feedback_id}: {e}")
        return jsonify(message="Failed to delete feedback."), 500

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
