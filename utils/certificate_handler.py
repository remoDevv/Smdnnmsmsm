import logging
from typing import Optional, Tuple
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509 import Certificate
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

logger = logging.getLogger(__name__)

class CertificateHandler:
    def __init__(self, p12_path: str, password: str):
        """Initialize certificate handler with P12 file path and password"""
        self.p12_path = p12_path
        self.password = password.encode() if password else None
        self._private_key = None
        self._cert = None
        
    def load(self) -> bool:
        """Load and validate P12 certificate"""
        try:
            # Read P12 file
            with open(self.p12_path, 'rb') as f:
                p12_data = f.read()
                
            # Parse P12 using cryptography
            self._private_key, self._cert, _ = pkcs12.load_key_and_certificates(
                p12_data, 
                self.password
            )
            
            if not isinstance(self._private_key, RSAPrivateKey):
                raise ValueError("Private key must be RSA")
                
            return True
        except Exception as e:
            logger.error(f"Failed to load P12 certificate: {str(e)}")
            return False
            
    def get_certificate_info(self) -> Optional[dict]:
        """Get certificate information"""
        if not self._cert:
            return None
            
        try:
            return {
                'common_name': self.get_common_name(),
                'organization': self._cert.subject.get_attributes_for_oid(
                    self._cert.oid.ORGANIZATION_NAME)[0].value,
                'expiry': self._cert.not_valid_after.isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get certificate info: {str(e)}")
            return None
            
    def sign_data(self, data: bytes) -> Optional[bytes]:
        """Sign data using the private key with modern crypto APIs"""
        if not self._private_key:
            return None
            
        try:
            signature = self._private_key.sign(
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return signature
        except Exception as e:
            logger.error(f"Failed to sign data: {str(e)}")
            return None
            
    def get_common_name(self) -> Optional[str]:
        if not self._cert:
            return None
            
        try:
            for attribute in self._cert.subject:
                if attribute.oid._name == 'commonName':
                    return attribute.value
            return None
        except Exception as e:
            logger.error(f"Failed to get common name: {str(e)}")
            return None
            
    def cleanup(self):
        """Clean up resources"""
        self._private_key = None
        self._cert = None
