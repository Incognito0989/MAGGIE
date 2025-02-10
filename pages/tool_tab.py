import datetime
import threading
from time import sleep
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import ipaddress, sys

import paramiko
from components.file_dropper import FileDropper
from components.configurator import ConfigPanel
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

        # Mode selection (Config or Generator)
        self.mode_notebook = ttk.Notebook(tool_tab)
        self.mode_notebook.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        # --- Config Tab ---
        config_frame = ttk.Frame(self.mode_notebook)
        self.mode_notebook.add(config_frame, text="By Config File")

        # --- Gen Tab ---
        gen_frame = ttk.Frame(self.mode_notebook)
        # self.mode_notebook.add(gen_frame, text="Setting Generator")
        self.config_panel = ConfigPanel(gen_frame)
        self.config_panel.pack(padx=10, pady=10)

        #file dropper
        self.selector = FileSelector(config_frame)  # Change to the desired directory path
        self.selector.pack(padx=20, pady=20)
        self.service_dir = self.selector.selected_file_path
        
        # Button to start the configuration process
        self.begin_button = tk.Button(tool_tab, text="Begin Config", command=self.begin_config, bg="green", fg="black")
        self.begin_button.pack(side=tk.BOTTOM, expand=True, pady=10, padx=10, anchor="e")

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
            try:
                print("Configuration process started...")
                
                if self.mode_notebook.index("current") == 0:  # Config mode
                    print(self.selector.selected_file_path)
                    self.payload = self.selector.selected_file_path
                    
                    if not self.validate_config_file(self.selector.selected_file_path):
                        print("Validation failed. Stopping process.")
                        return  # Stop execution if validation fails

                    self.send_payload_all()

                elif self.mode_notebook.index("current") == 1:  # Generator mode
                    if self.config_panel.fill_json_template():
                        self.payload = self.config_panel.get_payload()
                        self.processing_type = self.config_panel.get_processing_type()
                        print(f"Processing Type: {self.processing_type}")
                        print(f"Payload: \n {self.payload}")

                print("Configuration process completed.")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                print("... Process Done ...")

        # Run the process in a separate thread
        self.config_thread = threading.Thread(target=background, daemon=True)
        self.config_thread.start()     

    def send_payload_all(self):
            print()
            print("INITIATING PAYLOAD PROCESS")

            #Get all operational ports to configure
            print("Getting operational ports")
            update_all_ports(switch_ip, 1)
            sleep(10)
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
                # Check stop_event before proceeding
                if self.stop_event.is_set():
                    print("Configuration canceled.")
                    return
                self.status_panel.update_circle_color(port, 'processing')
                print()

                # (port - 1) because the first port is number 2. this is done for readability
                print(f"===================MEG CONFIG ON PORT {(int(port) - 1)}========================")
                print(f"Turning port {int(port) - 1} on")
                set_port(switch_ip, port, 1)      # Turn port on

                if is_ip_reachable(meg_ip, duration=60):
                    print("Meg is reachable. Continuing with payload")
                else:
                    print("Meg is not reachable. Skipping this port")
                    self.status_panel.update_circle_color(port, status='failed')
                    set_port(switch_ip, port, 2)  
                    continue

                # Get auth for this meg
                print("Getting authorization to meg")
                if post_auth(meg_ip) == 'error':
                    self.status_panel.update_circle_color(port, 'failed')
                    set_port(switch_ip, port, 2)  
                    continue
                
                # make post request to meg
                if process_service_for_ip(self.processing_type, base_meg_ip, self.payload) == 'error':
                    self.status_panel.update_circle_color(port, 'failed')
                    set_port(switch_ip, port, 2)  
                    continue

                # Turn port off
                set_port(switch_ip, port, 2)  

                # set status to green    
                self.status_panel.update_circle_color(port, status='success')  
            update_all_ports(switch_ip, 1)
            print()
            print("==============================================")
            print("PAYLOAD PROCESS COMPLETE")
