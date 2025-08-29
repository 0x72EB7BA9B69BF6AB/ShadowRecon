#!/usr/bin/env python3
"""
ShadowRecon Demo Script
Demonstrates the main functionality without requiring NDI hardware
"""

import sys
import os
import tempfile

# Add the main directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_basic_functionality():
    """Demonstrate basic functionality"""
    print("🎬 ShadowRecon v3.0 - Demo Mode")
    print("=" * 50)
    
    try:
        from main import ShadowReconApp, AppConfig
        
        # Create a custom config for demo
        config = AppConfig()
        config.log_level = "INFO"
        config.output_dir = "./demo_output"
        
        print("✓ Initializing ShadowRecon application...")
        
        with ShadowReconApp() as app:
            app.config = config
            
            print("✓ Running data collection...")
            success = app.run_data_collection()
            
            if success:
                print("✓ Data collection completed successfully")
                
                print("✓ Creating archive...")
                archive_path = app.create_final_archive()
                
                if archive_path:
                    print(f"✓ Archive created: {archive_path}")
                    
                    # Show statistics
                    print("\n📊 Statistics:")
                    app._display_statistics()
                else:
                    print("❌ Failed to create archive")
            else:
                print("❌ Data collection failed")
        
        print("\n🎉 Demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

def demo_configuration():
    """Demonstrate configuration system"""
    print("\n🔧 Configuration Demo")
    print("-" * 30)
    
    try:
        from main import AppConfig
        
        # Default config
        config = AppConfig()
        print(f"Default FPS cap: {config.max_redraw_fps}")
        print(f"Default log level: {config.log_level}")
        print(f"Default output dir: {config.output_dir}")
        
        # Modified config
        config.max_redraw_fps = 150
        config.log_level = "DEBUG"
        config.output_dir = "./custom_output"
        
        print(f"Modified FPS cap: {config.max_redraw_fps}")
        print(f"Modified log level: {config.log_level}")
        print(f"Modified output dir: {config.output_dir}")
        
        print("✓ Configuration system working")
        return True
        
    except Exception as e:
        print(f"❌ Configuration demo failed: {e}")
        return False

def demo_file_operations():
    """Demonstrate file management"""
    print("\n📁 File Operations Demo")
    print("-" * 30)
    
    try:
        from main import FileManager, AppConfig, Logger
        
        config = AppConfig()
        logger = Logger("Demo", "INFO")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config.temp_dir = temp_dir
            config.output_dir = temp_dir
            
            fm = FileManager(config, logger)
            fm.initialize()
            
            # Save various types of data
            test_data = {
                "demo": True,
                "timestamp": "2024-01-01T12:00:00",
                "numbers": [1, 2, 3, 4, 5]
            }
            
            # Save JSON data
            result1 = fm.save_data(test_data, "demo.json", "Demo")
            print(f"✓ Saved JSON: {result1}")
            
            # Save text data
            result2 = fm.save_data("Hello, ShadowRecon!", "demo.txt", "Demo")
            print(f"✓ Saved text: {result2}")
            
            # Save binary data
            result3 = fm.save_data(b"Binary data example", "demo.bin", "Demo")
            print(f"✓ Saved binary: {result3}")
            
            # Show stats
            stats = fm.stats
            print(f"✓ Files processed: {stats['files_processed']}")
            print(f"✓ Total size: {stats['total_size']} bytes")
            
            # Create archive
            archive = fm.create_archive()
            if archive:
                print(f"✓ Archive created: {archive}")
            
        print("✓ File operations demo successful")
        return True
        
    except Exception as e:
        print(f"❌ File operations demo failed: {e}")
        return False

def demo_ndi_info():
    """Show NDI information"""
    print("\n📺 NDI System Info")
    print("-" * 30)
    
    try:
        from main import NDI_AVAILABLE, NDIManager, AppConfig, Logger
        
        if NDI_AVAILABLE:
            print("✓ NDI dependencies available")
            print("✓ Can use full NDI functionality")
            
            config = AppConfig()
            logger = Logger("NDI Demo", "INFO")
            
            ndi = NDIManager(config, logger)
            print(f"✓ NDI Manager initialized")
            print(f"✓ Max FPS: {config.max_redraw_fps}")
            print(f"✓ FOV enabled: {ndi.use_fov}")
            print(f"✓ Default FOV size: {ndi.fov_size}")
            
        else:
            print("❌ NDI dependencies not available")
            print("💡 Install with: pip install cyndilib opencv-python numpy")
            print("💡 Download NDI SDK from: https://www.ndi.tv/sdk/")
            
        return True
        
    except Exception as e:
        print(f"❌ NDI info demo failed: {e}")
        return False

def main():
    """Run all demos"""
    print("🎯 ShadowRecon v3.0 - Complete Demo Suite")
    print("=" * 70)
    
    demos = [
        ("Basic Functionality", demo_basic_functionality),
        ("Configuration System", demo_configuration),
        ("File Operations", demo_file_operations),
        ("NDI Information", demo_ndi_info),
    ]
    
    results = []
    
    for name, demo_func in demos:
        print(f"\n🔹 Running: {name}")
        try:
            success = demo_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 Demo Results Summary")
    print("=" * 70)
    
    passed = 0
    for name, success in results:
        status = "✓ PASS" if success else "❌ FAIL"
        print(f"{status:<8} {name}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} demos passed")
    
    if passed == len(results):
        print("\n🎉 All demos completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Install NDI dependencies for full functionality")
        print("   2. Run: python main.py --mode interactive")
        print("   3. Try: python main.py --mode auto")
        return 0
    else:
        print("\n⚠️  Some demos had issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())