import os
import shutil
import logging
from .ipa_signer import IPASigner
from .certificate_handler import CertificateHandler
from .provisioning import ProvisioningProfile

logger = logging.getLogger(__name__)

def sign_ipa(ipa_path: str, p12_path: str, prov_path: str, p12_password: str) -> str:
    """
    Sign an IPA file using custom implementation
    
    Args:
        ipa_path: Path to input IPA file
        p12_path: Path to P12 certificate
        prov_path: Path to provisioning profile
        p12_password: Password for P12 certificate
        
    Returns:
        Path to signed IPA file
        
    Raises:
        Exception: If signing fails with detailed error message
    """
    try:
        # Initialize handlers
        cert_handler = CertificateHandler(p12_path, p12_password)
        profile = ProvisioningProfile(prov_path)
        
        # Validate inputs exist
        if not os.path.exists(ipa_path):
            raise Exception("IPA file not found")
        if not os.path.exists(p12_path):
            raise Exception("P12 certificate not found")
        if not os.path.exists(prov_path):
            raise Exception("Provisioning profile not found")
            
        # Sign IPA using custom implementation
        with IPASigner(ipa_path, cert_handler, profile) as signer:
            signed_ipa = signer.sign()
            if not signed_ipa:
                raise Exception("Failed to sign IPA - check logs for details")
                
            # Move to final location
            final_path = os.path.join(os.path.dirname(ipa_path), 'signed.ipa')
            shutil.move(signed_ipa, final_path)
            return final_path
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"IPA signing failed: {error_msg}")
        raise Exception(f"IPA signing failed: {error_msg}")
