#!/usr/bin/env python3
"""
NDI SDK Setup Script for DirectML Integration
Handles downloading and extraction of NDI SDK with Python 3.14 compatibility
"""

import os
import sys
import tarfile
import urllib.request
import urllib.error
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Optional


class NDISDKSetup:
    """NDI SDK Setup and Installation Manager"""
    
    def __init__(self):
        self.ndi_sdk_url = "https://downloads.ndi.tv/SDK/NDI_SDK_Linux/Install_NDI_SDK_v6_Linux.tar.gz"
        self.temp_dir = None
        self.extracted_dir = None
        
    def log(self, message: str, level: str = "INFO") -> None:
        """Log messages with proper formatting"""
        prefix = {
            "INFO": "[]",
            "ERROR": "[!]",
            "SUCCESS": "[✓]",
            "WARNING": "[!]"
        }
        print(f"{prefix.get(level, '[]')} {message}")
        
    def download_ndi_sdk(self) -> bool:
        """Download NDI SDK from official source"""
        try:
            self.log("Downloading NDI SDK from https://downloads.ndi.tv/SDK/NDI_SDK_Linux/Install_NDI_SDK_v6_Linux.tar.gz...")
            
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="ndi_sdk_")
            sdk_archive = os.path.join(self.temp_dir, "ndi_sdk.tar.gz")
            
            # Download with progress indication
            urllib.request.urlretrieve(self.ndi_sdk_url, sdk_archive)
            
            # Verify download
            if os.path.exists(sdk_archive) and os.path.getsize(sdk_archive) > 0:
                self.log("NDI SDK downloaded successfully", "SUCCESS")
                return True
            else:
                self.log("Download verification failed", "ERROR")
                return False
                
        except urllib.error.URLError as e:
            self.log(f"Download failed: {e}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Unexpected error during download: {e}", "ERROR")
            return False
    
    def extract_ndi_sdk(self) -> bool:
        """Extract NDI SDK with Python 3.14 compatibility"""
        try:
            self.log("Extracting NDI SDK...")
            
            sdk_archive = os.path.join(self.temp_dir, "ndi_sdk.tar.gz")
            extract_dir = os.path.join(self.temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            # Extract with Python 3.14 compatibility
            with tarfile.open(sdk_archive, 'r:gz') as tar:
                # Use filter argument for Python 3.14 compatibility
                # 'data' filter is the safest option for data archives
                if sys.version_info >= (3, 12):
                    # For Python 3.12+, use the filter argument
                    tar.extractall(extract_dir, filter='data')
                else:
                    # For older Python versions, use the legacy method
                    tar.extractall(extract_dir)
            
            # Find the extracted NDI SDK directory
            extracted_contents = os.listdir(extract_dir)
            ndi_directories = [d for d in extracted_contents 
                             if os.path.isdir(os.path.join(extract_dir, d)) 
                             and ('ndi' in d.lower() or 'sdk' in d.lower())]
            
            if ndi_directories:
                self.extracted_dir = os.path.join(extract_dir, ndi_directories[0])
                self.log(f"NDI SDK extracted to: {self.extracted_dir}", "SUCCESS")
                return True
            else:
                # If no NDI-specific directory found, check if extraction was successful
                if extracted_contents:
                    self.extracted_dir = extract_dir
                    self.log(f"SDK extracted to: {self.extracted_dir}", "SUCCESS")
                    return True
                else:
                    self.log("Could not find extracted NDI SDK directory", "ERROR")
                    return False
                    
        except tarfile.TarError as e:
            self.log(f"Extraction failed: {e}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Unexpected error during extraction: {e}", "ERROR")
            return False
    
    def setup_python_environment(self) -> bool:
        """Setup Python virtual environment and upgrade pip"""
        try:
            self.log("Setting up Python environment...")
            
            # Create virtual environment if it doesn't exist
            venv_path = os.path.join(os.getcwd(), "venv")
            if not os.path.exists(venv_path):
                subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
                self.log("Virtual environment created", "SUCCESS")
            
            # Determine pip executable path
            if os.name == "nt":  # Windows
                pip_path = os.path.join(venv_path, "Scripts", "pip")
                python_path = os.path.join(venv_path, "Scripts", "python")
            else:  # Unix/Linux/macOS
                pip_path = os.path.join(venv_path, "bin", "pip")
                python_path = os.path.join(venv_path, "bin", "python")
            
            # Upgrade pip inside venv
            self.log("Upgrading pip inside venv...")
            subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            self.log("Python environment setup completed", "SUCCESS")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"Python environment setup failed: {e}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Unexpected error during environment setup: {e}", "ERROR")
            return False
    
    def install_directml_dependencies(self) -> bool:
        """Install DirectML and related dependencies"""
        try:
            self.log("Installing DirectML dependencies...")
            
            venv_path = os.path.join(os.getcwd(), "venv")
            
            # Determine python executable path
            if os.name == "nt":  # Windows
                python_path = os.path.join(venv_path, "Scripts", "python")
            else:  # Unix/Linux/macOS
                python_path = os.path.join(venv_path, "bin", "python")
            
            # Install common DirectML dependencies
            dependencies = [
                "torch",
                "torch-directml",
                "numpy",
                "opencv-python"
            ]
            
            for dep in dependencies:
                self.log(f"Installing {dep}...")
                subprocess.run([python_path, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
            
            self.log("DirectML dependencies installed successfully", "SUCCESS")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"Dependency installation failed: {e}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Unexpected error during dependency installation: {e}", "ERROR")
            return False
    
    def cleanup(self) -> None:
        """Clean up temporary files"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.log("Temporary files cleaned up", "SUCCESS")
        except Exception as e:
            self.log(f"Cleanup warning: {e}", "WARNING")
    
    def run_setup(self) -> bool:
        """Run complete NDI SDK setup process"""
        try:
            self.log("Starting NDI SDK and DirectML setup...")
            
            # Step 1: Download NDI SDK
            if not self.download_ndi_sdk():
                return False
            
            # Step 2: Extract NDI SDK with Python 3.14 compatibility
            if not self.extract_ndi_sdk():
                return False
            
            # Step 3: Setup Python environment
            if not self.setup_python_environment():
                return False
            
            # Step 4: Install DirectML dependencies
            if not self.install_directml_dependencies():
                return False
            
            self.log("NDI SDK and DirectML setup completed successfully!", "SUCCESS")
            return True
            
        except KeyboardInterrupt:
            self.log("Setup interrupted by user", "WARNING")
            return False
        except Exception as e:
            self.log(f"Setup failed with unexpected error: {e}", "ERROR")
            return False
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    setup = NDISDKSetup()
    success = setup.run_setup()
    
    if success:
        print("\n" + "="*50)
        print("Setup completed successfully!")
        print("You can now use NDI SDK with DirectML.")
        print("="*50)
        sys.exit(0)
    else:
        print("\n" + "="*50)
        print("Setup failed. Please check the error messages above.")
        print("="*50)
        sys.exit(1)


if __name__ == "__main__":
    main()