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

    # Register blueprints
    from routes.auth import auth_bp
    from routes.public import public_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('404.html'), 404

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
