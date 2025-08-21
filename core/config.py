"""
Configuration management for Network Engineer Multitool
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration manager for the application"""
    
    def __init__(self):
        """Initialize configuration"""
        self.app_dir = Path(__file__).parent.parent
        self.portable_mode = self._detect_portable_mode()
        self.config_dir = self._get_config_directory()
        self.database_path = self.config_dir / "network_tool.db"
        self.settings_file = self.config_dir / "settings.json"
        self._ensure_directories()
        self.settings = self._load_settings()
    
    def _detect_portable_mode(self) -> bool:
        """Detect if running in portable mode"""
        # Check if portable.txt exists in app directory
        portable_marker = self.app_dir / "portable.txt"
        return portable_marker.exists()
    
    def _get_config_directory(self) -> Path:
        """Get the configuration directory based on mode"""
        if self.portable_mode:
            # Use 'data' subdirectory in app folder for portable mode
            return self.app_dir / "data"
        else:
            # Use user's AppData directory for installed mode
            if os.name == 'nt':  # Windows
                config_base = Path(os.environ.get('APPDATA', '~'))
            else:  # Unix-like
                config_base = Path.home() / '.config'
            return config_base / "NetworkMultitool"
    
    def _ensure_directories(self):
        """Ensure configuration directories exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create templates directory
        templates_dir = self.config_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # Create portable marker if needed
        if self.portable_mode:
            portable_marker = self.app_dir / "portable.txt"
            if not portable_marker.exists():
                portable_marker.write_text("This file marks the application as portable mode")
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        default_settings = {
            "ping_timeout": 5,
            "ping_count": 4,
            "config_backup": True,
            "auto_save": True,
            "theme": "default"
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                # Merge with defaults
                default_settings.update(settings)
            except Exception as e:
                print(f"Warning: Could not load settings: {e}")
        
        return default_settings
    
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save settings: {e}")
    
    def get_setting(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value
        self.save_settings()
    
    def get_templates_dir(self) -> Path:
        """Get the templates directory"""
        return self.config_dir / "templates"
