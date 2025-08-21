"""
Core application class for Network Engineer Multitool
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

from .database import DatabaseManager
from .config import Config
from modules.ping_tool import PingTool
from modules.ip_calculator import IPCalculator
from modules.config_tasks import ConfigTasks

class NetworkMultitool:
    """Main application class"""
    
    def __init__(self):
        """Initialize the application"""
        self.config = Config()
        self.db_manager = DatabaseManager(self.config.database_path)
        self.modules = self._initialize_modules()
        
    def _initialize_modules(self) -> Dict[str, Any]:
        """Initialize all available modules"""
        modules = {
            'ping': PingTool(self.db_manager),
            'ip_calc': IPCalculator(self.db_manager),
            'config': ConfigTasks(self.db_manager),
        }
        return modules
    
    def display_menu(self):
        """Display the main menu"""
        print("\n" + "="*50)
        print("    Network Engineer Multitool")
        print("="*50)
        print("1. Ping Tool")
        print("2. IP Calculator")
        print("3. Config Tasks")
        print("4. View Work History")
        print("5. Settings")
        print("0. Exit")
        print("="*50)
    
    def handle_menu_choice(self, choice: str):
        """Handle user menu selection"""
        if choice == '1':
            self.modules['ping'].run()
        elif choice == '2':
            self.modules['ip_calc'].run()
        elif choice == '3':
            self.modules['config'].run()
        elif choice == '4':
            self.view_history()
        elif choice == '5':
            self.show_settings()
        elif choice == '0':
            self.exit_app()
        else:
            print("Invalid choice. Please try again.")
    
    def view_history(self):
        """Display work history from database"""
        print("\n" + "="*40)
        print("    Work History")
        print("="*40)
        
        history = self.db_manager.get_work_history()
        if not history:
            print("No work history found.")
            return
        
        for record in history[-10:]:  # Show last 10 records
            print(f"{record['timestamp']} - {record['module']} - {record['action']}")
            if record['details']:
                print(f"  Details: {record['details']}")
            print("-" * 40)
    
    def show_settings(self):
        """Display and manage application settings"""
        print("\n" + "="*40)
        print("    Settings")
        print("="*40)
        print(f"Database Path: {self.config.database_path}")
        print(f"Config Directory: {self.config.config_dir}")
        print(f"Portable Mode: {self.config.portable_mode}")
        print("\nPress Enter to continue...")
        input()
    
    def exit_app(self):
        """Clean exit from application"""
        print("\nThank you for using Network Engineer Multitool!")
        self.db_manager.close()
        sys.exit(0)
    
    def run(self):
        """Main application loop"""
        print("Welcome to Network Engineer Multitool!")
        print(f"Data will be saved to: {self.config.database_path}")
        
        while True:
            try:
                self.display_menu()
                choice = input("\nEnter your choice: ").strip()
                self.handle_menu_choice(choice)
            except KeyboardInterrupt:
                print("\nUse '0' to exit properly.")
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Please try again.")
