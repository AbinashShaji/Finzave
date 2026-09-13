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
