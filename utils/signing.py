import os
import subprocess
import tempfile
import shutil
import logging
from .install_zsign import install_zsign
from .ipa_signer import IPASigner
from .certificate_handler import CertificateHandler
from .provisioning import ProvisioningProfile

logger = logging.getLogger(__name__)

def sign_ipa(ipa_path: str, p12_path: str, prov_path: str, p12_password: str) -> str:
    """
    Sign an IPA file using custom implementation with zsign fallback
    
    Args:
        ipa_path: Path to input IPA file
        p12_path: Path to P12 certificate
        prov_path: Path to provisioning profile
        p12_password: Password for P12 certificate
        
    Returns:
        Path to signed IPA file
        
    Raises:
        Exception: If signing fails
    """
    try:
        # Try custom implementation first
        cert_handler = CertificateHandler(p12_path, p12_password)
        profile = ProvisioningProfile(prov_path)
        
        with IPASigner(ipa_path, cert_handler, profile) as signer:
            signed_ipa = signer.sign()
            if signed_ipa:
                # Move to permanent location
                output_dir = os.path.dirname(ipa_path)
                final_path = os.path.join(output_dir, 'signed.ipa')
                shutil.move(signed_ipa, final_path)
                return final_path
                
        logger.warning("Custom signing failed, falling back to zsign...")
        
        # Fallback to zsign
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
                
            # Move to final location
            final_path = os.path.join(os.path.dirname(ipa_path), 'signed.ipa')
            shutil.move(output_path, final_path)
            return final_path
            
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except subprocess.CalledProcessError as e:
        raise Exception(f"Signing failed: {e.stderr}")
    except Exception as e:
        raise Exception(f"Signing failed: {str(e)}")
