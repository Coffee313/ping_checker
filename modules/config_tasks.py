"""
Config Tasks Module for Network Engineer Multitool
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from string import Template

class ConfigTasks:
    """Configuration template management and generation"""
    
    def __init__(self, db_manager):
        """Initialize config tasks with database manager"""
        self.db_manager = db_manager
    
    def create_template(self, name: str, device_type: str, content: str, description: str = None) -> Dict:
        """Create or update a configuration template"""
        try:
            template_id = self.db_manager.save_config_template(name, device_type, content, description)
            
            self.db_manager.log_work_history(
                module="config_tasks",
                action="create_template",
                details=f"Created/updated template '{name}' for {device_type}",
                data={'template_id': template_id, 'name': name, 'device_type': device_type}
            )
            
            return {'success': True, 'template_id': template_id}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_templates(self, device_type: str = None) -> List[Dict]:
        """List available templates"""
        return self.db_manager.get_config_templates(device_type)
    
    def generate_config(self, template_name: str, variables: Dict, device_name: str = None) -> Dict:
        """Generate configuration from template"""
        try:
            # Get template from database
            templates = self.db_manager.get_config_templates()
            template_data = next((t for t in templates if t['name'] == template_name), None)
            
            if not template_data:
                return {'success': False, 'error': f"Template '{template_name}' not found"}
            
            # Replace variables in template
            template = Template(template_data['template_content'])
            try:
                generated_config = template.safe_substitute(variables)
            except KeyError as e:
                return {'success': False, 'error': f"Missing variable: {e}"}
            
            # Save generation result
            gen_id = self.db_manager.save_config_generation(
                template_name, variables, generated_config, device_name
            )
            
            self.db_manager.log_work_history(
                module="config_tasks",
                action="generate_config",
                details=f"Generated config from template '{template_name}'" + 
                       (f" for device '{device_name}'" if device_name else ""),
                data={'generation_id': gen_id, 'template_name': template_name, 'device_name': device_name}
            )
            
            return {
                'success': True, 
                'generated_config': generated_config,
                'generation_id': gen_id
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def extract_variables_from_template(self, content: str) -> List[str]:
        """Extract variable placeholders from template content"""
        # Find all $variable patterns
        variables = re.findall(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', content)
        return list(set(variables))  # Remove duplicates
    
    def save_config_to_file(self, config: str, filename: str, config_dir: Path) -> Dict:
        """Save generated configuration to file"""
        try:
            config_file = config_dir / filename
            config_file.write_text(config, encoding='utf-8')
            
            return {'success': True, 'file_path': str(config_file)}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_sample_templates(self) -> Dict[str, str]:
        """Get sample templates for different device types"""
        return {
            'cisco_switch_vlan': '''! VLAN Configuration for $device_name
vlan $vlan_id
 name $vlan_name
!
interface vlan$vlan_id
 ip address $ip_address $subnet_mask
 description $description
 no shutdown
!
''',
            'cisco_router_interface': '''! Interface Configuration for $device_name
interface $interface_name
 description $description
 ip address $ip_address $subnet_mask
 no shutdown
!
''',
            'ubiquiti_wireless': '''# Wireless Network Configuration for $device_name
# SSID: $ssid_name
# Security: $security_type
# VLAN: $vlan_id
# Channel: $channel
''',
        }
    
    def display_menu(self):
        """Display config tasks menu"""
        print("\n" + "="*40)
        print("    Config Tasks")
        print("="*40)
        print("1. Create/Edit Template")
        print("2. List Templates")
        print("3. Generate Configuration")
        print("4. Load Sample Templates")
        print("5. View Generated Configs")
        print("0. Back to main menu")
        print("="*40)
    
    def run(self):
        """Run the config tasks interface"""
        while True:
            self.display_menu()
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '1':
                self._create_template_interactive()
            elif choice == '2':
                self._list_templates_interactive()
            elif choice == '3':
                self._generate_config_interactive()
            elif choice == '4':
                self._load_sample_templates()
            elif choice == '5':
                self._view_generated_configs()
            elif choice == '0':
                break
            else:
                print("Invalid choice. Please try again.")
    
    def _create_template_interactive(self):
        """Interactive template creation"""
        print("\n" + "-"*30)
        print("  Create/Edit Template")
        print("-"*30)
        
        name = input("Template name: ").strip()
        if not name:
            print("Template name cannot be empty")
            return
        
        device_type = input("Device type (e.g., cisco_switch, ubiquiti_ap): ").strip()
        if not device_type:
            print("Device type cannot be empty")
            return
        
        description = input("Description (optional): ").strip()
        
        print("\nEnter template content (use $variable_name for variables).")
        print("Press Ctrl+Z (Windows) or Ctrl+D (Unix) on a new line when finished:")
        
        content_lines = []
        try:
            while True:
                line = input()
                content_lines.append(line)
        except EOFError:
            pass
        
        content = '\n'.join(content_lines)
        
        if not content.strip():
            print("Template content cannot be empty")
            return
        
        # Show detected variables
        variables = self.extract_variables_from_template(content)
        if variables:
            print(f"\nDetected variables: {', '.join(variables)}")
        
        result = self.create_template(name, device_type, content, description)
        
        if result['success']:
            print(f"Template '{name}' saved successfully!")
        else:
            print(f"Error saving template: {result['error']}")
    
    def _list_templates_interactive(self):
        """Interactive template listing"""
        device_type = input("Filter by device type (or press Enter for all): ").strip()
        device_type = device_type if device_type else None
        
        templates = self.list_templates(device_type)
        
        if not templates:
            print("No templates found")
            return
        
        print("\n" + "="*80)
        print("    Available Templates")
        print("="*80)
        print(f"{'Name':<20} {'Device Type':<15} {'Created':<20} {'Description'}")
        print("-" * 80)
        
        for template in templates:
            created = template['created_at'][:16]  # Truncate timestamp
            desc = (template['description'] or "")[:30]  # Truncate description
            print(f"{template['name']:<20} {template['device_type']:<15} {created:<20} {desc}")
    
    def _generate_config_interactive(self):
        """Interactive config generation"""
        # List available templates
        templates = self.list_templates()
        if not templates:
            print("No templates available. Create a template first.")
            return
        
        print("\nAvailable templates:")
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template['name']} ({template['device_type']})")
        
        try:
            choice = int(input("\nSelect template number: ")) - 1
            if choice < 0 or choice >= len(templates):
                print("Invalid selection")
                return
        except ValueError:
            print("Invalid input")
            return
        
        selected_template = templates[choice]
        template_name = selected_template['name']
        
        # Extract variables from template
        variables = self.extract_variables_from_template(selected_template['template_content'])
        
        if not variables:
            print("This template has no variables")
            return
        
        print(f"\nTemplate '{template_name}' requires the following variables:")
        
        # Collect variable values
        variable_values = {}
        for var in variables:
            value = input(f"{var}: ").strip()
            if value:
                variable_values[var] = value
        
        device_name = input("Device name (optional): ").strip()
        device_name = device_name if device_name else None
        
        # Generate configuration
        result = self.generate_config(template_name, variable_values, device_name)
        
        if result['success']:
            print("\n" + "="*50)
            print("    Generated Configuration")
            print("="*50)
            print(result['generated_config'])
            print("="*50)
            
            # Ask if user wants to save to file
            save_to_file = input("\nSave to file? (y/n): ").strip().lower()
            if save_to_file == 'y':
                filename = input("Enter filename: ").strip()
                if filename:
                    from core.config import Config
                    config = Config()
                    save_result = self.save_config_to_file(
                        result['generated_config'], 
                        filename, 
                        config.config_dir
                    )
                    if save_result['success']:
                        print(f"Configuration saved to: {save_result['file_path']}")
                    else:
                        print(f"Error saving file: {save_result['error']}")
        else:
            print(f"Error generating configuration: {result['error']}")
    
    def _load_sample_templates(self):
        """Load sample templates into database"""
        samples = self.get_sample_templates()
        
        print("\nAvailable sample templates:")
        for name, content in samples.items():
            device_type = name.split('_')[0]  # Extract device type from name
            print(f"- {name} ({device_type})")
        
        load_all = input("\nLoad all samples? (y/n): ").strip().lower()
        
        if load_all == 'y':
            loaded_count = 0
            for name, content in samples.items():
                device_type = name.split('_')[0]
                result = self.create_template(
                    name, 
                    device_type, 
                    content, 
                    f"Sample template for {device_type}"
                )
                if result['success']:
                    loaded_count += 1
            
            print(f"Loaded {loaded_count} sample templates")
        else:
            sample_name = input("Enter sample template name to load: ").strip()
            if sample_name in samples:
                device_type = sample_name.split('_')[0]
                result = self.create_template(
                    sample_name, 
                    device_type, 
                    samples[sample_name], 
                    f"Sample template for {device_type}"
                )
                if result['success']:
                    print(f"Sample template '{sample_name}' loaded successfully")
                else:
                    print(f"Error loading template: {result['error']}")
            else:
                print("Sample template not found")
    
    def _view_generated_configs(self):
        """View recently generated configurations"""
        # This would require adding a method to database manager to get config generations
        print("Generated configurations history:")
        print("(This feature would show recently generated configs from the database)")
        print("Press Enter to continue...")
        input()
