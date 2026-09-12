from flask import Blueprint, render_template, redirect, url_for, jsonify

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def home():
    return render_template('public/home.html')

@public_bp.route('/about')
def about():
    return render_template('public/about.html')

@public_bp.route('/services')
def services():
    return render_template('public/services.html')

@public_bp.route('/reviews')
def reviews():
    return render_template('public/reviews.html')

@public_bp.route('/api/reviews', methods=['GET'])
def get_public_reviews():
    from models.review import Review
    live_reviews = Review.query.filter_by(status='live').order_by(Review.created_at.desc()).all()
    result = []
    for r in live_reviews:
        result.append({
            "id": r.id,
            "username": r.user.username if r.user else "Anonymous",
            "rating": r.rating,
            "content": r.content,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return jsonify(result), 200

@public_bp.route('/login')
def login():
    return render_template('auth/login.html')

@public_bp.route('/signup')
def signup():
    return render_template('auth/signup.html')

@public_bp.route('/workflow')
def workflow():
    return render_template('public/workflow.html')

@public_bp.route('/faq')
def faq():
    return render_template('public/faq.html')

@public_bp.route('/terms')
def terms():
    return render_template('public/terms.html')

@public_bp.route('/privacy')
def privacy():
    return render_template('public/privacy.html')
