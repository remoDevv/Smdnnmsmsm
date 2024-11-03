import os
import requests
import subprocess
from pathlib import Path

def install_zsign():
    """
    Download and install zsign binary
    """
    # Create bin directory if it doesn't exist
    bin_dir = Path('/home/runner/bin')
    bin_dir.mkdir(exist_ok=True)
    
    zsign_path = bin_dir / 'zsign'
    
    # If zsign already exists and is executable, we're done
    if zsign_path.exists() and os.access(zsign_path, os.X_OK):
        return True
        
    try:
        # Download zsign binary
        response = requests.get(
            'https://github.com/zhlynn/zsign/releases/download/v1.1.0/zsign-linux',
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Save binary
        with open(zsign_path, 'wb') as f:
            f.write(response.content)
        
        # Make executable
        os.chmod(zsign_path, 0o755)
        
        # Add to PATH if not already there
        os.environ['PATH'] = f"{bin_dir}:{os.environ.get('PATH', '')}"
        
        # Test zsign
        result = subprocess.run(['zsign', '-v'], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"zsign test failed: {result.stderr}")
            
        return True
        
    except Exception as e:
        print(f"Error installing zsign: {str(e)}")
        return False

if __name__ == '__main__':
    install_zsign()
