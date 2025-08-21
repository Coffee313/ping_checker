import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import subprocess
import threading
import time
from datetime import datetime
import os
import sys
from concurrent.futures import ThreadPoolExecutor
import queue

class PingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IP Ping Checker")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variables
        self.excel_file = None
        self.ip_addresses = []
        self.descriptions = []  # Store descriptions for each IP
        self.ping_results = []
        self.is_pinging = False
        self.infinite_ping = False
        self.sort_reverse = {}  # Track sort direction for each column
        self.max_workers = 50  # Maximum number of parallel ping threads
        self.ping_queue = queue.Queue()  # Queue for ping results
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # File selection
        ttk.Label(main_frame, text="Excel File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.file_var, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # Ping options
        options_frame = ttk.LabelFrame(main_frame, text="Ping Options", padding="5")
        options_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(1, weight=1)
        
        ttk.Label(options_frame, text="Timeout (ms):").grid(row=0, column=0, sticky=tk.W)
        self.timeout_var = tk.StringVar(value="100")
        ttk.Entry(options_frame, textvariable=self.timeout_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(options_frame, text="Count:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.count_var = tk.StringVar(value="4")
        self.count_entry = ttk.Entry(options_frame, textvariable=self.count_var, width=10)
        self.count_entry.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Infinite ping option
        self.infinite_var = tk.BooleanVar(value=True)  # Default to checked
        self.infinite_check = ttk.Checkbutton(options_frame, text="Infinite Ping", variable=self.infinite_var, command=self.toggle_infinite)
        self.infinite_check.grid(row=0, column=4, sticky=tk.W, padx=(20, 0))
        
        # Interval for infinite ping
        ttk.Label(options_frame, text="Interval (s):").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.interval_var = tk.StringVar(value="1")
        ttk.Entry(options_frame, textvariable=self.interval_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=(5, 0))
        
        # Max parallel threads option
        ttk.Label(options_frame, text="Parallel Threads:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=(5, 0))
        self.threads_var = tk.StringVar(value="50")
        ttk.Entry(options_frame, textvariable=self.threads_var, width=10).grid(row=1, column=3, sticky=tk.W, padx=(5, 0), pady=(5, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Ping", command=self.start_ping)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_ping, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Export Results", command=self.export_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Results", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        
        # Results treeview
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="5")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Treeview with scrollbars
        tree_frame = ttk.Frame(results_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_frame, columns=("IP", "Description", "Status", "Response Time", "Last Checked"), show="headings")
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure columns with sorting capability
        self.tree.heading("IP", text="IP Address", command=lambda: self.sort_tree("IP", False))
        self.tree.heading("Description", text="Description", command=lambda: self.sort_tree("Description", False))
        self.tree.heading("Status", text="Status", command=lambda: self.sort_tree("Status", False))
        self.tree.heading("Response Time", text="Response Time (ms)", command=lambda: self.sort_tree("Response Time", True))
        self.tree.heading("Last Checked", text="Last Checked", command=lambda: self.sort_tree("Last Checked", True))
        
        self.tree.column("IP", width=150)
        self.tree.column("Description", width=200)
        self.tree.column("Status", width=100)
        self.tree.column("Response Time", width=150)
        self.tree.column("Last Checked", width=200)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def sort_tree(self, col, numeric):
        """Sort tree contents by column"""
        # Get current sort direction for this column
        reverse = self.sort_reverse.get(col, False)
        
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]

        if numeric:
            # Handle numeric sorting with special cases
            def convert_to_float(text):
                if text in ["-", "Timeout", "Not tested", ""] or text.startswith("Error:"):
                    return -1 if reverse else float('inf')  # Put these at the end/beginning
                elif text == "< 1":
                    return 0.5
                else:
                    try:
                        return float(text)
                    except ValueError:
                        return -1 if reverse else float('inf')
            
            items = [(convert_to_float(text), k) for text, k in items]
        
        # Sort items
        items.sort(reverse=reverse)

        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(items):
            self.tree.move(k, '', index)

        # Toggle sort direction for next time
        self.sort_reverse[col] = not reverse
        
        # Update column heading to show sort direction
        direction = " ↓" if reverse else " ↑"
        if col == "IP":
            self.tree.heading(col, text=f"IP Address{direction}")
        elif col == "Status":
            self.tree.heading(col, text=f"Status{direction}")
        elif col == "Description":
            self.tree.heading(col, text=f"Description{direction}")
        elif col == "Response Time":
            self.tree.heading(col, text=f"Response Time (ms){direction}")
        elif col == "Last Checked":
            self.tree.heading(col, text=f"Last Checked{direction}")

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.file_var.set(filename)
            self.load_excel_file(filename)
            
    def load_excel_file(self, filename):
        try:
            # Read Excel file
            df = pd.read_excel(filename)
            
            # Try to find IP column (common names)
            ip_column = None
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['ip', 'address', 'host']):
                    ip_column = col
                    break
            
            if ip_column is None:
                # If no IP column found, use first column
                ip_column = df.columns[0]
            
            # Try to find description column
            description_column = None
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['description', 'desc', 'name', 'device', 'hostname']):
                    description_column = col
                    break
                
            # Extract IP addresses and descriptions
            self.ip_addresses = df[ip_column].dropna().tolist()
            
            if description_column is not None:
                self.descriptions = df[description_column].fillna("-").tolist()
                # Ensure descriptions list matches IP addresses length
                while len(self.descriptions) < len(self.ip_addresses):
                    self.descriptions.append("-")
            else:
                # If no description column, fill with dashes
                self.descriptions = ["-"] * len(self.ip_addresses)
            
            # Clear previous results
            self.clear_results()
            
            # Add IPs to treeview with descriptions
            for i, ip in enumerate(self.ip_addresses):
                description = self.descriptions[i] if i < len(self.descriptions) else "-"
                self.tree.insert("", tk.END, values=(str(ip), str(description), "Not tested", "-", "-"))
                
            self.status_var.set(f"Loaded {len(self.ip_addresses)} IP addresses from {os.path.basename(filename)}")
            
            # Set infinite ping as default when loading file
            self.toggle_infinite()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load Excel file:\n{str(e)}")
            
    def ping_ip(self, ip_address, timeout, count):
        """Ping a single IP address"""
        try:
            # Use Windows ping command with proper encoding
            cmd = f"ping -n {count} -w {timeout} {ip_address}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='cp866')
            
            if result.returncode == 0:
                # Parse response time from output (supports English and Russian)
                output_lines = result.stdout.split('\n')
                times = []
                for line in output_lines:
                    # Check for English format (time=XXXms)
                    if 'time=' in line.lower():
                        try:
                            time_part = line.split('time=')[1].split('ms')[0]
                            if '<' in time_part:
                                times.append(1)  # Less than 1ms
                            else:
                                times.append(int(time_part))
                        except:
                            pass
                    # Check for Russian format (время=XXXмс)
                    elif 'время=' in line.lower():
                        try:
                            time_part = line.split('время=')[1].split('мс')[0]
                            if '<' in time_part:
                                times.append(1)  # Less than 1ms
                            else:
                                times.append(int(time_part))
                        except:
                            pass
                
                if times:
                    avg_time = sum(times) / len(times)
                    return True, f"{avg_time:.1f}"
                else:
                    return True, "< 1"
            else:
                return False, "Timeout"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"
            
    def ping_single_ip(self, ip, item_id, timeout, count):
        """Ping a single IP and return result"""
        success, response_time = self.ping_ip(ip, timeout, count)
        status = "Online" if success else "Offline"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return (item_id, ip, status, response_time, timestamp, success)
    
    def ping_worker(self):
        """Worker thread for pinging IPs in parallel"""
        timeout = int(self.timeout_var.get())
        count = int(self.count_var.get())
        max_workers = min(int(self.threads_var.get()), len(self.ip_addresses))
        
        # Prepare list of IPs and their tree items
        ping_tasks = []
        for item in self.tree.get_children():
            if not self.is_pinging:
                break
            ip = self.tree.item(item)['values'][0]
            ping_tasks.append((ip, item))
        
        self.root.after(0, lambda: self.status_var.set(f"Pinging {len(ping_tasks)} IPs in parallel..."))
        
        # Use ThreadPoolExecutor for parallel pinging
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all ping tasks
            future_to_item = {}
            for ip, item in ping_tasks:
                if not self.is_pinging:
                    break
                future = executor.submit(self.ping_single_ip, ip, item, timeout, count)
                future_to_item[future] = item
            
            # Process completed pings
            completed = 0
            for future in future_to_item:
                if not self.is_pinging:
                    break
                try:
                    result = future.result()
                    item_id, ip, status, response_time, timestamp, success = result
                    completed += 1
                    
                    # Update treeview in main thread
                    def update_tree(item_id=item_id, ip=ip, status=status, response_time=response_time, timestamp=timestamp, success=success, completed=completed, total=len(ping_tasks)):
                        # Get current description from treeview
                        current_values = self.tree.item(item_id)['values']
                        description = current_values[1] if len(current_values) > 1 else "-"
                        self.tree.item(item_id, values=(ip, description, status, response_time, timestamp))
                        # Color coding
                        if success:
                            self.tree.item(item_id, tags=('online',))
                        else:
                            self.tree.item(item_id, tags=('offline',))
                        # Update progress
                        self.status_var.set(f"Completed {completed}/{total} pings")
                            
                    self.root.after(0, update_tree)
                    
                except Exception as e:
                    print(f"Error pinging: {e}")
            
        # Ping completed
        if self.is_pinging:
            self.root.after(0, self.ping_completed)
        
    def start_ping(self):
        if not self.ip_addresses:
            messagebox.showwarning("Warning", "Please load an Excel file first!")
            return
            
        self.is_pinging = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        # Configure treeview tags for coloring
        self.tree.tag_configure('online', background='lightgreen')
        self.tree.tag_configure('offline', background='lightcoral')
        
        # Start ping in separate thread
        if self.infinite_var.get():
            self.infinite_ping = True
            threading.Thread(target=self.infinite_ping_worker, daemon=True).start()
        else:
            threading.Thread(target=self.ping_worker, daemon=True).start()
        
    def stop_ping(self):
        self.is_pinging = False
        self.infinite_ping = False
        self.ping_completed()
        
    def ping_completed(self):
        self.is_pinging = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_var.set("Ping completed")
        
    def clear_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.ping_results = []
        self.status_var.set("Results cleared")
        
    def toggle_infinite(self):
        """Toggle infinite ping mode and enable/disable count entry"""
        if self.infinite_var.get():
            self.count_entry.config(state="disabled")
            self.count_var.set("1")  # Use single ping for infinite mode
        else:
            self.count_entry.config(state="normal")
            self.count_var.set("4")  # Reset to default
    
    def infinite_ping_worker(self):
        """Worker thread for infinite pinging with parallel execution"""
        timeout = int(self.timeout_var.get())
        count = 1  # Always use 1 ping for infinite mode
        interval = int(self.interval_var.get())
        max_workers = min(int(self.threads_var.get()), len(self.ip_addresses))
        
        ping_round = 1
        
        while self.is_pinging and self.infinite_ping:
            self.root.after(0, lambda r=ping_round: self.status_var.set(f"Infinite ping - Round {r} (parallel)"))
            
            # Prepare list of IPs and their tree items
            ping_tasks = []
            for item in self.tree.get_children():
                if not self.is_pinging or not self.infinite_ping:
                    break
                ip = self.tree.item(item)['values'][0]
                ping_tasks.append((ip, item))
            
            if not ping_tasks:
                break
                
            # Use ThreadPoolExecutor for parallel pinging
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all ping tasks
                future_to_item = {}
                for ip, item in ping_tasks:
                    if not self.is_pinging or not self.infinite_ping:
                        break
                    future = executor.submit(self.ping_single_ip, ip, item, timeout, count)
                    future_to_item[future] = item
                
                # Process completed pings
                completed = 0
                for future in future_to_item:
                    if not self.is_pinging or not self.infinite_ping:
                        break
                    try:
                        result = future.result()
                        item_id, ip, status, response_time, timestamp, success = result
                        completed += 1
                        
                        # Update treeview in main thread
                        def update_tree(item_id=item_id, ip=ip, status=status, response_time=response_time, timestamp=timestamp, success=success, completed=completed, total=len(ping_tasks), round_num=ping_round):
                            # Get current description from treeview
                            current_values = self.tree.item(item_id)['values']
                            description = current_values[1] if len(current_values) > 1 else "-"
                            self.tree.item(item_id, values=(ip, description, status, response_time, timestamp))
                            # Color coding
                            if success:
                                self.tree.item(item_id, tags=('online',))
                            else:
                                self.tree.item(item_id, tags=('offline',))
                            # Update progress
                            self.status_var.set(f"Round {round_num}: {completed}/{total} completed")
                                
                        self.root.after(0, update_tree)
                        
                    except Exception as e:
                        print(f"Error pinging: {e}")
            
            # Wait for the specified interval before next round
            if self.is_pinging and self.infinite_ping:
                for remaining in range(interval, 0, -1):
                    if not self.is_pinging or not self.infinite_ping:
                        break
                    self.root.after(0, lambda r=remaining: self.status_var.set(f"Next round in {r} seconds..."))
                    time.sleep(1)
                ping_round += 1
        
        # Ping completed or stopped
        self.root.after(0, self.ping_completed)
    
    def export_results(self):
        if not self.tree.get_children():
            messagebox.showwarning("Warning", "No results to export!")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
        )
        
        if filename:
            try:
                # Collect data from treeview
                data = []
                for item in self.tree.get_children():
                    values = self.tree.item(item)['values']
                    data.append({
                        'IP Address': values[0],
                        'Description': values[1],
                        'Status': values[2],
                        'Response Time (ms)': values[3],
                        'Last Checked': values[4]
                    })
                
                df = pd.DataFrame(data)
                
                if filename.endswith('.csv'):
                    df.to_csv(filename, index=False)
                else:
                    df.to_excel(filename, index=False)
                    
                messagebox.showinfo("Success", f"Results exported to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results:\n{str(e)}")

def main():
    root = tk.Tk()
    app = PingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
