"""
Ping Tool Module for Network Engineer Multitool
"""

import subprocess
import re
import platform
from typing import Dict, List, Optional

class PingTool:
    """Ping tool for network connectivity testing"""
    
    def __init__(self, db_manager):
        """Initialize ping tool with database manager"""
        self.db_manager = db_manager
        self.is_windows = platform.system().lower() == 'windows'
    
    def ping_host(self, target: str, count: int = 4, timeout: int = 5) -> Dict:
        """Ping a host and return results"""
        try:
            # Build ping command based on OS
            if self.is_windows:
                cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), target]
            else:
                cmd = ['ping', '-c', str(count), '-W', str(timeout), target]
            
            # Execute ping command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Parse results
            ping_result = self._parse_ping_output(result.stdout, result.stderr, target, count)
            
            # Save to database
            self.db_manager.save_ping_result(
                target=ping_result['target'],
                packets_sent=ping_result['packets_sent'],
                packets_received=ping_result['packets_received'],
                packet_loss=ping_result['packet_loss'],
                min_time=ping_result.get('min_time'),
                max_time=ping_result.get('max_time'),
                avg_time=ping_result.get('avg_time'),
                raw_output=result.stdout
            )
            
            # Log to work history
            self.db_manager.log_work_history(
                module="ping_tool",
                action="ping_host",
                details=f"Pinged {target} - {ping_result['packet_loss']:.1f}% loss",
                data=ping_result
            )
            
            return ping_result
            
        except subprocess.TimeoutExpired:
            return {
                'target': target,
                'success': False,
                'error': 'Ping command timed out',
                'packets_sent': count,
                'packets_received': 0,
                'packet_loss': 100.0
            }
        except Exception as e:
            return {
                'target': target,
                'success': False,
                'error': str(e),
                'packets_sent': count,
                'packets_received': 0,
                'packet_loss': 100.0
            }
    
    def _parse_ping_output(self, stdout: str, stderr: str, target: str, count: int) -> Dict:
        """Parse ping command output"""
        result = {
            'target': target,
            'success': False,
            'packets_sent': count,
            'packets_received': 0,
            'packet_loss': 100.0,
            'times': []
        }
        
        if stderr and 'could not find host' in stderr.lower():
            result['error'] = 'Host not found'
            return result
        
        if not stdout:
            result['error'] = 'No output received'
            return result
        
        if self.is_windows:
            return self._parse_windows_ping(stdout, result)
        else:
            return self._parse_unix_ping(stdout, result)
    
    def _parse_windows_ping(self, output: str, result: Dict) -> Dict:
        """Parse Windows ping output"""
        lines = output.split('\n')
        
        # Count successful pings and extract times
        times = []
        for line in lines:
            if 'time=' in line and 'TTL=' in line:
                result['packets_received'] += 1
                # Extract time
                time_match = re.search(r'time[<=](\d+)ms', line)
                if time_match:
                    times.append(float(time_match.group(1)))
        
        # Look for statistics
        for line in lines:
            if 'Lost =' in line:
                loss_match = re.search(r'Lost = (\d+)', line)
                if loss_match:
                    lost = int(loss_match.group(1))
                    result['packet_loss'] = (lost / result['packets_sent']) * 100
        
        if times:
            result['min_time'] = min(times)
            result['max_time'] = max(times)
            result['avg_time'] = sum(times) / len(times)
            result['times'] = times
            result['success'] = True
        
        return result
    
    def _parse_unix_ping(self, output: str, result: Dict) -> Dict:
        """Parse Unix/Linux ping output"""
        lines = output.split('\n')
        
        # Find statistics line
        for line in lines:
            if 'packets transmitted' in line:
                match = re.search(r'(\d+) packets transmitted, (\d+) (?:packets )?received.*?(\d+(?:\.\d+)?)% packet loss', line)
                if match:
                    result['packets_sent'] = int(match.group(1))
                    result['packets_received'] = int(match.group(2))
                    result['packet_loss'] = float(match.group(3))
        
        # Find timing statistics
        for line in lines:
            if 'min/avg/max' in line:
                match = re.search(r'= ([\d.]+)/([\d.]+)/([\d.]+)', line)
                if match:
                    result['min_time'] = float(match.group(1))
                    result['avg_time'] = float(match.group(2))
                    result['max_time'] = float(match.group(3))
                    result['success'] = True
        
        return result
    
    def ping_multiple_hosts(self, targets: List[str], count: int = 4) -> Dict:
        """Ping multiple hosts"""
        results = {}
        for target in targets:
            print(f"Pinging {target}...")
            results[target] = self.ping_host(target, count)
        return results
    
    def continuous_ping(self, target: str, interval: int = 1, duration: int = 60):
        """Perform continuous ping with real-time display"""
        print(f"Starting continuous ping to {target} for {duration} seconds...")
        print("Press Ctrl+C to stop early")
        
        import time
        start_time = time.time()
        ping_count = 0
        success_count = 0
        
        try:
            while time.time() - start_time < duration:
                result = self.ping_host(target, count=1)
                ping_count += 1
                
                if result['success'] and result['packets_received'] > 0:
                    success_count += 1
                    avg_time = result.get('avg_time', 0)
                    print(f"Reply from {target}: time={avg_time:.1f}ms")
                else:
                    print(f"Request timeout for {target}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nPing stopped by user")
        
        # Summary
        loss_rate = ((ping_count - success_count) / ping_count) * 100 if ping_count > 0 else 100
        print(f"\nPing statistics for {target}:")
        print(f"  Packets: Sent = {ping_count}, Received = {success_count}, Lost = {ping_count - success_count} ({loss_rate:.1f}% loss)")
    
    def get_ping_history(self, target: str = None) -> List[Dict]:
        """Get ping history from database"""
        return self.db_manager.get_ping_results(target)
    
    def display_menu(self):
        """Display ping tool menu"""
        print("\n" + "="*40)
        print("    Ping Tool")
        print("="*40)
        print("1. Ping single host")
        print("2. Ping multiple hosts")
        print("3. Continuous ping")
        print("4. View ping history")
        print("0. Back to main menu")
        print("="*40)
    
    def run(self):
        """Run the ping tool interface"""
        while True:
            self.display_menu()
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '1':
                self._ping_single_host()
            elif choice == '2':
                self._ping_multiple_hosts()
            elif choice == '3':
                self._continuous_ping()
            elif choice == '4':
                self._view_ping_history()
            elif choice == '0':
                break
            else:
                print("Invalid choice. Please try again.")
    
    def _ping_single_host(self):
        """Interactive single host ping"""
        target = input("Enter target (IP or hostname): ").strip()
        if not target:
            print("Target cannot be empty")
            return
        
        try:
            count = int(input("Enter number of pings (default 4): ").strip() or "4")
            timeout = int(input("Enter timeout in seconds (default 5): ").strip() or "5")
        except ValueError:
            print("Invalid input, using defaults")
            count, timeout = 4, 5
        
        print(f"\nPinging {target}...")
        result = self.ping_host(target, count, timeout)
        
        self._display_ping_result(result)
    
    def _ping_multiple_hosts(self):
        """Interactive multiple hosts ping"""
        targets_input = input("Enter targets separated by commas: ").strip()
        if not targets_input:
            print("No targets specified")
            return
        
        targets = [t.strip() for t in targets_input.split(',')]
        try:
            count = int(input("Enter number of pings per target (default 4): ").strip() or "4")
        except ValueError:
            count = 4
        
        results = self.ping_multiple_hosts(targets, count)
        
        print("\n" + "="*50)
        print("    Multiple Ping Results")
        print("="*50)
        for target, result in results.items():
            print(f"\n{target}:")
            self._display_ping_result(result, verbose=False)
    
    def _continuous_ping(self):
        """Interactive continuous ping"""
        target = input("Enter target (IP or hostname): ").strip()
        if not target:
            print("Target cannot be empty")
            return
        
        try:
            duration = int(input("Enter duration in seconds (default 60): ").strip() or "60")
            interval = int(input("Enter interval in seconds (default 1): ").strip() or "1")
        except ValueError:
            duration, interval = 60, 1
        
        self.continuous_ping(target, interval, duration)
    
    def _view_ping_history(self):
        """View ping history interface"""
        target = input("Enter target to filter (or press Enter for all): ").strip()
        target = target if target else None
        
        history = self.get_ping_history(target)
        
        if not history:
            print("No ping history found")
            return
        
        print("\n" + "="*80)
        print("    Ping History")
        print("="*80)
        print(f"{'Timestamp':<20} {'Target':<20} {'Sent':<6} {'Recv':<6} {'Loss%':<8} {'Avg(ms)':<10}")
        print("-" * 80)
        
        for record in history[-20:]:  # Show last 20 records
            timestamp = record['timestamp'][:16]  # Truncate timestamp
            target = record['target'][:18]  # Truncate long targets
            avg_time = f"{record['avg_time']:.1f}" if record['avg_time'] else "N/A"
            
            print(f"{timestamp:<20} {target:<20} {record['packets_sent']:<6} "
                  f"{record['packets_received']:<6} {record['packet_loss']:<8.1f} {avg_time:<10}")
    
    def _display_ping_result(self, result: Dict, verbose: bool = True):
        """Display formatted ping result"""
        if result.get('error'):
            print(f"Error: {result['error']}")
            return
        
        if result['success']:
            print(f"SUCCESS - {result['packets_received']}/{result['packets_sent']} packets received")
            print(f"Packet loss: {result['packet_loss']:.1f}%")
            
            if result.get('min_time') is not None:
                print(f"Round-trip times: min={result['min_time']:.1f}ms, "
                      f"avg={result['avg_time']:.1f}ms, max={result['max_time']:.1f}ms")
        else:
            print(f"FAILED - {result['packets_received']}/{result['packets_sent']} packets received")
            print(f"Packet loss: {result['packet_loss']:.1f}%")
