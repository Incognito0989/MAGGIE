import datetime
import threading
from time import sleep
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import ipaddress, sys
from components.file_dropper import FileDropper
from components.file_selector import FileSelector
from components.status_panel import StatusPanel
from utils.api_utils import *
from components.ip_range_selector import IPRangeSelector
from utils.ip_utils import *
from utils.switch_utils import *
from settings import *

class RedirectedOutput:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        # Add a timestamp before each message
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Format timestamp as you wish
        message_with_timestamp = f"[{timestamp}] {message}"

        # Temporarily enable the text widget to insert text
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message_with_timestamp)
        self.text_widget.see(tk.END)  # Auto-scroll to the latest output
        self.text_widget.config(state=tk.DISABLED)  # Disable it again to prevent editing
        
    def flush(self):  # To handle interactive environments
        pass

class ToolTab:
    def __init__(self, notebook, services_dir):
        self.notebook = notebook
        self.service_dir = services_dir
        self.processing_type = None
        self.payload = None

        # Create Tool tab
        tool_tab = ttk.Frame(self.notebook)
        self.notebook.add(tool_tab, text="Tool")

        # Mode selection (Config or Inventory)
        self.mode_notebook = ttk.Notebook(tool_tab)
        self.mode_notebook.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        # --- Config Tab ---
        config_frame = ttk.Frame(self.mode_notebook)
        self.mode_notebook.add(config_frame, text="By Config")

        #file dropper
        self.selector = FileSelector(config_frame)  # Change to the desired directory path
        self.selector.pack(padx=20, pady=20)
        self.service_dir = self.selector.selected_file_path
        
        # Button to start the configuration process
        begin_button = tk.Button(tool_tab, text="Begin Config", command=self.begin_config, bg="green", fg="black")
        begin_button.pack(side=tk.BOTTOM, expand=True, pady=10, padx=10, anchor="e")

        # Create and pack the Status Panel on the right side
        self.status_panel = StatusPanel(tool_tab, ports=48, width=tool_tab.winfo_screenwidth(), height=100)
        self.status_panel.pack(pady=20)

        # Console output display
        console_output = tk.Text(tool_tab, height=40, wrap="word", state="disabled")
        console_output.pack(fill="x", padx=10, pady=5)

        # Redirect stdout and sderr to the Text widget
        sys.stdout = RedirectedOutput(console_output)
        sys.stderr = RedirectedOutput(console_output)

    def validate_config_file(self, selected_file):
        if selected_file is None:
            print("No file has been selected")
            return False  # Nothing selected

        if not selected_file.endswith('.json'):
            print("Selected file is not of type json")
            return False  # File is not a JSON file
        
        try:
            with open(selected_file, 'r') as f:
                data = json.load(f)
            
            # Check for 'processing.processingType'
            processing_section = data.get("processing", {})
            processing_type = processing_section.get("processingType", "").strip()  # Ensure it's a string

            print(f"[DEBUG] Processing type read from JSON: '{processing_type}'")

            if not processing_type:
                print("Missing 'processingType' field in JSON.")
                return False

            # Define valid processing types
            valid_keywords = {"Decode", "Transcode", "Descramble"}

            # Find which valid keyword is in processingType
            matched_keyword = next((keyword for keyword in valid_keywords if keyword in processing_type), None)

            if not matched_keyword:
                print(f"Invalid processingType: '{processing_type}'. Expected to contain one of {valid_keywords}.")
                return False

            # Save the matched keyword
            self.processing_type = matched_keyword  
            print(f"[INFO] Matched processingType: '{self.processing_type}'")

            return True  # Valid processingType

        except (json.JSONDecodeError, FileNotFoundError) as e:
            # If there's an error loading the JSON, return False
            return False

    # Run config based on selected IP range or inventory file
    def begin_config(self):
            def background():
                print(self.selector.selected_file_path)
                self.payload = self.selector.selected_file_path
                # Validate that both the service type and config file are selected
                if not self.validate_config_file(self.selector.selected_file_path):
                    print("Validation failed. Please check the required fields.")
                    return  # Stop further execution of begin_config if validation failsvalidate_config_file(selector.selected_file_path)
            
                if self.mode_notebook.index("current") == 0:  # Config mode

                    # # Define path based on selected service type
                    # service_type = selected_service_type.get()
                    # service_dir = Path("./payloads/" + service_type + "/" + selected_file.get())

                    self.send_payload_all()


                elif self.mode_notebook.index("current") == 1:  # Inventory mode
                    if not self.inventory_file_loaded.get().startswith("Loaded file"):
                        messagebox.showwarning("Input Error", "Please upload an inventory file.")
                        return
                    messagebox.showinfo("Starting Config", f"Configuring based on {self.inventory_file_loaded.get()}.")

            # Run the process in a separate thread
            threading.Thread(target=background, daemon=True).start()

    def send_payload_all(self):
            print()
            print("INITIATING PAYLOAD PROCESS")

            #Get all operational ports to configure
            print("Getting operational ports")
            update_all_ports(switch_ip, 1)
            ports = get_active_ports(switch_ip)
            print("ACTIVE PORTS: ")
            print(ports)

            # turn off all ports except management
            print("Turning off all ports")
            update_all_ports(switch_ip, 2)
            self.status_panel.update_all_circle_color(status='disconnected')
            # print(get_all_port_status(switch_ip))

            # send payload for each port
            for port in ports:
                self.status_panel.update_circle_color(port, 'processing')
                print()

                # (port - 1) because the first port is number 2. this is done for readability
                print(f"===================MEG CONFIG ON PORT {(int(port) - 1)}========================")
                print(f"Turning port {port} on")
                set_port(switch_ip, port, 1)      # Turn port on

                sleep(6)                  # wait for meg to be reachable

                if is_ip_reachable(base_meg_ip):
                    print("Meg is reachable. Continuing with payload")
                else:
                    print("Meg is not reachable. Skipping this port")
                    self.status_panel.update_circle_color(port, status='failed')
                    continue

                # Get auth for this meg
                print("Getting authorization to meg")
                if post_auth(base_meg_ip) == 'error':
                    self.status_panel.update_circle_color(port, 'failed')
                    continue
                
                # make post request to meg
                if process_service_for_ip(self.processing_type, base_meg_ip, self.payload) == 'error':
                    self.status_panel.update_circle_color(port, 'failed')
                    continue

                # Turn port off
                set_port(switch_ip, port, 2)  

                # set status to green    
                self.status_panel.update_circle_color(port, status='success')  
            update_all_ports(switch_ip, 1)
            print()
            print("==============================================")
            print("PAYLOAD PROCESS COMPLETE")