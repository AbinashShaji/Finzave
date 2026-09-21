from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from extensions import db, jwt, cache, limiter, migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok", "message": "FinZave API is running"}), 200

    # JWT Error Handlers
    from flask import request, redirect, url_for
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        if request.path.startswith('/api') or request.path.startswith('/app/api'):
            return jsonify({"msg": "Token has expired"}), 401
        return redirect(url_for('public.login'))

    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        if request.path.startswith('/api') or request.path.startswith('/app/api'):
            return jsonify({"msg": error_string}), 401
        return redirect(url_for('public.login'))

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        if request.path.startswith('/api') or request.path.startswith('/app/api'):
            return jsonify({"msg": error_string}), 401
        return redirect(url_for('public.login'))

    from models.user import User

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return db.session.get(User, int(identity))

    @app.before_request
    def check_if_blocked():
        from flask_jwt_extended import verify_jwt_in_request, current_user
        try:
            # Check if there is a valid JWT. If so, it will load current_user
            verify_jwt_in_request(optional=True)
            if current_user and current_user.is_blocked:
                # Force logout behavior for APIs or Redirect
                if request.path.startswith('/api') or request.path.startswith('/app/api'):
                    return jsonify({"msg": "Your account has been blocked. Please contact support."}), 403
                from flask import redirect, url_for
                return redirect(url_for('public.login'))
        except Exception:
            pass

    @app.after_request
    def add_cache_control(response):
        if 'text/html' in response.headers.get('Content-Type', ''):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    # Register blueprints
    from routes.auth import auth_bp
    from routes.public import public_bp
    from routes.admin import admin_bp
    from routes.user import app_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(app_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('404.html'), 404

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
