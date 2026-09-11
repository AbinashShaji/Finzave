from flask import Blueprint, render_template, redirect, url_for

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

@public_bp.route('/login')
def login():
    return render_template('auth/login.html')

@public_bp.route('/signup')
def signup():
    return render_template('auth/signup.html')
