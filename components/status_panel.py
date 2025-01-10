import tkinter as tk
from tkinter import ttk

class StatusPanel(tk.Frame):
    def __init__(self, parent, port_count=10, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Dictionary to track each port's status canvas for color updates
        self.port_canvases = {}

        # Create a grid of port status indicators
        for port in range(1, port_count + 1):
            row = (port - 1) % 4  # Two columns per row
            col = (port - 1) // 4
            
            # Create a frame for each port with padding
            port_frame = tk.Frame(self, width=150, height=80, bg="#f0f0f0", relief="flat")
            port_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Use a Canvas to create rounded box
            canvas = tk.Canvas(port_frame, width=140, height=60, highlightthickness=0)
            canvas.pack(expand=True)
            
            self.update_port_status(port, "off")

            # Store the canvas for updating colors and status text
            self.port_canvases[port] = canvas

    def update_port_status(self, port, status):
        """
        Update the color and status text of the port based on its status.
        Status options: "off", "failed", "complete"
        """
        color_mapping = {
            "off": "blue",  # Grey for "off"
            "failed": "#ff4d4d",  # Red for "failed"
            "complete": "#4caf50"  # Green for "complete"
        }
        color = color_mapping.get(status, "#808080")
        
        if port in self.port_canvases:
            canvas = self.port_canvases[port]
            self._create_rounded_rectangle(canvas, 40, 10, 135, 55, radius=20, fill=color)
            canvas.create_text(90, 20, text=f"Port {port}", font=("Arial", 12, "bold"), fill="white")
            canvas.create_text(90, 40, text="Status: N/A", font=("Arial", 10), fill="white", tag="status")
            canvas.itemconfigure("status", text=f"Status: {status.capitalize()}")

    def _create_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
        """
        Helper function to draw a rounded rectangle on a canvas.
        """
        points = [
            x1 + radius, y1,
            x1 + radius, y1,
            x2 - radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)
