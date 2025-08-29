#!/usr/bin/env python3
"""
ShadowRecon v3.0 - Main Application with NDI Integration
================================================================

A comprehensive application that combines data collection capabilities 
with advanced NDI (Network Device Interface) video streaming functionality.

This main file orchestrates all operations efficiently with clear separation
of concerns and optimized performance.

Features:
- NDI Video Streaming with FOV (Field of View) control
- High-performance video capture (up to 300 FPS cap)
- Data collection and file management
- Clean modular architecture
- Comprehensive error handling and logging

Author: ShadowRecon Team
Version: 3.0.0
License: MIT
"""

import sys
import os
import time
import logging
import threading
import queue
import json
import gc
from typing import Optional, Dict, Any, List, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from contextlib import contextmanager

# NDI and video processing imports
try:
    import cv2
    import numpy as np
    from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
    from cyndilib.finder import Finder
    from cyndilib.receiver import Receiver
    from cyndilib.video_frame import VideoFrameSync
    from cyndilib.audio_frame import AudioFrameSync
    NDI_AVAILABLE = True
    # Type hints for numpy
    NDArray = np.ndarray
except ImportError as e:
    print(f"[WARNING] NDI dependencies not available: {e}")
    print("Install with: pip install cyndilib opencv-python numpy")
    NDI_AVAILABLE = False
    # Define dummy modules to allow import
    cv2 = None
    np = None
    # Fallback type hint
    NDArray = Any

# File operations and utilities
import shutil
import tempfile
import zipfile
import hashlib
from datetime import datetime


# ==================== CONFIGURATION ====================

@dataclass
class AppConfig:
    """Application configuration with sensible defaults"""
    # NDI Settings
    max_redraw_fps: int = 300
    light_sleep_us: int = 0
    keep_gc_disabled: bool = True
    fps_report_interval: float = 2.0
    ema_alpha: float = 0.18
    
    # Application Settings
    log_level: str = "INFO"
    temp_dir: Optional[str] = None
    output_dir: str = "./output"
    
    # Data Collection Settings
    collect_screenshots: bool = True
    collect_system_info: bool = True
    
    # Performance Settings
    max_workers: int = 4
    timeout_seconds: int = 30

# ==================== LOGGING SYSTEM ====================

