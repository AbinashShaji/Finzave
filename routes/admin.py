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
                if request.path.startswith('/api/'):
                    return jsonify(message="Missing or invalid token"), 401
                return redirect(url_for('public.login'))
            
            user_id = get_jwt_identity()
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

@admin_bp.route('/admin/settings')
@admin_required()
def settings():
    return render_template('admin/settings.html')

# ==========================================
# API ROUTES
# ==========================================

@admin_bp.route('/api/admin/stats', methods=['GET'])
@admin_required()
def get_stats():
    total_users = User.query.count()
    total_reviews = Review.query.count()
    pending_feedback = Feedback.query.filter_by(status='open').count()
    
    return jsonify({
        "total_users": total_users,
        "total_reviews": total_reviews,
        "pending_feedback": pending_feedback
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
            "created_at": u.created_at.isoformat() if u.created_at else None
        })
    return jsonify(result), 200

@admin_bp.route('/api/admin/users/<int:user_id>/role', methods=['PATCH'])
@admin_required()
def update_user_role(user_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id == user_id:
        return jsonify(message="Cannot change your own role"), 400
        
    data = request.get_json()
    new_role = data.get('role')
    if new_role not in ['user', 'admin']:
        return jsonify(message="Invalid role"), 400
        
    user = db.session.get(User, user_id)
    if not user:
        return jsonify(message="User not found"), 404
        
    user.role = new_role
    db.session.commit()
    return jsonify(message="Role updated successfully"), 200

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
    reviews_list = Review.query.order_by(Review.created_at.desc()).all()
    result = []
    for r in reviews_list:
        result.append({
            "id": r.id,
            "username": r.user.username if r.user else "Anonymous",
            "rating": r.rating,
            "content": r.content,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return jsonify(result), 200

@admin_bp.route('/api/admin/reviews/<int:review_id>/status', methods=['PATCH'])
@admin_required()
def update_review_status(review_id):
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['pending', 'approved', 'rejected']:
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
        
    db.session.delete(review)
    db.session.commit()
    return jsonify(message="Review deleted successfully"), 200

@admin_bp.route('/api/admin/feedback', methods=['GET'])
@admin_required()
def get_feedbacks():
    feedbacks_list = Feedback.query.order_by(Feedback.created_at.desc()).all()
    result = []
    for f in feedbacks_list:
        result.append({
            "id": f.id,
            "username": f.user.username if f.user else "Unknown",
            "type": f.feedback_type,
            "content": f.content,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None
        })
    return jsonify(result), 200

@admin_bp.route('/api/admin/feedback/<int:feedback_id>/status', methods=['PATCH'])
@admin_required()
def update_feedback_status(feedback_id):
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['open', 'in_progress', 'resolved']:
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
        
    db.session.delete(feedback)
    db.session.commit()
    return jsonify(message="Feedback deleted successfully"), 200
