import tkinter as tk
from settings import *

class StatusPanel(tk.Frame):
    def __init__(self, parent, ports, width=400, height=100, circle_colors=None, **kwargs):
        """
        Status Panel with circles representing switch ports.
        
        :param parent: Parent widget
        :param ports: Number of ports on the switch
        :param width: Width of the rectangle
        :param height: Height of the rectangle
        :param circle_colors: A list of colors for the circles (default is gray)
        """
        super().__init__(parent, **kwargs)
        self.width = width
        self.height = height
        self.ports = ports
        self.circle_colors = circle_colors or [self.port_status["disconnected"]] * ports
        self.circle_colors[management_port - 1] = self.port_status["mgmt"]
        self.circle_objects = []

        # Create canvas to draw the panel
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # Draw the status panel
        self.draw_status_panel()
    port_status = {
        "success": {'bg_color': 'green', 'txt_color': 'white'},
        "failed": {'bg_color': 'red', 'txt_color': 'white'},
        "mgmt": {'bg_color': 'yellow', 'txt_color': 'black'},
        "connected": {'bg_color': 'lightblue', 'txt_color': 'black'},
        "disconnected": {'bg_color': 'lightgrey', 'txt_color': 'black'},
        "processing": {'bg_color': 'blue', 'txt_color': 'white'}
    }

    def draw_status_panel(self):
        self.canvas.delete("all")
        rows = 2
        cols = (self.ports + 1) // 2  # Calculate columns dynamically based on ports
        circle_size = min(self.width // (cols), self.height // (rows)) / 1.5
        x_margin = (self.width - (cols * (circle_size + 10))) // 2
        y_margin = (self.height - (rows * (circle_size + 10))) // 2

        for i in range(self.ports):
            row = i // cols
            col = i % cols
            x = x_margin + col * (circle_size + 10)
            y = y_margin + row * (circle_size + 10)
            color = self.circle_colors[i]['bg_color']
            # self.draw_circle(i, x, y, circle_size)
            # Draw the circle
            circle = self.canvas.create_oval(
                x, y, x + circle_size, y + circle_size, fill=color, outline="black"
            )
            # Draw the port number inside the circle
            text = self.canvas.create_text(
                x + circle_size / 2,
                y + circle_size / 2,
                text=str(i + 1),
                fill=self.circle_colors[i]['txt_color'],
                font=("Arial", 10),
            )
            self.circle_objects.append({'x': x, 'y': y, 'circle_size': circle_size, 'status': color})

    def update_circle_color(self, port, status):
        """
        Update the color of a specific port's circle.
        
        :param port: Port number (1-based index)
        :param color: New color for the circle
        """
        # (port - 1) since the array of ports is offset by one. ie: port1 is 2
        port = int(port) - 1
        c = self.circle_objects[port]

        if 1 <= port <= self.ports:
            self.circle_colors[port - 1] = self.port_status[status]
            c['color'] = self.port_status[status]
            self.draw_status_panel()
            # self.draw_circle(port=port, x=c['x'], y=c['y'], circle_size=c['circle_size'])

    def update_all_circle_color(self, status):
        """
        Update the color of all port circles to a new color.

        :param color: New color for all circles
        """
        self.circle_colors = [self.port_status[status]] * self.ports
        self.circle_colors[management_port - 1] = self.port_status["mgmt"]
        self.draw_status_panel()

    def draw_circle(self, port, x, y, circle_size):
        # Draw the circle
        circle = self.canvas.create_oval(
            x, y, x + circle_size, y + circle_size, fill=self.circle_colors[port]['bg_color'], outline="black"
        )
        # Draw the port number inside the circle
        text = self.canvas.create_text(
            x + circle_size / 2,
            y + circle_size / 2,
            text=str(port + 1),
            fill=self.circle_colors[port]['txt_color'],
            font=("Arial", 10),
        )