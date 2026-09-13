from flask import render_template
from routes.user import app_bp

@app_bp.route('/planning')
def planning():
    return render_template('app/planning.html')
