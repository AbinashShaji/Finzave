from flask import render_template
from routes.user import app_bp

@app_bp.route('/feedback')
def feedback():
    return render_template('app/feedback.html')
