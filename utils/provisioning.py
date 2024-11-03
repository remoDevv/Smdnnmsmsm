import plistlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ProvisioningProfile:
    def __init__(self, profile_path: str):
        self.profile_path = profile_path
        self._data = None
        
    def load(self) -> bool:
        """Load and parse mobileprovision file"""
        try:
            with open(self.profile_path, 'rb') as f:
                # Remove leading and trailing XML markers if present
                content = f.read()
                start = content.find(b'<?xml')
                end = content.rfind(b'</plist>') + 8
                if start >= 0 and end > start:
                    content = content[start:end]
                    
                self._data = plistlib.loads(content)
            return True
        except Exception as e:
            logger.error(f"Failed to load provisioning profile: {str(e)}")
            return False
            
    def get_entitlements(self) -> Optional[Dict[str, Any]]:
        """Extract entitlements from the profile"""
        if not self._data:
            return None
            
        try:
            return self._data.get('Entitlements', {})
        except Exception as e:
            logger.error(f"Failed to get entitlements: {str(e)}")
            return None
            
    def get_team_identifier(self) -> Optional[str]:
        """Get team identifier from the profile"""
        if not self._data:
            return None
            
        try:
            return self._data.get('TeamIdentifier', [None])[0]
        except Exception as e:
            logger.error(f"Failed to get team identifier: {str(e)}")
            return None
            
    def is_valid(self) -> bool:
        """Check if the provisioning profile is valid and not expired"""
        if not self._data:
            return False
            
        try:
            expiration_date = self._data.get('ExpirationDate')
            if not expiration_date:
                return False
                
            return expiration_date > datetime.now()
        except Exception as e:
            logger.error(f"Failed to check profile validity: {str(e)}")
            return False
