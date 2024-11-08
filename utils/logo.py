import tkinter as tk
from PIL import Image, ImageTk

class ResizableImageApp(tk.Frame):
    def __init__(self, root, image_path):
        super().__init__()


        # Load the image
        self.original_image = Image.open(image_path)
        self.image_tk = ImageTk.PhotoImage(self.original_image)

        # Create a label to display the image
        self.image_label = tk.Label(self, image=self.image_tk)
        self.image_label.grid(row=0, column=0, columnspan=3, sticky="n", pady=10)

        # Keep a reference to the image to avoid garbage collection
        self.image_label.image = self.image_tk
        # Bind the configure event to resize the image
        self.bind("<Configure>", self.resize_image)
        self.pack()

    def resize_image(self, event):
        # Get the current size of the window
        max_width = 400
        max_height = 100

        # Calculate the new size while maintaining aspect ratio
        image_ratio = self.original_image.width / self.original_image.height
        window_ratio = max_width / max_height

        if max_width < self.original_image.width or max_height < self.original_image.height:
            if window_ratio > image_ratio:
                new_width = int(max_height * image_ratio)
                new_height = max_height
            else:
                new_width = max_width
                new_height = int(max_width / image_ratio)

            # Resize the image only if the new dimensions are different
            if new_width != self.image_tk.width() or new_height != self.image_tk.height():
                resized_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.image_tk = ImageTk.PhotoImage(resized_image)
                self.image_label.config(image=self.image_tk)
                self.image_label.image = self.image_tk  # Keep a reference