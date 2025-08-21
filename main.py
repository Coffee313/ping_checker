#!/usr/bin/env python3
"""
Network Engineer Multitool
A comprehensive tool for network engineering tasks
"""

import sys
import os
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.app import NetworkMultitool

def main():
    """Main entry point for the application"""
    try:
        app = NetworkMultitool()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
