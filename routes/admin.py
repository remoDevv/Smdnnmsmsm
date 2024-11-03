from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user
from models import Admin, APIKey, db
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/albos')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == 'albos':
            admin = Admin.query.filter_by(username='admin').first()
            if not admin:
                admin = Admin(username='admin')
                admin.set_password('albos')
                db.session.add(admin)
                db.session.commit()
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid password')
    return render_template('admin/login.html')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    api_keys = APIKey.query.all()
    return render_template('admin/dashboard.html', api_keys=api_keys)

@admin_bp.route('/keys/create', methods=['POST'])
@login_required
def create_key():
    name = request.form['name']
    tier = request.form['tier']
    
    api_key = APIKey(
        key=APIKey.generate_key(),
        name=name,
        tier=tier
    )
    db.session.add(api_key)
    db.session.commit()
    
    flash(f'API Key created: {api_key.key}')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/keys/<int:key_id>/toggle', methods=['POST'])
@login_required
def toggle_key(key_id):
    api_key = APIKey.query.get_or_404(key_id)
    api_key.is_active = not api_key.is_active
    db.session.commit()
    return redirect(url_for('admin.dashboard'))
