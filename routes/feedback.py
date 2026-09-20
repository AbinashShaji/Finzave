from flask import render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from extensions import db, limiter
from models.feedback import Feedback
from models.review import Review

@app_bp.route('/feedback', methods=['GET'])
@jwt_required()
def feedback():
    user_id = int(get_jwt_identity())
    feedbacks = db.session.query(Feedback).filter_by(user_id=user_id).order_by(Feedback.created_at.desc()).limit(3).all()
    reviews = db.session.query(Review).filter_by(user_id=user_id).order_by(Review.created_at.desc()).limit(3).all()
    return render_template('app/feedback.html', feedbacks=feedbacks, reviews=reviews)

@app_bp.route('/api/feedback', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def submit_feedback():
    user_id = int(get_jwt_identity())
    data = request.json
    
    category = data.get('category', '').strip()
    message = data.get('message', '').strip()
    
    if not category or category not in ['App Review', 'Bug Report', 'Suggestions', 'Other']:
        return jsonify({"msg": "Invalid feedback category."}), 400
        
    if not message or len(message) < 5 or len(message) > 1000:
        return jsonify({"msg": "Feedback message must be between 5 and 1000 characters."}), 400
    
    try:
        new_feedback = Feedback( # type: ignore
            user_id=user_id,
            feedback_type=category,
            content=message,
            status='pending'
        )
        db.session.add(new_feedback)
        db.session.commit()
        return jsonify({
            "msg": "Feedback submitted successfully",
            "feedback": {
                "type": new_feedback.feedback_type,
                "content": new_feedback.content,
                "status": new_feedback.status,
                "created_at": new_feedback.created_at.isoformat() if new_feedback.created_at else None
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to submit feedback", "msg": str(e)}), 400

@app_bp.route('/api/reviews', methods=['POST'])
@jwt_required()
@limiter.limit("1 per minute")
def submit_review():
    user_id = int(get_jwt_identity())
    data = request.json
    
    rating = data.get('rating')
    content = data.get('content', '')
    
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"msg": "Rating must be an integer between 1 and 5"}), 400
        
    if not content or not str(content).strip():
        return jsonify({"msg": "Review content cannot be empty"}), 400
        
    content = str(content).strip()
    if len(content) > 1000:
        return jsonify({"msg": "Review content is too long (max 1000 characters)"}), 400
        
    try:
        new_review = Review( # type: ignore
            user_id=user_id,
            rating=rating,
            content=content.strip(),
            status='pending'
        )
        db.session.add(new_review)
        db.session.commit()
        return jsonify({
            "msg": "Review submitted successfully",
            "review": {
                "rating": new_review.rating,
                "content": new_review.content,
                "status": new_review.status,
                "created_at": new_review.created_at.isoformat() if new_review.created_at else None
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to submit review", "msg": str(e)}), 400

