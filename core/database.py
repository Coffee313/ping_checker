"""
Database management for Network Engineer Multitool
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """Database manager for storing work history and data"""
    
    def __init__(self, db_path: Path):
        """Initialize database connection"""
        self.db_path = Path(db_path)
        self.connection = None
        self._connect()
        self._initialize_tables()
    
    def _connect(self):
        """Connect to the database"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
        except Exception as e:
            raise Exception(f"Failed to connect to database: {e}")
    
    def _initialize_tables(self):
        """Initialize database tables"""
        cursor = self.connection.cursor()
        
        # Work history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                module TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                data TEXT
            )
        ''')
        
        # Ping results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ping_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                target TEXT NOT NULL,
                packets_sent INTEGER,
                packets_received INTEGER,
                packet_loss REAL,
                min_time REAL,
                max_time REAL,
                avg_time REAL,
                raw_output TEXT
            )
        ''')
        
        # IP calculations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                calculation_type TEXT NOT NULL,
                input_data TEXT NOT NULL,
                result TEXT NOT NULL
            )
        ''')
        
        # Config templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                device_type TEXT NOT NULL,
                template_content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        # Config generations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config_generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                template_name TEXT NOT NULL,
                variables TEXT NOT NULL,
                generated_config TEXT NOT NULL,
                device_name TEXT
            )
        ''')
        
        self.connection.commit()
    
    def log_work_history(self, module: str, action: str, details: str = None, data: Dict = None):
        """Log work activity to history"""
        cursor = self.connection.cursor()
        timestamp = datetime.now().isoformat()
        data_json = json.dumps(data) if data else None
        
        cursor.execute('''
            INSERT INTO work_history (timestamp, module, action, details, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, module, action, details, data_json))
        
        self.connection.commit()
    
    def get_work_history(self, limit: int = 50) -> List[Dict]:
        """Get work history records"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM work_history
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def save_ping_result(self, target: str, packets_sent: int, packets_received: int,
                        packet_loss: float, min_time: float = None, max_time: float = None,
                        avg_time: float = None, raw_output: str = None) -> int:
        """Save ping test results"""
        cursor = self.connection.cursor()
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO ping_results 
            (timestamp, target, packets_sent, packets_received, packet_loss, 
             min_time, max_time, avg_time, raw_output)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, target, packets_sent, packets_received, packet_loss,
              min_time, max_time, avg_time, raw_output))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_ping_results(self, target: str = None, limit: int = 50) -> List[Dict]:
        """Get ping test results"""
        cursor = self.connection.cursor()
        
        if target:
            cursor.execute('''
                SELECT * FROM ping_results
                WHERE target = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (target, limit))
        else:
            cursor.execute('''
                SELECT * FROM ping_results
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def save_ip_calculation(self, calculation_type: str, input_data: str, result: str) -> int:
        """Save IP calculation result"""
        cursor = self.connection.cursor()
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO ip_calculations (timestamp, calculation_type, input_data, result)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, calculation_type, input_data, result))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def save_config_template(self, name: str, device_type: str, content: str, 
                           description: str = None) -> int:
        """Save or update config template"""
        cursor = self.connection.cursor()
        timestamp = datetime.now().isoformat()
        
        # Check if template exists
        cursor.execute('SELECT id FROM config_templates WHERE name = ?', (name,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE config_templates 
                SET device_type = ?, template_content = ?, updated_at = ?, description = ?
                WHERE name = ?
            ''', (device_type, content, timestamp, description, name))
            return existing[0]
        else:
            cursor.execute('''
                INSERT INTO config_templates 
                (name, device_type, template_content, created_at, updated_at, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, device_type, content, timestamp, timestamp, description))
            
            self.connection.commit()
            return cursor.lastrowid
    
    def get_config_templates(self, device_type: str = None) -> List[Dict]:
        """Get config templates"""
        cursor = self.connection.cursor()
        
        if device_type:
            cursor.execute('''
                SELECT * FROM config_templates
                WHERE device_type = ?
                ORDER BY name
            ''', (device_type,))
        else:
            cursor.execute('''
                SELECT * FROM config_templates
                ORDER BY device_type, name
            ''')
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def save_config_generation(self, template_name: str, variables: Dict, 
                             generated_config: str, device_name: str = None) -> int:
        """Save config generation result"""
        cursor = self.connection.cursor()
        timestamp = datetime.now().isoformat()
        variables_json = json.dumps(variables)
        
        cursor.execute('''
            INSERT INTO config_generations 
            (timestamp, template_name, variables, generated_config, device_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, template_name, variables_json, generated_config, device_name))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
