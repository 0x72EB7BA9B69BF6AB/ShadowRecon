# ShadowRecon v3.0 - Python Edition with NDI Support

A clean, efficient, and well-structured application that orchestrates data collection with advanced NDI (Network Device Interface) video streaming capabilities.

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt

# For NDI support, you may also need the NDI SDK
# Download from: https://www.ndi.tv/sdk/
```

### Basic Usage

```bash
# Interactive mode (default)
python main.py

# Automatic mode (non-interactive)
python main.py --mode auto

# NDI viewer only
python main.py --mode ndi-only

# Custom configuration
python main.py --config shadowrecon_config.json --log-level DEBUG
```

## 🏗️ Architecture

This single `main.py` file orchestrates everything with clean separation of concerns:

### Core Components

- **AppConfig**: Centralized configuration management
- **Logger**: Structured logging system
- **ErrorHandler**: Comprehensive error handling
- **Utils**: Core utility functions
- **FileManager**: Advanced file operations and archiving
- **DataCollector**: System data collection
- **NDIManager**: High-performance NDI video streaming
- **ShadowReconApp**: Main application orchestrator

### Key Features

1. **Modular Design**: Each class has a specific, well-defined purpose
2. **Efficient Operation**: Optimized for performance with configurable settings
3. **NDI Integration**: Advanced video streaming with FOV control and 300 FPS cap
4. **Error Resilience**: Comprehensive error handling throughout
5. **Interactive & Automated Modes**: Flexible execution options

## 🎯 NDI Features

### Video Streaming Capabilities

- **High Performance**: Up to 300 FPS with intelligent frame rate limiting
- **FOV Control**: Configurable field of view (256x256 to 640x640 or full screen)
- **Auto-Discovery**: Automatic NDI source detection and connection
- **Optimized Rendering**: Efficient color format handling (BGRX/RGBA)
- **Real-time Stats**: Live FPS monitoring and performance metrics

### NDI Configuration Options

1. **256x256** - Small FOV (good for detail focus)
2. **320x320** - Medium FOV 
3. **480x480** - Large FOV
4. **640x640** - Extra-large FOV
5. **Full Screen** - Complete source display
6. **Custom Size** - User-defined dimensions (64-4096)

## 📋 Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --config, -c PATH     Configuration file path
  --mode, -m MODE       Application mode: interactive|auto|ndi-only
  --log-level, -l LEVEL Logging level: DEBUG|INFO|WARNING|ERROR
  --output-dir, -o DIR  Output directory for archives
  --help                Show help message
```

## ⚙️ Configuration

Edit `shadowrecon_config.json` to customize:

```json
{
  "max_redraw_fps": 300,        // Maximum display FPS
  "light_sleep_us": 0,          // Micro-sleep between frames (microseconds)
  "keep_gc_disabled": true,     // Disable garbage collection during operation
  "fps_report_interval": 2.0,   // FPS reporting interval (seconds)
  "ema_alpha": 0.18,           // FPS smoothing factor
  "log_level": "INFO",         // Logging verbosity
  "collect_screenshots": true,  // Enable screenshot capture
  "collect_system_info": true   // Enable system info collection
}
```

## 🧪 Testing

Run the test suite to verify functionality:

```bash
python test_main.py
```

## 📁 Output Structure

Generated archives contain organized data:

```
output/
├── shadowrecon_YYYYMMDD_HHMMSS.zip
└── Archives contain:
    ├── System/
    │   └── system_info.json
    ├── Screenshots/
    │   └── screenshot_YYYYMMDD_HHMMSS.png
    └── Reports/
        └── collection_summary.json
```

## 🔧 Advanced Usage

### Performance Tuning

- Adjust `max_redraw_fps` for different display performance
- Set `light_sleep_us` for CPU usage control
- Configure `ema_alpha` for FPS smoothing responsiveness

### Integration Examples

```python
# Use as a module
from main import ShadowReconApp

with ShadowReconApp("custom_config.json") as app:
    app.run_data_collection()
    app.create_final_archive()
```

## ⚠️ Requirements

- Python 3.7+
- OpenCV (opencv-python)
- NumPy
- cyndilib (for NDI support)
- Pillow (for screenshots)

## 🚨 Important Notice

This tool is designed for **educational purposes** and **authorized testing only**. Users must ensure compliance with all applicable laws and regulations.

## 📝 License

MIT License - see original repository for details.