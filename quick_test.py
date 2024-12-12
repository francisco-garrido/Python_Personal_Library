import tkinter as tk
from tkinter import font

def show_fonts():
    root = tk.Tk()
    root.title("Available Fonts")
    root.geometry("800x600")
    fonts = list(font.families())  # Get all available fonts
    fonts.sort()  # Sort alphabetically
    print(f"Found {len(fonts)} fonts")  # Debug print
    
    canvas = tk.Canvas(root)  # Create canvas and scrollbar
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    
    canvas.configure(yscrollcommand=scrollbar.set)  # Configure scrolling
    
    for font_name in fonts:  # Add fonts to frame
        label = tk.Label(scrollable_frame, 
                        text=f"{font_name} - Sample Text", 
                        font=(font_name, 14),
                        pady=5)
        label.pack()
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")  # Pack widgets
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    
    scrollable_frame.update_idletasks()  # Update scroll region
    canvas.configure(scrollregion=canvas.bbox("all"))
    
    root.mainloop()

if __name__ == "__main__":
    show_fonts() 