# NDI SDK and DirectML Setup

This directory contains the setup script for NDI SDK and DirectML integration with Python 3.14 compatibility.

## Problem Fixed

The original issue was a Python 3.14 deprecation warning when extracting tar archives:

```
DeprecationWarning: Python 3.14 will, by default, filter extracted tar archives and reject files or modify their metadata. Use the filter argument to control this behavior.
  tar.extractall(temp_dir)
```

## Solution

The `setup_directml.py` script now includes proper handling for Python 3.14's tar extraction requirements by:

1. **Using the filter argument**: For Python 3.12+, uses `tar.extractall(path, filter='data')`
2. **Backward compatibility**: Maintains support for older Python versions
3. **Proper error handling**: Includes comprehensive error handling and logging
4. **Safe extraction**: Uses the 'data' filter which is appropriate for data archives

## Usage

### Basic Setup

```bash
python3 src/setup_directml.py
```

### Manual Steps

If you prefer to run the steps manually:

```python
from src.setup_directml import NDISDKSetup

setup = NDISDKSetup()
setup.run_setup()
```

## What the Script Does

1. **Downloads NDI SDK**: Downloads the official NDI SDK for Linux
2. **Extracts with Python 3.14 compatibility**: Uses proper filter arguments
3. **Sets up Python environment**: Creates virtual environment and upgrades pip
4. **Installs DirectML dependencies**: Installs torch, torch-directml, and related packages
5. **Cleanup**: Removes temporary files

## Python 3.14 Compatibility Features

### Tar Extraction
- Uses `filter='data'` for Python 3.12+ (forward compatible with 3.14)
- Falls back to legacy method for older Python versions
- Prevents potential security issues with unsafe tar files

### Version Detection
```python
if sys.version_info >= (3, 12):
    tar.extractall(extract_dir, filter='data')
else:
    tar.extractall(extract_dir)
```

## Error Handling

The script provides detailed error messages and logging:
- `[]` - Info messages
- `[!]` - Error/Warning messages  
- `[✓]` - Success messages

## Testing

Run the test suite to verify functionality:

```bash
python3 tests/test_setup_directml.py
```

The tests verify:
- Python version compatibility
- Tar extraction with proper filter usage
- Download functionality (mocked)
- Error handling
- Cleanup operations

## Requirements

- Python 3.7+ (recommended: Python 3.12+ for full compatibility)
- Internet connection for downloading NDI SDK
- Sufficient disk space for SDK extraction

## Troubleshooting

### "Could not find extracted NDI SDK directory"

This error means the tar extraction succeeded but the expected directory structure wasn't found. The script now handles this by:
1. Looking for directories containing 'ndi' or 'sdk' in the name
2. Falling back to the extraction root if specific directories aren't found
3. Providing detailed error messages

### Python 3.14 Compatibility

The script is forward-compatible with Python 3.14 by using the `filter='data'` argument for tar extraction, which:
- Prevents the deprecation warning
- Ensures safe extraction of data archives
- Maintains compatibility with current Python versions

## File Structure After Setup

```
project/
├── venv/                     # Python virtual environment
├── src/
│   └── setup_directml.py    # Setup script
└── temp/                    # Temporary files (cleaned up automatically)
```