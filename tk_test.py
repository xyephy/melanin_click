#!/usr/bin/env python3
"""
Simple Tkinter test to verify GUI rendering
"""
import tkinter as tk
import os

os.environ['TK_SILENCE_DEPRECATION'] = '1'

def create_window():
    # Create the main window
    root = tk.Tk()
    root.title("Tkinter Test")
    root.geometry("300x200")
    
    # Create a label
    label = tk.Label(root, text="Hello, Tkinter is working!", font=("Helvetica", 14))
    label.pack(pady=20)
    
    # Create a button
    button = tk.Button(root, text="Click Me", command=lambda: label.config(text="Button clicked!"))
    button.pack(pady=10)
    
    print("Tkinter window created")
    
    # Start the event loop
    root.mainloop()
    print("Window closed")

if __name__ == "__main__":
    print("Starting Tkinter test...")
    create_window() 