import os
import requests
import subprocess
import logging
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_zsign_installation(zsign_path):
    """Test if zsign is working properly"""
    try:
        result = subprocess.run([zsign_path, '-v'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error testing zsign: {str(e)}")
        return False

def install_via_package_manager():
    """Try installing zsign via package manager"""
    try:
        logger.info("Attempting to install zsign via package manager...")
        result = subprocess.run(['nix-env', '-iA', 'nixpkgs.zsign'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            zsign_path = subprocess.run(['which', 'zsign'], 
                                      capture_output=True, text=True).stdout.strip()
            if zsign_path and test_zsign_installation(zsign_path):
                logger.info("Successfully installed zsign via package manager")
                return True
                
        logger.warning("Failed to install zsign via package manager")
        return False
    except Exception as e:
        logger.error(f"Error during package manager installation: {str(e)}")
        return False

def install_via_binary():
    """Download and install pre-built zsign binary"""
    bin_dir = Path('/home/runner/bin')
    bin_dir.mkdir(exist_ok=True)
    zsign_path = bin_dir / 'zsign'
    
    try:
        logger.info("Attempting to download pre-built zsign binary...")
        response = requests.get(
            'https://github.com/zhlynn/zsign/releases/download/v1.1.0/zsign-linux',
            allow_redirects=True
        )
        response.raise_for_status()
        
        with open(zsign_path, 'wb') as f:
            f.write(response.content)
        
        os.chmod(zsign_path, 0o755)
        os.environ['PATH'] = f"{bin_dir}:{os.environ.get('PATH', '')}"
        
        if test_zsign_installation(zsign_path):
            logger.info("Successfully installed zsign binary")
            return True
            
        logger.warning("Binary installation failed verification")
        return False
    except Exception as e:
        logger.error(f"Error during binary installation: {str(e)}")
        return False

def install_from_source():
    """Compile and install zsign from source"""
    try:
        logger.info("Attempting to compile zsign from source...")
        
        # Install dependencies
        subprocess.run(['nix-env', '-iA', 'nixpkgs.openssl', 'nixpkgs.gcc'], 
                      check=True)
        
        # Clone repository
        subprocess.run(['git', 'clone', 'https://github.com/zhlynn/zsign.git', 
                       '/tmp/zsign'], check=True)
        
        # Build zsign
        build_cmd = [
            'g++', '*.cpp', 'common/*.cpp',
            '-std=gnu++11', '-lcrypto', '-O3', '-o', 'zsign'
        ]
        subprocess.run(build_cmd, cwd='/tmp/zsign', check=True)
        
        # Install to bin directory
        bin_dir = Path('/home/runner/bin')
        bin_dir.mkdir(exist_ok=True)
        shutil.copy('/tmp/zsign/zsign', bin_dir / 'zsign')
        os.chmod(bin_dir / 'zsign', 0o755)
        
        if test_zsign_installation(bin_dir / 'zsign'):
            logger.info("Successfully compiled and installed zsign from source")
            return True
            
        logger.warning("Source compilation failed verification")
        return False
    except Exception as e:
        logger.error(f"Error during source compilation: {str(e)}")
        return False
    finally:
        # Cleanup
        if os.path.exists('/tmp/zsign'):
            shutil.rmtree('/tmp/zsign')

def install_zsign():
    """
    Install zsign using multiple methods in order of preference:
    1. Package manager
    2. Pre-built binary
    3. Compile from source
    """
    logger.info("Starting zsign installation process...")
    
    # Check if zsign is already installed
    zsign_path = Path('/home/runner/bin/zsign')
    if zsign_path.exists() and os.access(zsign_path, os.X_OK):
        if test_zsign_installation(zsign_path):
            logger.info("zsign is already installed and working")
            return True
        else:
            logger.warning("Existing zsign installation is broken, attempting reinstall")
    
    # Try each installation method in sequence
    if install_via_package_manager():
        return True
        
    logger.info("Package manager installation failed, trying binary download...")
    if install_via_binary():
        return True
        
    logger.info("Binary installation failed, trying source compilation...")
    if install_from_source():
        return True
        
    error_msg = "Failed to install zsign through all available methods"
    logger.error(error_msg)
    raise Exception(error_msg)

if __name__ == '__main__':
    install_zsign()
