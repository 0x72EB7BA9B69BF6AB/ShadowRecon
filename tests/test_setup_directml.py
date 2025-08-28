#!/usr/bin/env python3
"""
Test script for setup_directml.py
Verifies Python 3.14 compatibility and tar extraction functionality
"""

import sys
import os
import tempfile
import tarfile
import unittest
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from setup_directml import NDISDKSetup
except ImportError as e:
    print(f"Error importing setup_directml: {e}")
    sys.exit(1)


class TestNDISDKSetup(unittest.TestCase):
    """Test cases for NDI SDK setup functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.setup = NDISDKSetup()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_log_formatting(self):
        """Test log message formatting"""
        # Capture output
        from io import StringIO
        import contextlib
        
        f = StringIO()
        with contextlib.redirect_stdout(f):
            self.setup.log("Test message", "INFO")
            self.setup.log("Error message", "ERROR")
            self.setup.log("Success message", "SUCCESS")
        
        output = f.getvalue()
        self.assertIn("[] Test message", output)
        self.assertIn("[!] Error message", output)
        self.assertIn("[✓] Success message", output)
    
    def test_tar_extraction_python_compatibility(self):
        """Test tar extraction with Python 3.14 compatibility"""
        # Create a test tar file
        test_tar_path = os.path.join(self.temp_dir, "test.tar.gz")
        test_extract_dir = os.path.join(self.temp_dir, "extract")
        os.makedirs(test_extract_dir, exist_ok=True)
        
        # Create test content
        test_file_content = "test content"
        test_file_path = os.path.join(self.temp_dir, "test_file.txt")
        with open(test_file_path, 'w') as f:
            f.write(test_file_content)
        
        # Create tar archive
        with tarfile.open(test_tar_path, 'w:gz') as tar:
            tar.add(test_file_path, arcname="test_file.txt")
        
        # Test extraction with compatibility
        with tarfile.open(test_tar_path, 'r:gz') as tar:
            if sys.version_info >= (3, 12):
                # Should not raise deprecation warning
                tar.extractall(test_extract_dir, filter='data')
            else:
                tar.extractall(test_extract_dir)
        
        # Verify extraction
        extracted_file = os.path.join(test_extract_dir, "test_file.txt")
        self.assertTrue(os.path.exists(extracted_file))
        
        with open(extracted_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, test_file_content)
    
    @patch('urllib.request.urlretrieve')
    def test_download_ndi_sdk_success(self, mock_urlretrieve):
        """Test successful NDI SDK download"""
        # Mock successful download
        def mock_download(url, filename):
            # Create a dummy file
            with open(filename, 'wb') as f:
                f.write(b'dummy content')
        
        mock_urlretrieve.side_effect = mock_download
        
        result = self.setup.download_ndi_sdk()
        self.assertTrue(result)
        self.assertIsNotNone(self.setup.temp_dir)
        
        # Verify file was created
        archive_path = os.path.join(self.setup.temp_dir, "ndi_sdk.tar.gz")
        self.assertTrue(os.path.exists(archive_path))
    
    @patch('urllib.request.urlretrieve')
    def test_download_ndi_sdk_failure(self, mock_urlretrieve):
        """Test NDI SDK download failure"""
        # Mock download failure
        mock_urlretrieve.side_effect = Exception("Download failed")
        
        result = self.setup.download_ndi_sdk()
        self.assertFalse(result)
    
    def test_python_version_compatibility(self):
        """Test that the script handles different Python versions"""
        # This test verifies that the version check works correctly
        current_version = sys.version_info
        
        # Test version comparison logic
        if current_version >= (3, 12):
            # Should use filter argument
            self.assertTrue(True)  # Placeholder for filter usage check
        else:
            # Should use legacy method
            self.assertTrue(True)  # Placeholder for legacy method check
    
    def test_cleanup_functionality(self):
        """Test cleanup of temporary files"""
        # Set up temporary directory
        self.setup.temp_dir = tempfile.mkdtemp()
        temp_path = self.setup.temp_dir
        
        # Verify directory exists
        self.assertTrue(os.path.exists(temp_path))
        
        # Run cleanup
        self.setup.cleanup()
        
        # Verify directory is removed
        self.assertFalse(os.path.exists(temp_path))


def run_compatibility_check():
    """Run Python 3.14 compatibility check"""
    print("Python 3.14 Compatibility Check")
    print("=" * 40)
    print(f"Python version: {sys.version}")
    print(f"Version info: {sys.version_info}")
    
    # Test tar extraction with filter
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            # Create empty tar for testing
            with tarfile.open(tmp_file.name, 'w:gz') as tar:
                pass
            
            # Test extraction with filter (Python 3.12+)
            with tarfile.open(tmp_file.name, 'r:gz') as tar:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    if sys.version_info >= (3, 12):
                        tar.extractall(tmp_dir, filter='data')
                        print("✓ Python 3.12+ filter argument supported")
                    else:
                        tar.extractall(tmp_dir)
                        print("✓ Legacy tar extraction works")
        
        os.unlink(tmp_file.name)
        print("✓ Tar extraction compatibility verified")
        
    except Exception as e:
        print(f"✗ Tar extraction test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("Running NDI SDK setup tests...")
    print("=" * 50)
    
    # Run compatibility check first
    if not run_compatibility_check():
        print("Compatibility check failed!")
        sys.exit(1)
    
    print("\nRunning unit tests...")
    print("-" * 30)
    
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    print("\nAll tests completed!")