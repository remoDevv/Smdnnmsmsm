from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    tier = db.Column(db.String(20), nullable=False)  # 'regular' or 'premium'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    daily_usage = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    @staticmethod
    def generate_key():
        return str(uuid.uuid4())

    def get_daily_limit(self):
        return 100 if self.tier == 'premium' else 10

class SigningJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_key.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    input_file = db.Column(db.String(255))
    output_file = db.Column(db.String(255))
    error_message = db.Column(db.Text)
