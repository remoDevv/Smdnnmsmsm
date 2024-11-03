import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import APIKey, SigningJob, db
from utils.signing import sign_ipa
from datetime import datetime
import functools

api_bp = Blueprint('api', __name__, url_prefix='/api')

def require_api_key(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'No API key provided'}), 401
            
        key = APIKey.query.filter_by(key=api_key, is_active=True).first()
        if not key:
            return jsonify({'error': 'Invalid API key'}), 401
            
        # Check rate limit
        if key.daily_usage >= key.get_daily_limit():
            return jsonify({'error': 'Daily limit exceeded'}), 429
            
        return f(key, *args, **kwargs)
    return wrapped

@api_bp.route('/sign', methods=['POST'])
@require_api_key
def sign_app(api_key):
    if 'ipa' not in request.files:
        return jsonify({'error': 'No IPA file provided'}), 400
        
    if 'p12' not in request.files:
        return jsonify({'error': 'No P12 certificate provided'}), 400
        
    if 'mobileprovision' not in request.files:
        return jsonify({'error': 'No provisioning profile provided'}), 400
        
    if 'p12_password' not in request.form:
        return jsonify({'error': 'No P12 password provided'}), 400

    # Save files
    ipa_file = request.files['ipa']
    p12_file = request.files['p12']
    prov_file = request.files['mobileprovision']
    
    ipa_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                           secure_filename(ipa_file.filename))
    p12_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                           secure_filename(p12_file.filename))
    prov_path = os.path.join(current_app.config['UPLOAD_FOLDER'],
                            secure_filename(prov_file.filename))
    
    ipa_file.save(ipa_path)
    p12_file.save(p12_path)
    prov_file.save(prov_path)
    
    # Create signing job
    job = SigningJob(
        api_key_id=api_key.id,
        status='pending',
        input_file=ipa_path
    )
    db.session.add(job)
    db.session.commit()
    
    try:
        output_path = sign_ipa(
            ipa_path, 
            p12_path,
            prov_path,
            request.form['p12_password']
        )
        
        job.status = 'completed'
        job.output_file = output_path
        job.completed_at = datetime.utcnow()
        
        # Update API key usage
        api_key.daily_usage += 1
        api_key.last_used = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'job_id': job.id,
            'message': 'IPA signed successfully'
        })
        
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        db.session.commit()
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup
        for path in [ipa_path, p12_path, prov_path]:
            if os.path.exists(path):
                os.remove(path)
