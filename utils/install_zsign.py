import os
import subprocess
import logging
import shutil
import tempfile

logger = logging.getLogger(__name__)

def install_zsign() -> bool:
    """
    Install zsign binary from source
    Returns: True if installation successful, False otherwise
    """
    try:
        # Check if zsign is already installed
        if shutil.which('zsign'):
            return True
            
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Clone zsign repository
            subprocess.run(
                ['git', 'clone', 'https://github.com/zhlynn/zsign.git', temp_dir],
                check=True,
                capture_output=True
            )
            
            # Build zsign
            subprocess.run(
                ['make'],
                cwd=temp_dir,
                check=True,
                capture_output=True
            )
            
            # Move binary to /usr/local/bin
            zsign_path = os.path.join(temp_dir, 'zsign')
            if os.path.exists(zsign_path):
                dest_path = '/usr/local/bin/zsign'
                shutil.copy2(zsign_path, dest_path)
                os.chmod(dest_path, 0o755)
                return True
                
            return False
            
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install zsign: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Failed to install zsign: {str(e)}")
        return False
