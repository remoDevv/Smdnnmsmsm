import os
import subprocess
import tempfile
import shutil
from .install_zsign import install_zsign

def sign_ipa(ipa_path, p12_path, prov_path, p12_password):
    """
    Sign an IPA file using zsign
    """
    # Ensure zsign is installed
    if not install_zsign():
        raise Exception("Failed to install zsign")
        
    # Create temp directory for output
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, 'signed.ipa')
    
    try:
        # Build zsign command
        cmd = [
            'zsign',
            '-k', p12_path,
            '-p', p12_password,
            '-m', prov_path,
            '-o', output_path,
            '-z', '9',
            ipa_path
        ]
        
        # Execute zsign
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if not os.path.exists(output_path):
            raise Exception("Signing failed - no output file created")
            
        return output_path
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Signing failed: {e.stderr}")
    except Exception as e:
        raise Exception(f"Signing failed: {str(e)}")
