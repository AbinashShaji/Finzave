from flask import render_template
from routes.user import app_bp

@app_bp.route('/goals')
def goals():
    return render_template('app/goals.html')
