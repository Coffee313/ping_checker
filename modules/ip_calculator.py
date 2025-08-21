"""
IP Calculator Module for Network Engineer Multitool
"""

import ipaddress
from typing import Dict, List

class IPCalculator:
    """IP address calculation tools"""
    
    def __init__(self, db_manager):
        """Initialize IP calculator with database manager"""
        self.db_manager = db_manager
    
    def calculate_subnet(self, network_cidr: str) -> Dict:
        """Calculate subnet details"""
        try:
            network = ipaddress.ip_network(network_cidr, strict=False)
            result = {
                'network_address': str(network.network_address),
                'netmask': str(network.netmask),
                'broadcast_address': str(network.broadcast_address),
                'total_hosts': network.num_addresses,
                'usable_hosts': network.num_addresses - 2 if network.prefixlen < 31 else network.num_addresses,
                'cidr': network.prefixlen,
                'host_range_start': str(network.network_address + 1) if network.prefixlen < 31 else str(network.network_address),
                'host_range_end': str(network.broadcast_address - 1) if network.prefixlen < 31 else str(network.broadcast_address)
            }
            
            self.db_manager.save_ip_calculation(
                calculation_type="subnet_calculation",
                input_data=network_cidr,
                result=str(result)
            )
            self.db_manager.log_work_history(
                module="ip_calculator",
                action="calculate_subnet",
                details=f"Calculated subnet for {network_cidr}",
                data=result
            )
            
            return {'success': True, 'data': result}
        
        except ValueError as e:
            return {'success': False, 'error': str(e)}
    
    def get_supernets(self, cidr_list: List[str]) -> Dict:
        """Calculate supernets for a list of CIDRs"""
        try:
            networks = [ipaddress.ip_network(c) for c in cidr_list]
            supernets = ipaddress.summarize_address_range(
                min(n.network_address for n in networks),
                max(n.broadcast_address for n in networks)
            )
            result = [str(s) for s in supernets]
            
            self.db_manager.save_ip_calculation(
                calculation_type="supernet_calculation",
                input_data=",".join(cidr_list),
                result=str(result)
            )
            
            return {'success': True, 'data': result}
        
        except ValueError as e:
            return {'success': False, 'error': str(e)}
    
    def display_menu(self):
        """Display IP calculator menu"""
        print("\n" + "="*40)
        print("    IP Calculator")
        print("="*40)
        print("1. Calculate Subnet Details")
        print("2. Calculate Supernets")
        print("0. Back to main menu")
        print("="*40)
    
    def run(self):
        """Run the IP calculator interface"""
        while True:
            self.display_menu()
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '1':
                self._calculate_subnet_details()
            elif choice == '2':
                self._calculate_supernets()
            elif choice == '0':
                break
            else:
                print("Invalid choice. Please try again.")
    
    def _calculate_subnet_details(self):
        """Interactive subnet calculation"""
        network_input = input("Enter network address (e.g., 192.168.1.0/24): ").strip()
        if not network_input:
            print("Input cannot be empty")
            return
        
        result = self.calculate_subnet(network_input)
        
        if result['success']:
            print("\n" + "-"*30)
            print("  Subnet Calculation Result")
            print("-"*30)
            for key, value in result['data'].items():
                print(f"{key.replace('_', ' ').title():<20}: {value}")
        else:
            print(f"Error: {result['error']}")
    
    def _calculate_supernets(self):
        """Interactive supernet calculation"""
        cidr_input = input("Enter comma-separated CIDRs: ").strip()
        if not cidr_input:
            print("Input cannot be empty")
            return
        
        cidr_list = [c.strip() for c in cidr_input.split(',')]
        result = self.get_supernets(cidr_list)
        
        if result['success']:
            print("\n" + "-"*30)
            print("  Supernet Calculation Result")
            print("-"*30)
            print("Supernets:")
            for supernet in result['data']:
                print(f"- {supernet}")
        else:
            print(f"Error: {result['error']}")