class Logger:
    """Centralized logging system with structured output"""
    
    def __init__(self, name: str = "ShadowRecon", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        if not self.logger.handlers:
            formatter = logging.Formatter(
                '[%(asctime)s] %(name)s [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        self.logger.info(self._format_message(message, kwargs))
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(self._format_message(message, kwargs))
    
    def error(self, message: str, **kwargs):
        self.logger.error(self._format_message(message, kwargs))
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(self._format_message(message, kwargs))
    
    def _format_message(self, message: str, kwargs: Dict) -> str:
        if kwargs:
            details = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{message} | {details}"
        return message

# ==================== ERROR HANDLING ====================

class ShadowReconError(Exception):
    """Base exception for ShadowRecon application"""
    pass

class NDIError(ShadowReconError):
    """NDI-specific exceptions"""
    pass

class ConfigurationError(ShadowReconError):
    """Configuration-related exceptions"""
    pass

class ErrorHandler:
    """Centralized error handling with logging"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def handle(self, error: Exception, context: str = "") -> None:
        """Handle errors with appropriate logging and context"""
        error_type = type(error).__name__
        context_str = f" in {context}" if context else ""
        
        if isinstance(error, ShadowReconError):
            self.logger.error(f"{error_type}{context_str}: {error}")
        else:
            self.logger.error(f"Unhandled {error_type}{context_str}: {error}")
    
    @contextmanager
    def catch_and_log(self, context: str = ""):
        """Context manager for automatic error handling"""
        try:
            yield
        except Exception as e:
            self.handle(e, context)
            raise

# ==================== UTILITIES ====================

class Utils:
    """Core utility functions"""
    
    @staticmethod
    def generate_id(length: int = 10) -> str:
        """Generate cryptographically secure random ID"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Collect basic system information"""
        import platform
        import socket
        
        try:
            hostname = socket.gethostname()
            username = os.getenv('USER') or os.getenv('USERNAME') or 'unknown'
            
            return {
                'hostname': hostname,
                'username': username,
                'platform': platform.system(),
                'architecture': platform.machine(),
                'python_version': platform.python_version(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception:
            return {'error': 'Failed to collect system info'}
    
    @staticmethod
    def ensure_directory(path: str) -> Path:
        """Ensure directory exists and return Path object"""
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj
    
    @staticmethod
    def safe_remove(path: str) -> bool:
        """Safely remove file or directory"""
        try:
            path_obj = Path(path)
            if path_obj.is_file():
                path_obj.unlink()
            elif path_obj.is_dir():
                shutil.rmtree(path_obj)
            return True
        except Exception:
            return False

# ==================== FILE MANAGER ====================

class FileManager:
    """Advanced file management with archiving capabilities"""
    
    def __init__(self, config: AppConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.temp_dir = None
        self.output_dir = None
        self.files_saved = []
        self.stats = {
            'files_processed': 0,
            'total_size': 0,
            'errors': 0
        }
    
    def initialize(self) -> None:
        """Initialize file manager with temporary directories"""
        self.temp_dir = Utils.ensure_directory(
            self.config.temp_dir or tempfile.mkdtemp(prefix="shadowrecon_")
        )
        self.output_dir = Utils.ensure_directory(self.config.output_dir)
        self.logger.info("File manager initialized", 
                        temp_dir=str(self.temp_dir), 
                        output_dir=str(self.output_dir))
    
    def save_data(self, data: Any, filename: str, subfolder: str = "") -> Optional[Path]:
        """Save data to organized structure"""
        try:
            if subfolder:
                target_dir = self.temp_dir / subfolder
                Utils.ensure_directory(str(target_dir))
            else:
                target_dir = self.temp_dir
            
            file_path = target_dir / filename
            
            if isinstance(data, str):
                file_path.write_text(data, encoding='utf-8')
            elif isinstance(data, bytes):
                file_path.write_bytes(data)
            elif isinstance(data, dict):
                file_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
            else:
                file_path.write_text(str(data), encoding='utf-8')
            
            self.files_saved.append(file_path)
            self.stats['files_processed'] += 1
            self.stats['total_size'] += file_path.stat().st_size
            
            self.logger.debug(f"Saved file: {file_path}")
            return file_path
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Failed to save {filename}: {e}")
            return None
    
    def create_archive(self, password: Optional[str] = None) -> Optional[Path]:
        """Create ZIP archive of all saved files"""
        if not self.files_saved:
            self.logger.warning("No files to archive")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"shadowrecon_{timestamp}.zip"
        archive_path = self.output_dir / archive_name
        
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in self.files_saved:
                    # Calculate relative path from temp_dir
                    rel_path = file_path.relative_to(self.temp_dir)
                    zf.write(file_path, rel_path)
            
            archive_size = archive_path.stat().st_size / (1024 * 1024)  # MB
            self.logger.info("Archive created", 
                           path=str(archive_path), 
                           size_mb=f"{archive_size:.2f}",
                           files=len(self.files_saved))
            return archive_path
            
        except Exception as e:
            self.logger.error(f"Failed to create archive: {e}")
            return None
    
    def cleanup(self) -> None:
        """Clean up temporary files and directories"""
        if self.temp_dir and self.temp_dir.exists():
            Utils.safe_remove(str(self.temp_dir))
            self.logger.info("Temporary files cleaned up")

# ==================== NDI MANAGER ====================

class NDIManager:
    """
    Advanced NDI (Network Device Interface) video streaming manager
    Optimized for high performance with configurable FOV and frame rate limiting
    """
    
    def __init__(self, config: AppConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.error_handler = ErrorHandler(logger)
        
        # NDI components
        self.finder = None
        self.receiver = None
        self.video_frame = None
        self.audio_frame = None
        
        # Connection state
        self.connected = False
        self.current_source = None
        self.last_connect_attempt = 0.0
        self.connect_interval = 1.0
        
        # FOV settings
        self.use_fov = True
        self.fov_size = 256
        self.crop_coords = None
        self.source_resolution = None
        
        # Performance tracking
        self.fps_ema = 0.0
        self.last_frame_time = time.perf_counter()
        self.last_fps_report = 0.0
        
        # Frame rate limiting
        self.min_redraw_interval = (1.0 / self.config.max_redraw_fps) if self.config.max_redraw_fps > 0 else 0.0
        self.last_redraw_time = 0.0
        
        # Buffers
        self.output_bgr = None
        self.using_bgrx = False
        
        # Window management
        self.window_name = "ShadowRecon NDI Viewer"
        self.running = False
        
        # Status tracking
        self.last_status = ""
    
    def prompt_fov_configuration(self) -> None:
        """Interactive FOV configuration"""
        print("\n=== NDI FOV Configuration ===")
        print("1. 256x256 (Small)")
        print("2. 320x320 (Medium)")
        print("3. 480x480 (Large)")
        print("4. 640x640 (X-Large)")
        print("5. Full screen")
        print("6. Custom size")
        
        while True:
            try:
                choice = input("Your choice (1-6): ").strip()
                
                if choice == "1":
                    self.fov_size, self.use_fov = 256, True
                    break
                elif choice == "2":
                    self.fov_size, self.use_fov = 320, True
                    break
                elif choice == "3":
                    self.fov_size, self.use_fov = 480, True
                    break
                elif choice == "4":
                    self.fov_size, self.use_fov = 640, True
                    break
                elif choice == "5":
                    self.use_fov = False
                    break
                elif choice == "6":
                    size = int(input("Custom size (64-4096): "))
                    if 64 <= size <= 4096:
                        self.fov_size, self.use_fov = size, True
                        break
                    else:
                        print("Size must be between 64 and 4096")
                else:
                    print("Invalid choice. Please select 1-6.")
                    
            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Please try again.")
        
        if self.use_fov:
            self.logger.info(f"FOV configured: {self.fov_size}x{self.fov_size}")
        else:
            self.logger.info("Full screen mode configured")
    
    def initialize_ndi(self) -> bool:
        """Initialize NDI components"""
        if not NDI_AVAILABLE:
            raise NDIError("NDI libraries are not available")
        
        try:
            self.finder = Finder()
            self.finder.set_change_callback(lambda: None)
            self.finder.open()
            
            # Try preferred color format first
            try:
                preferred_format = getattr(RecvColorFormat, "BGRX_BGRA", RecvColorFormat.RGBX_RGBA)
                self.receiver = Receiver(
                    color_format=preferred_format,
                    bandwidth=RecvBandwidth.highest
                )
                self.using_bgrx = (preferred_format == getattr(RecvColorFormat, "BGRX_BGRA", None))
            except Exception:
                self.receiver = Receiver(
                    color_format=RecvColorFormat.RGBX_RGBA,
                    bandwidth=RecvBandwidth.highest
                )
                self.using_bgrx = False
            
            self.video_frame = VideoFrameSync()
            self.audio_frame = AudioFrameSync()
            
            self.receiver.frame_sync.set_video_frame(self.video_frame)
            self.receiver.frame_sync.set_audio_frame(self.audio_frame)
            
            self.logger.info("NDI components initialized successfully")
            return True
            
        except Exception as e:
            raise NDIError(f"Failed to initialize NDI: {e}")
    
    def try_connect_to_source(self, force: bool = False) -> bool:
        """Attempt to connect to available NDI source"""
        now = time.perf_counter()
        
        if not force and (now - self.last_connect_attempt) < self.connect_interval:
            return self.connected
        
        self.last_connect_attempt = now
        
        try:
            sources = self.finder.get_source_names() or []
        except Exception:
            sources = []
        
        if not sources:
            self._update_status("Waiting for NDI sources...")
            return False
        
        target_source = sources[0]
        
        # Check if already connected to this source
        if (self.connected and 
            self.current_source == target_source and 
            self.receiver.is_connected()):
            return True
        
        # Attempt connection
        source_obj = self.finder.get_source(target_source)
        if not source_obj:
            return False
        
        try:
            self.receiver.set_source(source_obj)
        except Exception as e:
            self._update_status(f"Connection failed: {e}")
            return False
        
        # Wait for connection establishment
        connection_start = time.perf_counter()
        while time.perf_counter() - connection_start < 2.0:
            if self.receiver.is_connected():
                self.connected = True
                self.current_source = target_source
                
                color_mode = "BGRX direct" if self.using_bgrx else "RGBA (conversion)"
                self._update_status(f"Connected to: {self.current_source} | Mode: {color_mode}")
                
                # Reset state for new source
                self.crop_coords = None
                self.source_resolution = None
                self.output_bgr = None
                
                return True
            
            time.sleep(0.012)
        
        self.connected = False
        return False
    
    def _compute_crop_coordinates(self, width: int, height: int) -> Optional[Tuple[int, int, int, int]]:
        """Compute crop coordinates for FOV"""
        if not self.use_fov:
            return None
        
        size = min(self.fov_size, width, height)
        x1 = (width - size) // 2
        y1 = (height - size) // 2
        x2 = x1 + size
        y2 = y1 + size
        
        # Ensure coordinates are within bounds
        if x1 < 0:
            x1, x2 = 0, size
        if y1 < 0:
            y1, y2 = 0, size
        if x2 > width:
            x2, x1 = width, width - size
        if y2 > height:
            y2, y1 = height, height - size
        
        return (x1, y1, x2, y2)
    
    def capture_frame(self) -> Optional[NDArray]:
        """Capture and process video frame"""
        if not NDI_AVAILABLE or not self.connected:
            return None
        
        try:
            self.receiver.frame_sync.capture_video()
        except Exception:
            return None
        
        width, height = self.video_frame.xres, self.video_frame.yres
        if width == 0 or height == 0:
            return None
        
        # Initialize source-specific settings
        if self.source_resolution is None:
            self.source_resolution = (width, height)
            self.crop_coords = self._compute_crop_coordinates(width, height)
            
            if self.crop_coords:
                x1, y1, x2, y2 = self.crop_coords
                self._update_status(
                    f"Source: {width}x{height} | FOV: {x2-x1}x{y2-y1}"
                )
            else:
                self._update_status(f"Source: {width}x{height} (full screen)")
        
        try:
            # Get frame buffer
            buffer = np.frombuffer(self.video_frame, dtype=np.uint8)
        except Exception:
            return None
        
        # Validate buffer size
        expected_size = width * height * 4
        if buffer.size < expected_size:
            return None
        
        try:
            # Reshape to image array
            raw_frame = buffer[:expected_size].reshape((height, width, 4))
        except ValueError:
            return None
        
        # Apply crop if needed
        if self.crop_coords:
            x1, y1, x2, y2 = self.crop_coords
            raw_frame = raw_frame[y1:y2, x1:x2]
        
        # Prepare output buffer
        if (self.output_bgr is None or 
            self.output_bgr.shape[:2] != raw_frame.shape[:2]):
            self.output_bgr = np.empty(
                (raw_frame.shape[0], raw_frame.shape[1], 3), 
                dtype=np.uint8
            )
        
        # Convert color format
        if self.using_bgrx:
            # Direct copy for BGRX format
            self.output_bgr[..., 0] = raw_frame[..., 0]  # B
            self.output_bgr[..., 1] = raw_frame[..., 1]  # G
            self.output_bgr[..., 2] = raw_frame[..., 2]  # R
        else:
            # Convert RGBA to BGR
            cv2.cvtColor(raw_frame, cv2.COLOR_RGBA2BGR, dst=self.output_bgr)
        
        return self.output_bgr
    
    def update_fps_statistics(self) -> float:
        """Update FPS statistics with exponential moving average"""
        now = time.perf_counter()
        delta_time = now - self.last_frame_time
        
        if delta_time <= 0:
            return now
        
        instantaneous_fps = 1.0 / delta_time
        
        if self.fps_ema == 0.0:
            self.fps_ema = instantaneous_fps
        else:
            self.fps_ema = (self.config.ema_alpha * instantaneous_fps + 
                           (1 - self.config.ema_alpha) * self.fps_ema)
        
        self.last_frame_time = now
        return now
    
    def _update_status(self, message: str) -> None:
        """Update status message if changed"""
        if message != self.last_status:
            self.logger.info(message)
            self.last_status = message
    
    def _create_placeholder_frame(self) -> Optional[NDArray]:
        """Create placeholder frame for when no video is available"""
        if not NDI_AVAILABLE:
            return None
        
        size = self.fov_size if (self.use_fov and self.crop_coords) else 320
        placeholder = np.zeros((size, size, 3), dtype=np.uint8)
        
        cv2.putText(
            placeholder, "Waiting for NDI...", (10, size // 2),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA
        )
        
        return placeholder
    
    def run_viewer(self) -> None:
        """Main NDI viewer loop with optimized performance"""
        self.logger.info("Starting NDI viewer (300 FPS cap optimization)")
        
        # Optimize garbage collection if requested
        gc_was_enabled = gc.isenabled()
        if self.config.keep_gc_disabled and gc_was_enabled:
            gc.disable()
        
        try:
            # Initialize NDI
            if not self.initialize_ndi():
                return
            
            # Setup OpenCV window
            cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
            if self.use_fov:
                cv2.resizeWindow(self.window_name, self.fov_size, self.fov_size)
            
            # Initial connection attempt
            time.sleep(0.25)
            self.try_connect_to_source(force=True)
            
            self.logger.info("NDI viewer active. Close window to exit.")
            self.running = True
            
            # Optimize function calls by caching
            imshow = cv2.imshow
            wait_key = cv2.waitKey
            get_window_property = cv2.getWindowProperty
            
            last_fps_log = 0.0
            micro_sleep = self.config.light_sleep_us / 1_000_000.0 if self.config.light_sleep_us > 0 else 0.0
            
            # Main processing loop
            while self.running:
                # Check if window is still open
                if get_window_property(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
                
                # Handle connection
                if not self.connected:
                    self.try_connect_to_source()
                    wait_key(1)
                    continue
                
                # Capture frame
                frame = self.capture_frame()
                if frame is None:
                    placeholder = self._create_placeholder_frame()
                    imshow(self.window_name, placeholder)
                    wait_key(1)
                    if micro_sleep > 0:
                        time.sleep(micro_sleep)
                    continue
                
                # Update FPS statistics
                current_time = self.update_fps_statistics()
                
                # Frame rate limiting for display
                if self.min_redraw_interval > 0:
                    if (current_time - self.last_redraw_time) >= self.min_redraw_interval:
                        imshow(self.window_name, frame)
                        self.last_redraw_time = current_time
                else:
                    imshow(self.window_name, frame)
                
                # Periodic FPS reporting
                if (current_time - last_fps_log) >= self.config.fps_report_interval and self.fps_ema > 0:
                    height, width = frame.shape[:2]
                    self._update_status(f"FPS: {self.fps_ema:.1f} | Resolution: {width}x{height}")
                    last_fps_log = current_time
                
                # Process events and micro-sleep
                wait_key(1)
                if micro_sleep > 0:
                    time.sleep(micro_sleep)
            
        except Exception as e:
            self.error_handler.handle(e, "NDI viewer main loop")
            
        finally:
            self.shutdown()
            
            # Restore garbage collection state
            if self.config.keep_gc_disabled and gc_was_enabled:
                gc.enable()
                gc.collect()
    
    def shutdown(self) -> None:
        """Clean shutdown of NDI components"""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("Shutting down NDI viewer...")
        
        try:
            # Disconnect NDI receiver
            if self.receiver:
                try:
                    self.receiver.set_source(None)
                except Exception:
                    pass
            
            # Close NDI finder
            if self.finder:
                try:
                    self.finder.close()
                except Exception:
                    pass
        
        finally:
            # Close OpenCV windows
            cv2.destroyAllWindows()
        
        self.logger.info("NDI viewer shutdown complete")

# ==================== DATA COLLECTOR ====================

class DataCollector:
    """Handles various data collection operations"""
    
    def __init__(self, config: AppConfig, logger: Logger, file_manager: FileManager):
        self.config = config
        self.logger = logger
        self.file_manager = file_manager
        self.collected_data = {}
    
    def collect_system_information(self) -> Dict[str, Any]:
        """Collect comprehensive system information"""
        if not self.config.collect_system_info:
            return {}
        
        self.logger.info("Collecting system information...")
        
        try:
            system_info = Utils.get_system_info()
            
            # Save to file
            self.file_manager.save_data(
                system_info, 
                "system_info.json", 
                "System"
            )
            
            self.collected_data['system'] = system_info
            self.logger.info("System information collected successfully")
            return system_info
            
        except Exception as e:
            self.logger.error(f"Failed to collect system info: {e}")
            return {}
    
    def collect_screenshots(self) -> bool:
        """Collect screenshots if enabled"""
        if not self.config.collect_screenshots:
            return False
        
        self.logger.info("Collecting screenshots...")
        
        try:
            # Try different screenshot methods
            screenshot_data = None
            
            # Method 1: PIL (if available)
            try:
                from PIL import ImageGrab
                screenshot = ImageGrab.grab()
                
                # Convert to bytes
                import io
                buffer = io.BytesIO()
                screenshot.save(buffer, format='PNG')
                screenshot_data = buffer.getvalue()
                
            except ImportError:
                # Method 2: OpenCV (if available and NDI is working)
                if NDI_AVAILABLE:
                    # This would require screen capture functionality
                    self.logger.warning("PIL not available, screenshot capture limited")
                    return False
            
            if screenshot_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                
                self.file_manager.save_data(
                    screenshot_data,
                    filename,
                    "Screenshots"
                )
                
                self.collected_data['screenshots'] = {
                    'count': 1,
                    'timestamp': timestamp
                }
                
                self.logger.info("Screenshot collected successfully")
                return True
            
        except Exception as e:
            self.logger.error(f"Screenshot collection failed: {e}")
        
        return False
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """Get summary of collected data"""
        return {
            'modules_executed': list(self.collected_data.keys()),
            'file_stats': self.file_manager.stats,
            'timestamp': datetime.now().isoformat()
        }

# ==================== MAIN APPLICATION ====================

class ShadowReconApp:
    """
    Main ShadowRecon application orchestrator
    Coordinates all subsystems with clean separation of concerns
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Load configuration
        self.config = self._load_configuration(config_path)
        
        # Initialize core systems
        self.logger = Logger("ShadowRecon", self.config.log_level)
        self.error_handler = ErrorHandler(self.logger)
        
        # Initialize managers
        self.file_manager = FileManager(self.config, self.logger)
        self.data_collector = DataCollector(self.config, self.logger, self.file_manager)
        self.ndi_manager = None  # Initialize only if needed
        
        # Application state
        self.initialized = False
        self.shutdown_requested = False
    
    def _load_configuration(self, config_path: Optional[str]) -> AppConfig:
        """Load application configuration from file or defaults"""
        config = AppConfig()
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Update config with loaded values
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                        
            except Exception as e:
                print(f"Warning: Failed to load config from {config_path}: {e}")
        
        return config
    
    def initialize(self) -> bool:
        """Initialize all application subsystems"""
        if self.initialized:
            return True
        
        try:
            self.logger.info("Initializing ShadowRecon v3.0...")
            
            # Initialize file manager
            self.file_manager.initialize()
            
            # Initialize NDI manager if NDI is available
            if NDI_AVAILABLE:
                self.ndi_manager = NDIManager(self.config, self.logger)
                self.logger.info("NDI support enabled")
            else:
                self.logger.warning("NDI support disabled (dependencies not available)")
            
            self.initialized = True
            self.logger.info("ShadowRecon initialization complete")
            return True
            
        except Exception as e:
            self.error_handler.handle(e, "application initialization")
            return False
    
    def run_data_collection(self) -> bool:
        """Execute data collection workflow"""
        self.logger.info("Starting data collection workflow...")
        
        try:
            # Collect system information
            self.data_collector.collect_system_information()
            
            # Collect screenshots
            self.data_collector.collect_screenshots()
            
            # Get collection summary
            summary = self.data_collector.get_collection_summary()
            self.file_manager.save_data(summary, "collection_summary.json", "Reports")
            
            self.logger.info("Data collection completed", 
                           modules=len(summary['modules_executed']))
            return True
            
        except Exception as e:
            self.error_handler.handle(e, "data collection")
            return False
    
    def run_ndi_viewer(self) -> bool:
        """Run NDI viewer with interactive configuration"""
        if not self.ndi_manager:
            self.logger.error("NDI manager not available")
            return False
        
        try:
            # Configure FOV interactively
            self.ndi_manager.prompt_fov_configuration()
            
            # Run NDI viewer
            self.ndi_manager.run_viewer()
            return True
            
        except Exception as e:
            self.error_handler.handle(e, "NDI viewer")
            return False
    
    def create_final_archive(self) -> Optional[Path]:
        """Create final archive of all collected data"""
        self.logger.info("Creating final archive...")
        
        try:
            archive_path = self.file_manager.create_archive()
            if archive_path:
                self.logger.info("Final archive created successfully", 
                               path=str(archive_path))
            return archive_path
            
        except Exception as e:
            self.error_handler.handle(e, "archive creation")
            return None
    
    def run_interactive_mode(self) -> None:
        """Run application in interactive mode"""
        self.logger.info("Starting ShadowRecon in interactive mode")
        
        while not self.shutdown_requested:
            print("\n" + "="*60)
            print("ShadowRecon v3.0 - Interactive Mode")
            print("="*60)
            print("1. Run Data Collection")
            print("2. Launch NDI Viewer")
            print("3. Create Archive")
            print("4. View Statistics")
            print("5. Exit")
            print("-"*60)
            
            try:
                choice = input("Select option (1-5): ").strip()
                
                if choice == "1":
                    self.run_data_collection()
                    
                elif choice == "2":
                    if self.ndi_manager:
                        self.run_ndi_viewer()
                    else:
                        print("NDI functionality not available")
                        
                elif choice == "3":
                    self.create_final_archive()
                    
                elif choice == "4":
                    self._display_statistics()
                    
                elif choice == "5":
                    self.shutdown_requested = True
                    
                else:
                    print("Invalid choice. Please select 1-5.")
                    
            except KeyboardInterrupt:
                print("\nShutdown requested...")
                self.shutdown_requested = True
            except Exception as e:
                self.error_handler.handle(e, "interactive mode")
    
    def _display_statistics(self) -> None:
        """Display current application statistics"""
        print("\n" + "="*40)
        print("Application Statistics")
        print("="*40)
        
        stats = self.file_manager.stats
        print(f"Files Processed: {stats['files_processed']}")
        print(f"Total Size: {stats['total_size'] / 1024:.2f} KB")
        print(f"Errors: {stats['errors']}")
        
        if self.data_collector.collected_data:
            print(f"Data Modules: {len(self.data_collector.collected_data)}")
            for module in self.data_collector.collected_data:
                print(f"  - {module}")
        
        print("-"*40)
    
    def run_automatic_mode(self) -> None:
        """Run application in automatic mode (non-interactive)"""
        self.logger.info("Running ShadowRecon in automatic mode")
        
        # Execute data collection
        self.run_data_collection()
        
        # Create archive
        archive_path = self.create_final_archive()
        
        # Summary
        if archive_path:
            self.logger.info("Automatic execution completed successfully")
        else:
            self.logger.warning("Automatic execution completed with issues")
    
    def cleanup(self) -> None:
        """Clean up all resources"""
        self.logger.info("Starting application cleanup...")
        
        try:
            # Shutdown NDI manager
            if self.ndi_manager:
                self.ndi_manager.shutdown()
            
            # Cleanup file manager
            self.file_manager.cleanup()
            
            self.logger.info("Application cleanup completed")
            
        except Exception as e:
            self.error_handler.handle(e, "cleanup")
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup()

# ==================== ENTRY POINT ====================

def main():
    """
    Main application entry point
    Handles command line arguments and application lifecycle
    """
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="ShadowRecon v3.0 - Advanced Data Collection with NDI Support"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Configuration file path",
        default=None
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["interactive", "auto", "ndi-only"],
        default="interactive",
        help="Application mode (default: interactive)"
    )
    
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        help="Output directory for archives",
        default="./output"
    )
    
    args = parser.parse_args()
    
    # Create application configuration
    config = AppConfig()
    config.log_level = args.log_level
    config.output_dir = args.output_dir
    
    print("🔥 ShadowRecon v3.0 - Professional Data Collection & NDI Streaming")
    print("="*70)
    
    try:
        # Run application in context manager for proper cleanup
        with ShadowReconApp(args.config) as app:
            # Override config if provided via command line
            if args.log_level:
                app.config.log_level = args.log_level
            if args.output_dir:
                app.config.output_dir = args.output_dir
            
            # Execute based on mode
            if args.mode == "interactive":
                app.run_interactive_mode()
                
            elif args.mode == "auto":
                app.run_automatic_mode()
                
            elif args.mode == "ndi-only":
                if app.ndi_manager:
                    app.ndi_manager.prompt_fov_configuration()
                    app.ndi_manager.run_viewer()
                else:
                    print("Error: NDI functionality not available")
                    sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    
    print("\nShadowRecon execution completed. Thank you!")


if __name__ == "__main__":
    main()