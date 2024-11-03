import os
import shutil
import zipfile
import logging
import tempfile
import plistlib
from typing import Optional, List
from .certificate_handler import CertificateHandler
from .provisioning import ProvisioningProfile

logger = logging.getLogger(__name__)

class IPASigner:
    def __init__(self, ipa_path: str, cert_handler: CertificateHandler, 
                 profile: ProvisioningProfile):
        self.ipa_path = ipa_path
        self.cert_handler = cert_handler
        self.profile = profile
        self.temp_dir = None
        
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup temp directory and certificate handler
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.cert_handler.cleanup()
            
    def _find_binaries(self, app_dir: str) -> List[str]:
        """Find all Mach-O binaries in the app bundle"""
        binaries = []
        
        for root, _, files in os.walk(app_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Check if file is Mach-O binary using file magic
                try:
                    with open(file_path, 'rb') as f:
                        magic = f.read(4)
                        if magic.startswith(b'\xca\xfe\xba\xbe') or \
                           magic.startswith(b'\xce\xfa\xed\xfe') or \
                           magic.startswith(b'\xcf\xfa\xed\xfe'):
                            binaries.append(file_path)
                except:
                    continue
                    
        return binaries
            
    def _update_info_plist(self, app_dir: str) -> bool:
        """Update Info.plist with new bundle ID and entitlements"""
        try:
            info_plist_path = os.path.join(app_dir, 'Info.plist')
            with open(info_plist_path, 'rb') as f:
                info_plist = plistlib.load(f)
                
            # Update with provisioning profile data
            entitlements = self.profile.get_entitlements()
            if entitlements:
                bundle_id = entitlements.get('application-identifier', '').split('.')[-1]
                if bundle_id:
                    info_plist['CFBundleIdentifier'] = bundle_id
                    
            # Write updated plist
            with open(info_plist_path, 'wb') as f:
                plistlib.dump(info_plist, f)
                
            return True
        except Exception as e:
            logger.error(f"Failed to update Info.plist: {str(e)}")
            return False

    def _sign_binary(self, binary_path: str, entitlements: dict) -> bool:
        try:
            # Create temporary entitlements file
            entitlements_path = os.path.join(self.temp_dir, 'entitlements.plist')
            with open(entitlements_path, 'wb') as f:
                plistlib.dump(entitlements, f)
                
            # Get certificate common name
            common_name = self.cert_handler.get_common_name()
            if not common_name:
                raise Exception("Failed to get certificate common name")
                
            logger.info(f"Signing {binary_path} with certificate: {common_name}")
            
            # Use codesign command
            result = os.system(f'codesign --force --sign "{common_name}" '
                            f'--entitlements "{entitlements_path}" "{binary_path}"')
            
            if result != 0:
                raise Exception(f"codesign command failed with exit code {result}")
                
            return True
        except Exception as e:
            logger.error(f"Failed to sign binary {binary_path}: {str(e)}")
            return False
                    
    def _unzip_ipa(self) -> Optional[str]:
        """Extract IPA contents"""
        try:
            app_dir = None
            with zipfile.ZipFile(self.ipa_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
                
            # Find .app directory
            payload_dir = os.path.join(self.temp_dir, 'Payload')
            for item in os.listdir(payload_dir):
                if item.endswith('.app'):
                    app_dir = os.path.join(payload_dir, item)
                    break
                    
            return app_dir
        except Exception as e:
            logger.error(f"Failed to unzip IPA: {str(e)}")
            return None
            
    def _repackage_ipa(self, app_dir: str) -> Optional[str]:
        """Repackage signed app into IPA"""
        try:
            output_path = os.path.join(self.temp_dir, 'signed.ipa')
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for root, _, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, self.temp_dir)
                        zip_ref.write(file_path, arc_path)
                        
            return output_path
        except Exception as e:
            logger.error(f"Failed to repackage IPA: {str(e)}")
            return None
            
    def sign(self) -> Optional[str]:
        """
        Sign the IPA file
        Returns: Path to signed IPA or None if signing fails
        """
        try:
            # Load certificate and profile
            if not self.cert_handler.load():
                raise Exception("Failed to load certificate")
                
            if not self.profile.load():
                raise Exception("Failed to load provisioning profile")
                
            # Check profile validity
            if not self.profile.is_valid():
                raise Exception("Provisioning profile is expired or invalid")
                
            # Unzip IPA
            app_dir = self._unzip_ipa()
            if not app_dir:
                raise Exception("Failed to unzip IPA")
                
            # Update Info.plist
            if not self._update_info_plist(app_dir):
                raise Exception("Failed to update Info.plist")
                
            # Copy provisioning profile
            profile_dest = os.path.join(app_dir, 'embedded.mobileprovision')
            shutil.copy2(self.profile.profile_path, profile_dest)
                
            # Sign all binaries
            entitlements = self.profile.get_entitlements()
            if not entitlements:
                raise Exception("Failed to get entitlements from profile")
                
            binaries = self._find_binaries(app_dir)
            for binary in binaries:
                if not self._sign_binary(binary, entitlements):
                    raise Exception(f"Failed to sign binary: {binary}")
                    
            # Repackage IPA
            signed_ipa = self._repackage_ipa(app_dir)
            if not signed_ipa:
                raise Exception("Failed to repackage IPA")
                
            return signed_ipa
            
        except Exception as e:
            logger.error(f"Signing failed: {str(e)}")
            return None
