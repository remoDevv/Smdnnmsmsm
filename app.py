import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from models import Admin
    return Admin.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    
    # Config
    app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "default-secret-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = '/tmp/zsign_uploads'
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'
    
    # Register blueprints
    from routes.admin import admin_bp
    from routes.api import api_bp
    from routes.web import web_bp
    
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with app.app_context():
        db.create_all()
        
    return app
