from flask import render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from extensions import db
from models.feedback import Feedback

@app_bp.route('/feedback', methods=['GET'])
@jwt_required()
def feedback():
    user_id = int(get_jwt_identity())
    feedbacks = db.session.query(Feedback).filter_by(user_id=user_id).order_by(Feedback.created_at.desc()).all()
    return render_template('app/feedback.html', feedbacks=feedbacks)

@app_bp.route('/api/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    user_id = int(get_jwt_identity())
    data = request.json
    
    try:
        new_feedback = Feedback(
            user_id=user_id,
            feedback_type=data.get('category', 'Other'),
            content=data.get('message', ''),
            status='open'
        )
        db.session.add(new_feedback)
        db.session.commit()
        return jsonify({"msg": "Feedback submitted successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to submit feedback", "msg": str(e)}), 400
