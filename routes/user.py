from flask import Blueprint

app_bp = Blueprint('app', __name__, url_prefix='/app')

# Import modules to register routes to app_bp
from routes import dashboard, transactions, goals, analysis, planning, feedback, settings
