from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from flask_login import login_user, login_required, logout_user
from models import Admin, APIKey, SigningJob, db
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import func
import logging
import os
from utils.signing import sign_ipa

admin_bp = Blueprint('admin', __name__, url_prefix='/albos')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('admin/login.html')
            
        if username == 'admin' and password == 'albos':
            admin = Admin.query.filter_by(username='admin').first()
            if not admin:
                admin = Admin(username='admin')
                admin.set_password('albos')
                db.session.add(admin)
                db.session.commit()
                logger.info('Created new admin user')
            
            login_user(admin)
            logger.info(f'Admin user {username} logged in successfully')
            return redirect(url_for('admin.dashboard'))
        
        flash('Invalid username or password', 'danger')
        logger.warning(f'Failed login attempt for username: {username}')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    api_keys = APIKey.query.all()
    return render_template('admin/dashboard.html', api_keys=api_keys)

@admin_bp.route('/analytics')
@login_required
def analytics():
    # Get data for the past 7 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    # Daily signing requests
    daily_jobs = db.session.query(
        func.date(SigningJob.created_at).label('date'),
        func.count(SigningJob.id).label('count')
    ).filter(
        SigningJob.created_at >= start_date
    ).group_by(
        func.date(SigningJob.created_at)
    ).order_by(
        func.date(SigningJob.created_at)
    ).all()
    
    dates = []
    daily_counts = []
    current_date = start_date
    while current_date.date() <= end_date.date():
        dates.append(current_date.strftime('%Y-%m-%d'))
        count = next((job.count for job in daily_jobs if job.date == current_date.date()), 0)
        daily_counts.append(count)
        current_date += timedelta(days=1)
    
    # API key usage distribution
    key_stats = db.session.query(
        APIKey.name,
        func.count(SigningJob.id).label('usage')
    ).outerjoin(
        SigningJob,
        APIKey.id == SigningJob.api_key_id
    ).group_by(
        APIKey.id,
        APIKey.name
    ).all()
    
    key_names = [stat.name for stat in key_stats]
    key_usage = [stat.usage for stat in key_stats]
    
    # Recent signing jobs
    recent_jobs = SigningJob.query.order_by(
        SigningJob.created_at.desc()
    ).limit(10).all()
    
    return render_template('admin/analytics.html',
                         dates=dates,
                         daily_counts=daily_counts,
                         key_names=key_names,
                         key_usage=key_usage,
                         recent_jobs=recent_jobs)

@admin_bp.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    if request.method == 'POST':
        if 'ipa' not in request.files or 'p12' not in request.files or 'mobileprovision' not in request.files:
            flash('All files are required', 'danger')
            return render_template('admin/test.html')

        p12_password = request.form.get('p12_password')
        if not p12_password:
            flash('P12 password is required', 'danger')
            return render_template('admin/test.html')

        # Save files
        upload_folder = '/tmp/zsign_uploads'
        os.makedirs(upload_folder, exist_ok=True)

        ipa_file = request.files['ipa']
        p12_file = request.files['p12']
        prov_file = request.files['mobileprovision']
        
        ipa_path = os.path.join(upload_folder, secure_filename(ipa_file.filename))
        p12_path = os.path.join(upload_folder, secure_filename(p12_file.filename))
        prov_path = os.path.join(upload_folder, secure_filename(prov_file.filename))
        
        try:
            ipa_file.save(ipa_path)
            p12_file.save(p12_path)
            prov_file.save(prov_path)
            
            # Sign the IPA
            output_path = sign_ipa(ipa_path, p12_path, prov_path, p12_password)
            
            # Store the output path in session for download
            session['signed_ipa_path'] = output_path
            
            flash('IPA signed successfully!', 'success')
            return render_template('admin/test.html', signed_file_path=output_path)
            
        except Exception as e:
            flash(f'Error signing IPA: {str(e)}', 'danger')
            return render_template('admin/test.html')
        finally:
            # Cleanup input files
            for path in [ipa_path, p12_path, prov_path]:
                if os.path.exists(path):
                    os.remove(path)
    
    return render_template('admin/test.html')

@admin_bp.route('/download_signed_ipa')
@login_required
def download_signed_ipa():
    file_path = request.args.get('file_path')
    if not file_path or not os.path.exists(file_path):
        flash('Signed IPA file not found', 'danger')
        return redirect(url_for('admin.test'))
    
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name='signed.ipa'
        )
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'danger')
        return redirect(url_for('admin.test'))
    finally:
        # Cleanup the signed file after download
        if os.path.exists(file_path):
            os.remove(file_path)

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
