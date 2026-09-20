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
    from flask import request
    from models.review import Review
    from sqlalchemy.orm import joinedload
    page = request.args.get('page', 1, type=int)
    paginated_reviews = Review.query.options(joinedload(Review.user)).filter_by(status='live').order_by(Review.created_at.desc()).paginate(page=page, per_page=12, error_out=False)
    return render_template('public/reviews.html', paginated_reviews=paginated_reviews)

@public_bp.route('/api/reviews', methods=['GET'])
def get_public_reviews():
    from flask import request
    from models.review import Review
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    from sqlalchemy.orm import joinedload
    paginated = Review.query.options(joinedload(Review.user)).filter_by(status='live').order_by(Review.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "items": [r.to_dict() for r in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total
    }), 200

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
