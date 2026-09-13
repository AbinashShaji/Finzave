from flask import render_template
from routes.user import app_bp

@app_bp.route('/settings')
def settings():
    return render_template('app/settings.html')
