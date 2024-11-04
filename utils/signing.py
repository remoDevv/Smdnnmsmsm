import os
import subprocess
import logging
import shutil
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

def sign_ipa(ipa_path: str, p12_path: str, prov_path: str, p12_password: str) -> str:
    try:
        # Create temp directory for zsign binary if not exists
        zsign_dir = '/tmp/zsign'
        os.makedirs(zsign_dir, exist_ok=True)
        
        # Clone zsign if not already present
        if not os.path.exists(os.path.join(zsign_dir, 'zsign')):
            subprocess.run(['git', 'clone', 'https://github.com/gyke69/compiled-zsign.git', zsign_dir], check=True)
            subprocess.run(['chmod', '+x', os.path.join(zsign_dir, 'zsign')], check=True)
        
        # Prepare output path
        output_dir = os.path.dirname(ipa_path)
        output_path = os.path.join(output_dir, 'signed.ipa')
        
        # Build zsign command
        cmd = [
            os.path.join(zsign_dir, 'zsign'),
            '-k', p12_path,
            '-p', p12_password,
            '-m', prov_path,
            '-o', output_path,
            '-z', '9',
            ipa_path
        ]
        
        # Execute zsign
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if not os.path.exists(output_path):
            raise Exception("Failed to generate signed IPA")
            
        return output_path
        
    except subprocess.CalledProcessError as e:
        error_msg = f"zsign failed: {e.stderr}"
        logger.error(error_msg)
        if "password error" in e.stderr.lower():
            raise Exception("Invalid P12 certificate password")
        elif "provision error" in e.stderr.lower():
            raise Exception("Invalid provisioning profile")
        elif "bundle id" in e.stderr.lower():
            raise Exception("Bundle ID mismatch between IPA and provisioning profile")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Signing failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
