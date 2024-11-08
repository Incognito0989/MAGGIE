import tkinter as tk
from tkinter import ttk

class IPRangeSelector(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Variables for checkbox and IP entries
        self.send_to_all_connected = tk.BooleanVar()

        self.pack(fill="x", padx=10, pady=10)

        # Checkbox
        self.check_button = ttk.Checkbutton(
            self, text="Send to All Connected", 
            variable=self.send_to_all_connected,
            command=self.toggle_ip_range_entries
        )
        self.check_button.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # IP Range Start Entry
        self.ip_start_label = ttk.Label(self, text="IP Range Start:")
        self.ip_start_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.ip_start_entry = ttk.Entry(self)
        self.ip_start_entry.grid(row=1, column=1, padx=5, pady=5)

        # IP Range End Entry
        self.ip_end_label = ttk.Label(self, text="IP Range End:")
        self.ip_end_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.ip_end_entry = ttk.Entry(self)
        self.ip_end_entry.grid(row=2, column=1, padx=5, pady=5)

        # Initialize entries as enabled
        self.toggle_ip_range_entries()

    def toggle_ip_range_entries(self):
        if self.send_to_all_connected.get():
            # Hide and disable the IP range fields
            self.ip_start_label.grid_remove()
            self.ip_start_entry.grid_remove()
            self.ip_start_entry.config(state='disabled')

            self.ip_end_label.grid_remove()
            self.ip_end_entry.grid_remove()
            self.ip_end_entry.config(state='disabled')
        else:
            # Show and enable the IP range fields
            self.ip_start_label.grid()
            self.ip_start_entry.grid()
            self.ip_start_entry.config(state='normal')

            self.ip_end_label.grid()
            self.ip_end_entry.grid()
            self.ip_end_entry.config(state='normal')

    # Getter for IP range start
    def get_ip_start(self):
        print(self.ip_start_entry.get())
        return self.ip_start_entry.get()

    # Getter for IP range end
    def get_ip_end(self):
        return self.ip_end_entry.get()