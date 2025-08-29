#!/usr/bin/env python3
"""
Simple test script for ShadowRecon main.py
Tests basic functionality without requiring NDI hardware
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the main directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test that basic imports work"""
    print("Testing basic imports...")
    
    try:
        from main import (
            AppConfig, Logger, ErrorHandler, Utils, 
            FileManager, DataCollector, ShadowReconApp
        )
        print("✓ Basic imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("Testing configuration...")
    
    try:
        from main import AppConfig
        
        # Test default config
        config = AppConfig()
        assert config.max_redraw_fps == 300
        assert config.log_level == "INFO"
        
        print("✓ Configuration test passed")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_logger():
    """Test logging functionality"""
    print("Testing logger...")
    
    try:
        from main import Logger
        
        logger = Logger("Test", "INFO")
        logger.info("Test message")
        logger.warning("Test warning")
        
        print("✓ Logger test passed")
        return True
    except Exception as e:
        print(f"✗ Logger test failed: {e}")
        return False

def test_utils():
    """Test utility functions"""
    print("Testing utilities...")
    
    try:
        from main import Utils
        
        # Test ID generation
        test_id = Utils.generate_id(10)
        assert len(test_id) == 10
        
        # Test system info
        sys_info = Utils.get_system_info()
        assert 'hostname' in sys_info
        assert 'username' in sys_info
        
        # Test directory creation
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = os.path.join(temp_dir, "test_subdir")
            result = Utils.ensure_directory(test_path)
            assert result.exists()
        
        print("✓ Utils test passed")
        return True
    except Exception as e:
        print(f"✗ Utils test failed: {e}")
        return False

def test_file_manager():
    """Test file manager functionality"""
    print("Testing file manager...")
    
    try:
        from main import FileManager, AppConfig, Logger
        
        config = AppConfig()
        logger = Logger("Test", "INFO")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config.temp_dir = temp_dir
            config.output_dir = temp_dir
            
            fm = FileManager(config, logger)
            fm.initialize()
            
            # Test saving data
            test_data = {"test": "data", "number": 42}
            result = fm.save_data(test_data, "test.json", "TestFolder")
            assert result is not None
            assert result.exists()
            
            # Test stats
            stats = fm.stats
            assert stats['files_processed'] > 0
            
            print("✓ File manager test passed")
            return True
            
    except Exception as e:
        print(f"✗ File manager test failed: {e}")
        return False

def test_data_collector():
    """Test data collector"""
    print("Testing data collector...")
    
    try:
        from main import DataCollector, FileManager, AppConfig, Logger
        
        config = AppConfig()
        logger = Logger("Test", "INFO")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config.temp_dir = temp_dir
            config.output_dir = temp_dir
            
            fm = FileManager(config, logger)
            fm.initialize()
            
            collector = DataCollector(config, logger, fm)
            
            # Test system info collection
            sys_info = collector.collect_system_information()
            assert isinstance(sys_info, dict)
            
            # Test summary
            summary = collector.get_collection_summary()
            assert 'modules_executed' in summary
            
            print("✓ Data collector test passed")
            return True
            
    except Exception as e:
        print(f"✗ Data collector test failed: {e}")
        return False

def test_app_initialization():
    """Test main application initialization"""
    print("Testing app initialization...")
    
    try:
        from main import ShadowReconApp
        
        app = ShadowReconApp()
        success = app.initialize()
        assert success
        
        # Test cleanup
        app.cleanup()
        
        print("✓ App initialization test passed")
        return True
        
    except Exception as e:
        print(f"✗ App initialization test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("ShadowRecon Main.py Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_configuration,
        test_logger,
        test_utils,
        test_file_manager,
        test_data_collector,
        test_app_initialization,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print()
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())