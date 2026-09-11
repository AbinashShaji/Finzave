from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from extensions import db, jwt, cache

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok", "message": "FinZave API is running"}), 200

    # Register blueprints
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
