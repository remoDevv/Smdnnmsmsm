import OpenSSL
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class CertificateHandler:
    def __init__(self, p12_path: str, password: str):
        self.p12_path = p12_path
        self.password = password.encode() if password else None
        self._cert = None
        self._private_key = None
        
    def load(self) -> bool:
        """Load and validate P12 certificate"""
        try:
            # Read P12 file
            with open(self.p12_path, 'rb') as f:
                p12_data = f.read()
                
            # Parse P12
            p12 = OpenSSL.crypto.load_pkcs12(p12_data, self.password)
            self._cert = p12.get_certificate()
            self._private_key = p12.get_privatekey()
            
            return True
        except Exception as e:
            logger.error(f"Failed to load P12 certificate: {str(e)}")
            return False
            
    def get_certificate_info(self) -> Optional[dict]:
        """Get certificate information"""
        if not self._cert:
            return None
            
        try:
            subject = self._cert.get_subject()
            return {
                'common_name': subject.CN,
                'organization': subject.O,
                'expiry': self._cert.get_notAfter().decode()
            }
        except Exception as e:
            logger.error(f"Failed to get certificate info: {str(e)}")
            return None
            
    def sign_data(self, data: bytes) -> Optional[bytes]:
        """Sign data using the private key"""
        if not self._private_key:
            return None
            
        try:
            signature = OpenSSL.crypto.sign(self._private_key, data, 'sha256')
            return signature
        except Exception as e:
            logger.error(f"Failed to sign data: {str(e)}")
            return None
