import subprocess
import time

def test_ping_function():
    """Test the ping functionality"""
    print("Testing ping functionality...")
    
    test_ips = ["8.8.8.8", "1.1.1.1", "192.168.1.999"]  # Last one should fail
    
    for ip in test_ips:
        print(f"\nTesting {ip}...")
        try:
            cmd = f"ping -n 2 -w 3000 {ip}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"✓ {ip} is reachable")
                # Parse response time
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'time=' in line.lower():
                        try:
                            time_part = line.split('time=')[1].split('ms')[0]
                            print(f"  Response time: {time_part}ms")
                            break
                        except:
                            pass
            else:
                print(f"✗ {ip} is not reachable")
                
        except subprocess.TimeoutExpired:
            print(f"✗ {ip} timed out")
        except Exception as e:
            print(f"✗ Error pinging {ip}: {e}")

if __name__ == "__main__":
    test_ping_function()
    print("\nTest completed!")
    input("Press Enter to continue...")
