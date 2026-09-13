from flask import render_template
from routes.user import app_bp

@app_bp.route('/analysis')
def analysis():
    return render_template('app/analysis.html')
