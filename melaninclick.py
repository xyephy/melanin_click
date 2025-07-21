#!/usr/bin/env python3
"""
Melanin Click - Cross-platform Bitcoin & Whive Manager
A unified application that works on macOS, Linux, and Windows
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os
import sys
import urllib.request
import threading
from queue import Queue
import subprocess
import logging
import platform
import json
import re
from logging.handlers import RotatingFileHandler

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import zipfile
        import psutil
    except ImportError:
        print("Required Windows packages missing. Please run: pip install psutil")
        sys.exit(1)
else:  # macOS and Linux
    import tarfile

# Version Constants
BITCOIN_VERSION = "28.2"
WHIVE_VERSION = "22.2.3"

# Set up logging with rotation
log_handler = RotatingFileHandler("melanin_click.log", maxBytes=5*1024*1024, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[log_handler]
)

def get_platform_info():
    """Get detailed platform information"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": get_architecture(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }

def get_architecture():
    """Detect system architecture"""
    arch = platform.machine().lower()
    if arch in ["x86_64", "amd64", "i386", "i686"]:
        return "x86_64"
    elif arch in ["arm64", "aarch64"]:
        return "arm64"
    else:
        return "unknown"

def get_bitcoin_download_url():
    """Get appropriate Bitcoin download URL based on OS and architecture"""
    os_type = platform.system()
    arch = get_architecture()
    
    if os_type == "Darwin":  # macOS
        if arch == "arm64":
            return f"https://bitcoincore.org/bin/bitcoin-core-{BITCOIN_VERSION}/bitcoin-{BITCOIN_VERSION}-arm64-apple-darwin.tar.gz"
        else:
            return f"https://bitcoincore.org/bin/bitcoin-core-{BITCOIN_VERSION}/bitcoin-{BITCOIN_VERSION}-x86_64-apple-darwin.tar.gz"
    elif os_type == "Linux":
        if arch == "arm64":
            return f"https://bitcoincore.org/bin/bitcoin-core-{BITCOIN_VERSION}/bitcoin-{BITCOIN_VERSION}-aarch64-linux-gnu.tar.gz"
        else:
            return f"https://bitcoincore.org/bin/bitcoin-core-{BITCOIN_VERSION}/bitcoin-{BITCOIN_VERSION}-x86_64-linux-gnu.tar.gz"
    elif os_type == "Windows":
        return f"https://bitcoincore.org/bin/bitcoin-core-{BITCOIN_VERSION}/bitcoin-{BITCOIN_VERSION}-win64.zip"
    else:
        # Default to x86_64 macOS
        return f"https://bitcoincore.org/bin/bitcoin-core-{BITCOIN_VERSION}/bitcoin-{BITCOIN_VERSION}-x86_64-apple-darwin.tar.gz"

def get_whive_download_url():
    """Get appropriate Whive download URL based on OS and architecture"""
    os_type = platform.system()
    arch = get_architecture()
    
    if os_type == "Darwin":  # macOS
        if arch == "arm64":
            return f"https://github.com/whiveio/whive_releases/releases/download/{WHIVE_VERSION}/whive-ventura-{WHIVE_VERSION}-arm64.tar.gz"
        else:
            return f"https://github.com/whiveio/whive_releases/releases/download/{WHIVE_VERSION}/whive-ventura-{WHIVE_VERSION}-osx64.tar.gz"
    elif os_type == "Linux":
        # For Linux, we'll default to x86_64 as arm64 might not be available
        return f"https://github.com/whiveio/whive_releases/releases/download/{WHIVE_VERSION}/whive-{WHIVE_VERSION}-x86_64-linux-gnu.tar.gz"
    elif os_type == "Windows":
        return f"https://github.com/whiveio/whive_releases/releases/download/{WHIVE_VERSION}/whive-{WHIVE_VERSION}-win64.zip"
    else:
        # Default to x86_64 macOS
        return f"https://github.com/whiveio/whive_releases/releases/download/{WHIVE_VERSION}/whive-ventura-{WHIVE_VERSION}-osx64.tar.gz"

def ensure_binary_permissions(binary_path):
    """Ensure binary is executable"""
    os_type = platform.system()
    
    if os_type != "Windows":  # Linux and macOS
        try:
            os.chmod(binary_path, 0o755)  # rwx r-x r-x
            logging.info(f"Set executable permissions for {os.path.basename(binary_path)}")
            return True
        except Exception as e:
            logging.error(f"Failed to set permissions: {e}")
            return False
    return True  # Windows doesn't need permission changes

def check_disk_space(path="/"):
    """Check available disk space in GB"""
    if platform.system() == "Windows":
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(path), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value / (1024**3)
    else:
        s = os.statvfs(path)
        return s.f_frsize * s.f_bavail / (10**9)

def get_file_extension():
    """Get the appropriate file extension based on the OS"""
    os_type = platform.system()
    if os_type == "Windows":
        return ".zip"
    else:  # macOS and Linux
        return ".tar.gz"

def get_executable_extension():
    """Get the appropriate executable extension based on the OS"""
    return ".exe" if platform.system() == "Windows" else ""

class Application(tk.Tk):
    """Main application window"""
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Melanin Click - Bitcoin & Whive Manager")
        
        os_type = platform.system()
        
        # Platform-specific UI adjustments
        if os_type == "Darwin":  # macOS
            try:
                # macOS high DPI support
                self.tk.call('tk::unsupported::MacWindowStyle', 'style', self._w, 'moveableModal', '')
            except Exception as e:
                logging.warning(f"MacWindowStyle error (non-critical): {e}")
        elif os_type == "Linux":
            # Linux scaling
            try:
                self.tk.call('tk', 'scaling', 1.0)
            except Exception as e:
                logging.warning(f"Tk scaling error (non-critical): {e}")
        
        # Responsive sizing
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Adjust size based on screen dimensions
        width = min(620, int(screen_width * 0.6))
        height = min(692, int(screen_height * 0.7))
        
        self.minsize(width, height)
        self.geometry(f"{width}x{height}")
        self.protocol("WM_DELETE_WINDOW", self.exit_app)

        # Setup UI differently for Windows vs Unix-like systems
        if os_type == "Windows":
            # Simpler UI for Windows (no scrollbars)
            self.container = tk.Frame(self)
            self.container.pack(side="top", fill="both", expand=True)
        else:
            # More complex UI with scrollbar for macOS and Linux
            self.canvas = tk.Canvas(self, bg="#2e2e2e", highlightthickness=0)
            self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.container = ttk.Frame(self.canvas)
            self.canvas.configure(yscrollcommand=self.scrollbar.set)

            self.scrollbar.pack(side="right", fill="y")
            self.canvas.pack(side="left", fill="both", expand=True)
            
            self.canvas_window = self.canvas.create_window((0, 0), window=self.container, anchor="nw")
            self.container.bind("<Configure>", self.update_scrollregion_and_width)

        # Make container responsive
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Create frames
        self.frames = {}
        for F in (StartPage, TermsPage, InstallPage):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)
        self.initialize_platform_ui()
        
        # Log the platform information
        platform_info = get_platform_info()
        logging.info(f"Application started on: {json.dumps(platform_info)}")

    def update_scrollregion_and_width(self, event):
        """Update the scrollbar region when the frame size changes"""
        if hasattr(self, 'canvas'):  # Only for Unix-like systems
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.itemconfig(self.canvas_window, width=self.container.winfo_reqwidth())

    def show_frame(self, page):
        """Show the specified frame"""
        frame = self.frames[page]
        frame.tkraise()
        
        if platform.system() != "Windows":  # Only for Unix-like systems
            self.container.update_idletasks()
            if hasattr(self, 'canvas') and hasattr(self, 'canvas_window'):
                self.canvas.itemconfig(self.canvas_window, width=self.container.winfo_reqwidth())
                if self.winfo_width() > self.container.winfo_reqwidth():
                    self.canvas.itemconfig(self.canvas_window, width=self.winfo_width() - self.scrollbar.winfo_width())

    def initialize_platform_ui(self):
        """Apply platform-specific UI adjustments"""
        os_type = platform.system()
        logging.info(f"Initializing UI for {os_type} platform")

    def exit_app(self):
        """Exit the application"""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.quit()
            logging.info("Application shutdown initiated by user.")

class StartPage(ttk.Frame):
    """Welcome page"""
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        
        os_type = platform.system()
        
        # Different styling for Windows vs Unix-like
        if os_type == "Windows":
            # Windows styling
            main_frame = tk.Frame(self)
            main_frame.place(relx=0.5, rely=0.1, anchor="n")

            # Windows logo
            logo_label = tk.Label(main_frame, text="🖱️", font=("Arial", 50))
            logo_label.pack(pady=(20, 10))

            # Title and subtitle
            tk.Label(main_frame, text="Melanin Click", font=("Arial", 24, "bold")).pack(pady=(0, 5))
            tk.Label(main_frame, text="Bitcoin & Whive Wallet and Miner Manager", font=("Arial", 12)).pack(pady=(0, 20))

            # Buttons
            tk.Button(
                main_frame, text="Get Started", 
                command=lambda: controller.show_frame(TermsPage),
                font=("Arial", 10, "bold"), bg="#0078d7", fg="white", padx=10, pady=5
            ).pack(fill="x", padx=20, pady=5)
            
            tk.Button(
                main_frame, text="Exit", 
                command=controller.exit_app,
                font=("Arial", 10), bg="#555555", fg="white", padx=10, pady=5
            ).pack(fill="x", padx=20, pady=5)
        
        else:
            # macOS and Linux styling with ttk
            main_frame = ttk.Frame(self, style="Card.TFrame")
            main_frame.place(relx=0.5, rely=0.1, anchor="n")

            # Logo
            logo_label = ttk.Label(main_frame, text="🖱️", font=("Helvetica", 50), background="#3a3a3a", foreground="white")
            logo_label.pack(pady=(20, 10))

            # Title and subtitle
            ttk.Label(main_frame, text="Melanin Click", font=("Helvetica", 24, "bold"), background="#3a3a3a", foreground="white").pack(pady=(0, 5))
            ttk.Label(main_frame, text="Bitcoin & Whive Wallet and Miner Manager", font=("Helvetica", 12), background="#3a3a3a", foreground="#cccccc").pack(pady=(0, 20))

            # Buttons
            ttk.Button(main_frame, text="Get Started", command=lambda: controller.show_frame(TermsPage), style="Accent.TButton").pack(fill="x", padx=20, pady=5)
            ttk.Button(main_frame, text="Exit", command=controller.exit_app, style="Secondary.TButton").pack(fill="x", padx=20, pady=5) 

class TermsPage(ttk.Frame):
    """Terms and Conditions page"""
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        
        os_type = platform.system()
        
        if os_type == "Windows":
            # Windows styling
            # Title
            tk.Label(self, text="Terms and Conditions", font=("Arial", 14, "bold")).pack(pady=5)

            # Text area with scrollbar
            text_frame = tk.Frame(self)
            text_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self.text = tk.Text(text_frame, height=10, wrap="word")
            scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
            self.text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            self.text.pack(side="left", fill="both", expand=True)

            # Acceptance checkbox
            self.terms_accepted = tk.BooleanVar()
            tk.Checkbutton(
                self, text="I accept the Terms and Conditions", 
                variable=self.terms_accepted, 
                command=self.toggle_next_button
            ).pack(pady=2)

            # Button frame
            button_frame = tk.Frame(self)
            button_frame.pack(pady=5, fill="x")
            
            self.next_button = tk.Button(
                button_frame, text="Next", state='disabled',
                command=lambda: controller.show_frame(InstallPage),
                font=("Arial", 10, "bold"), bg="#0078d7", fg="white"
            )
            self.next_button.pack(side="left", padx=2, fill="x", expand=True)
            
            tk.Button(
                button_frame, text="Exit",
                command=controller.exit_app,
                font=("Arial", 10), bg="#555555", fg="white"
            ).pack(side="left", padx=2, fill="x", expand=True)
        
        else:
            # macOS and Linux styling
            # Title
            ttk.Label(self, text="Terms and Conditions", font=("Helvetica", 14, "bold")).pack(pady=5)

            # Text area with scrollbar
            text_frame = ttk.Frame(self)
            text_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self.text = tk.Text(text_frame, height=10, wrap="word")
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
            self.text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            self.text.pack(side="left", fill="both", expand=True)

            # Acceptance checkbox
            self.terms_accepted = tk.BooleanVar()
            ttk.Checkbutton(self, text="I accept the Terms and Conditions", variable=self.terms_accepted, command=self.toggle_next_button).pack(pady=2)

            # Button frame
            button_frame = ttk.Frame(self)
            button_frame.pack(pady=5, fill="x")
            self.next_button = ttk.Button(button_frame, text="Next", state='disabled', command=lambda: controller.show_frame(InstallPage), style="Accent.TButton")
            self.next_button.pack(side="left", padx=2, fill="x", expand=True)
            ttk.Button(button_frame, text="Exit", command=controller.exit_app).pack(side="left", padx=2, fill="x", expand=True)

        self.load_terms()

    def toggle_next_button(self):
        """Enable or disable the Next button based on checkbox state"""
        self.next_button.config(state='normal' if self.terms_accepted.get() else 'disabled')

    def load_terms(self):
        """Load the terms and conditions from the remote URL or local file"""
        # First try to load from a local file
        local_path = "melanin_click_terms_of_use.md"
        if os.path.exists(local_path):
            try:
                with open(local_path, 'r') as f:
                    self.text.insert('end', f.read())
                logging.info("Terms loaded from local file.")
                self.text.config(state='disabled')
                return
            except Exception as e:
                logging.error(f"Failed to load terms from local file: {e}")
        
        # If local file not available, try to download
        url = "https://raw.githubusercontent.com/melaninsolar/melaninclick/main/melanin_click_terms_of_use.md"
        try:
            with urllib.request.urlopen(url) as response:
                self.text.insert('end', response.read().decode())
            logging.info("Terms loaded successfully from URL.")
        except urllib.error.URLError as e:
            error_msg = f"Failed to load terms: {e}"
            self.text.insert('end', error_msg)
            logging.error(error_msg)
        self.text.config(state='disabled') 

class InstallPage(ttk.Frame):
    """Installation and management page"""
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.cancel_flag = False
        self.message_queue = Queue()
        # Start processing the message queue
        self.after(100, self.process_queue)
        
        # Main content grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Output Area
        output_frame = ttk.LabelFrame(self, text="Output", padding=5)
        output_frame.grid(row=0, column=0, sticky="nsew", pady=5, padx=5)
        self.output = tk.Text(output_frame, state='disabled', height=5, wrap="word")
        self.output.tag_configure("error", foreground="red")
        self.output.tag_configure("success", foreground="green")
        self.output.pack(fill="both", expand=True)

        # Content Frame
        content_frame = ttk.Frame(self)
        content_frame.grid(row=1, column=0, sticky="nsew", pady=5, padx=5)
        content_frame.columnconfigure(0, weight=1)

        # Bitcoin Section
        bitcoin_frame = ttk.LabelFrame(content_frame, text="Bitcoin Core Wallet & Miner", padding=5)
        bitcoin_frame.pack(fill="x", pady=2)
        self._create_bitcoin_section(bitcoin_frame)

        # Whive Section
        whive_frame = ttk.LabelFrame(content_frame, text="Whive Core Wallet & Miner", padding=5)
        whive_frame.pack(fill="x", pady=2)
        self._create_whive_section(whive_frame)

        # Progress and Controls
        control_frame = ttk.Frame(self)
        control_frame.grid(row=2, column=0, sticky="ew", pady=5, padx=5)
        control_frame.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.grid(row=0, column=0, sticky="ew", pady=2)
        self._create_control_buttons(control_frame)

        # Load saved config
        self.load_config()
        
    def _create_bitcoin_section(self, parent):
        parent.columnconfigure(0, weight=1)
        ttk.Button(parent, text="Install Bitcoin Core", command=self.check_storage_and_install_bitcoin).grid(row=0, column=0, pady=1, sticky="ew")
        self.run_mainnet_button = ttk.Button(parent, text="Run Full Node", state='disabled', command=self.run_mainnet)
        self.run_mainnet_button.grid(row=1, column=0, pady=1, sticky="ew")
        self.run_pruned_node_button = ttk.Button(parent, text="Run Pruned Node", state='disabled', command=self.run_pruned_node)
        self.run_pruned_node_button.grid(row=2, column=0, pady=1, sticky="ew")
        self.status_bitcoin_button = ttk.Button(parent, text="Check Node Status", state='disabled', command=self.check_bitcoin_status)
        self.status_bitcoin_button.grid(row=3, column=0, pady=1, sticky="ew")

        ttk.Label(parent, text="Mining Device:").grid(row=4, column=0, pady=1, sticky="w")
        self.miner_type = tk.StringVar(value="CPU Mining")
        ttk.OptionMenu(parent, self.miner_type, "CPU Mining", "CPU Mining", "StickMiner").grid(row=5, column=0, pady=1, sticky="ew")

        ttk.Label(parent, text="Bitcoin Mining Pool:").grid(row=6, column=0, pady=1, sticky="w")
        self.bitcoin_pool = tk.StringVar(value="CKPool")
        self.bitcoin_pool_options = {
            "CKPool": "stratum+tcp://solo.ckpool.org:3333",
            "Public Pool": "stratum+tcp://public-pool.io:21496",
            "Ocean Pool": "stratum+tcp://stratum.ocean.xyz:3000",
            "Ocean Pool (Alt)": "stratum+tcp://mine.ocean.xyz:3334"
        }
        ttk.OptionMenu(parent, self.bitcoin_pool, "CKPool", *self.bitcoin_pool_options.keys()).grid(row=7, column=0, pady=1, sticky="ew")

        self.public_pool_button = ttk.Button(parent, text="Run Pool Miner", state='disabled', command=self.run_bitcoin_miner)
        self.public_pool_button.grid(row=8, column=0, pady=1, sticky="ew")

    def _create_whive_section(self, parent):
        parent.columnconfigure(0, weight=1)
        ttk.Button(parent, text="Install Whive Core", command=self.check_storage_and_install_whive).grid(row=0, column=0, pady=1, sticky="ew")
        self.run_whive_button = ttk.Button(parent, text="Run Full Node", state='disabled', command=self.run_whive)
        self.run_whive_button.grid(row=1, column=0, pady=1, sticky="ew")
        self.status_whive_button = ttk.Button(parent, text="Check Node Status", state='disabled', command=self.check_whive_status)
        self.status_whive_button.grid(row=2, column=0, pady=1, sticky="ew")
        self.run_cpuminer_button = ttk.Button(parent, text="Run Pool Miner", state='disabled', command=self.run_whive_miner)
        self.run_cpuminer_button.grid(row=3, column=0, pady=1, sticky="ew")

    def _create_control_buttons(self, parent):
        parent.columnconfigure((0, 1, 2), weight=1)
        self.cancel_button = ttk.Button(parent, text="Cancel", command=self.cancel_install, state='disabled')
        self.cancel_button.grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(parent, text="Help", command=self.display_help).grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(parent, text="Exit", command=self.controller.exit_app, style="Accent.TButton").grid(row=1, column=2, padx=2, pady=2, sticky="ew")

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.miner_type.set(config.get("miner_type", "CPU Mining"))
                self.bitcoin_pool.set(config.get("bitcoin_pool", "CKPool"))
            logging.info("Configuration loaded.")
        except FileNotFoundError:
            pass

    def save_config(self):
        config = {
            "miner_type": self.miner_type.get(),
            "bitcoin_pool": self.bitcoin_pool.get()
        }
        with open("config.json", "w") as f:
            json.dump(config, f)
        logging.info("Configuration saved.")

    def check_storage_and_install_bitcoin(self):
        self.cancel_flag = False
        self.progress.start()
        self.cancel_button.config(state='normal')
        bitcoin_install_path = os.path.expanduser('~/bitcoin-core')
        
        if os.path.exists(bitcoin_install_path):
            if not messagebox.askyesno("Update", f"Bitcoin Core {BITCOIN_VERSION} is installed. Update it?"):
                self.update_output("Skipping Bitcoin Core update.", "success")
                self.enable_bitcoin_buttons()
                self.progress.stop()
                return

        self.update_output("Checking storage for Bitcoin...")
        free_space = check_disk_space()

        # Different install strategies based on available space
        if free_space > 600:
            self.update_output(f"Detected {free_space:.2f}GB free space. Installing full node support.")
            threading.Thread(
                target=self.install,
                args=('bitcoin', get_bitcoin_download_url(), False)
            ).start()
        elif free_space > 10:
            self.update_output(f"Detected {free_space:.2f}GB free space. Installing with pruned mode support.")
            threading.Thread(
                target=self.install,
                args=('bitcoin', get_bitcoin_download_url(), True)
            ).start()
        else:
            self.update_output(f"Insufficient space: {free_space:.2f} GB available. Need at least 10GB.", "error")
            self.progress.stop()

    def check_storage_and_install_whive(self):
        self.cancel_flag = False
        self.progress.start()
        self.cancel_button.config(state='normal')
        whive_install_path = os.path.expanduser('~/whive-core')
        
        if os.path.exists(whive_install_path):
            if not messagebox.askyesno("Update", f"Whive Core {WHIVE_VERSION} is installed. Update it?"):
                self.update_output("Skipping Whive Core update.", "success")
                self.enable_whive_buttons()
                self.progress.stop()
                return

        self.update_output("Checking storage for Whive...")
        free_space = check_disk_space()

        if free_space > 10:
            self.update_output(f"Detected {free_space:.2f}GB free space. Installing Whive Core.")
            threading.Thread(
                target=self.install,
                args=('whive', get_whive_download_url(), False)
            ).start()
        else:
            self.update_output(f"Insufficient space: {free_space:.2f} GB available. Need at least 10GB.", "error")
            self.progress.stop()

    def install(self, software, download_url, prune=False):
        self.update_output(f"Downloading {software} for {platform.system()} ({get_architecture()})...")
        install_path = os.path.expanduser(f'~/{software}-core')
        os_type = platform.system()
        
        # Get appropriate file extension based on OS
        file_ext = get_file_extension()
        downloaded_file = os.path.join(install_path, f"{software}{file_ext}")
        os.makedirs(install_path, exist_ok=True)

        try:
            # Download with progress updates
            def reporthook(blocknum, blocksize, totalsize):
                if totalsize > 0:
                    percent = min(100, blocknum * blocksize * 100 / totalsize)
                    self.message_queue.put((f"Downloading: {percent:.1f}%", None))
            
            urllib.request.urlretrieve(download_url, downloaded_file, reporthook=reporthook)
            
            if self.cancel_flag:
                os.remove(downloaded_file)
                self.message_queue.put(("Installation cancelled.", "error"))
                self.progress.stop()
                self.cancel_button.config(state='disabled')
                return
                
            self.message_queue.put((f"Extracting {software}...", None))
            
            # Extract based on OS
            if os_type == "Windows":
                with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
                    zip_ref.extractall(path=install_path)
            else:  # macOS and Linux
                with tarfile.open(downloaded_file, "r:gz") as tar:
                    tar.extractall(path=install_path)
            
            os.remove(downloaded_file)
            
            # Set executable permissions on binaries
            bin_dir = self.find_bin_directory(install_path, software)
            if bin_dir and os.path.exists(bin_dir):
                for binary in os.listdir(bin_dir):
                    binary_path = os.path.join(bin_dir, binary)
                    if os.path.isfile(binary_path) and not binary.endswith('.dll') and not binary.endswith('.exe.config'):
                        ensure_binary_permissions(binary_path)
            
            self.message_queue.put((f"{software.capitalize()} Core {BITCOIN_VERSION if software == 'bitcoin' else WHIVE_VERSION} installed successfully!", "success"))
            
            # Enable the appropriate buttons based on what was installed
            if software == 'bitcoin':
                self.controller.after(0, self.enable_bitcoin_buttons)
            else:
                self.controller.after(0, self.enable_whive_buttons)
                
            # Create default configuration file for Bitcoin
            if software == 'bitcoin':
                data_dir = os.path.expanduser('~/.bitcoin/mainnet')
                conf_path = os.path.join(data_dir, 'bitcoin.conf')
                if not os.path.exists(conf_path):
                    os.makedirs(data_dir, exist_ok=True)
                    self.create_bitcoin_conf(conf_path, prune)
            
        except Exception as e:
            self.message_queue.put((f"Failed to install {software}: {str(e)}", "error"))
            logging.error(f"Installation error: {e}")
        finally:
            self.progress.stop()
            self.cancel_button.config(state='disabled')

    def find_bin_directory(self, base_path, software):
        """Find the bin directory in the extracted software folder"""
        for root, dirs, files in os.walk(base_path):
            if 'bin' in dirs:
                bin_dir = os.path.join(root, 'bin')
                # Check if this bin directory contains expected binaries
                expected_binary = f"{software}-qt" if software == 'bitcoin' else f"{software}-qt"
                for item in os.listdir(bin_dir):
                    if expected_binary in item:
                        return bin_dir
        return None

    def enable_bitcoin_buttons(self):
        self.run_mainnet_button.config(state='normal')
        self.run_pruned_node_button.config(state='normal')
        self.public_pool_button.config(state='normal')
        self.status_bitcoin_button.config(state='normal')

    def enable_whive_buttons(self):
        self.run_whive_button.config(state='normal')
        self.run_cpuminer_button.config(state='normal')
        self.status_whive_button.config(state='normal')

    def run_mainnet(self):
        os_type = platform.system()
        exe_ext = get_executable_extension()
        
        # Build paths based on OS and version
        bitcoin_path = os.path.join(os.path.expanduser('~'), "bitcoin-core")
        binary_name = f"bitcoin-qt{exe_ext}"
        
        # Find the binary directory
        bin_dir = self.find_bin_directory(bitcoin_path, "bitcoin")
        if bin_dir:
            bitcoin_path = os.path.join(bin_dir, binary_name)
        else:
            bitcoin_path = os.path.join(bitcoin_path, f"bitcoin-{BITCOIN_VERSION}", "bin", binary_name)
        
        mainnet_conf_dir = os.path.join(os.path.expanduser('~'), ".bitcoin/mainnet")
        conf_path = os.path.join(mainnet_conf_dir, "bitcoin.conf")
        if not os.path.exists(conf_path):
            os.makedirs(mainnet_conf_dir, exist_ok=True)
            self.create_bitcoin_conf(conf_path, prune=False)
        
        self.run_software(bitcoin_path, f"-conf={conf_path}")

    def run_pruned_node(self):
        os_type = platform.system()
        exe_ext = get_executable_extension()
        
        # Build paths based on OS and version
        bitcoin_path = os.path.join(os.path.expanduser('~'), "bitcoin-core")
        binary_name = f"bitcoin-qt{exe_ext}"
        
        # Find the binary directory
        bin_dir = self.find_bin_directory(bitcoin_path, "bitcoin")
        if bin_dir:
            bitcoin_path = os.path.join(bin_dir, binary_name)
        else:
            bitcoin_path = os.path.join(bitcoin_path, f"bitcoin-{BITCOIN_VERSION}", "bin", binary_name)
        
        pruned_conf_dir = os.path.join(os.path.expanduser('~'), ".bitcoin/pruned")
        conf_path = os.path.join(pruned_conf_dir, "bitcoin.conf")
        if not os.path.exists(conf_path):
            os.makedirs(pruned_conf_dir, exist_ok=True)
            self.create_bitcoin_conf(conf_path, prune=True)
        
        self.run_software(bitcoin_path, f"--datadir={pruned_conf_dir}", f"-conf={conf_path}")

    def create_bitcoin_conf(self, conf_path, prune=False):
        os_type = platform.system()
        arch = get_architecture()
        
        # Base configuration
        conf_content = ["daemon=1", "txindex=1"]
        
        # Pruning if requested
        if prune:
            conf_content.append("prune=550")
        
        # OS-specific settings
        if os_type == "Linux":
            # Add Linux-specific optimizations
            conf_content.append("dbcache=450")
        elif os_type == "Darwin":
            # Add macOS-specific optimizations
            conf_content.append("dbcache=800")
        elif os_type == "Windows":
            # Add Windows-specific optimizations
            conf_content.append("dbcache=1024")
            
        # Architecture-specific optimizations
        if arch == "arm64":
            # ARM64 processors may benefit from lower thread counts
            conf_content.append("par=4")
        else:
            # x86_64 processors can often handle more threads
            conf_content.append("par=8")
            
        # Write the configuration file
        with open(conf_path, 'w') as conf_file:
            conf_file.write("\n".join(conf_content))
        self.update_output(f"Created bitcoin.conf at {conf_path} with {os_type}/{arch} optimizations")

    def check_bitcoin_status(self):
        self.check_node_status("bitcoin")

    def check_whive_status(self):
        self.check_node_status("whive")

    def check_node_status(self, software):
        os_type = platform.system()
        exe_ext = get_executable_extension()
        
        bin_path = os.path.join(os.path.expanduser('~'), f"{software}-core")
        cli_name = f"{software}-cli{exe_ext}"
        
        # Find the binary directory
        bin_dir = self.find_bin_directory(bin_path, software)
        if bin_dir:
            cli_path = os.path.join(bin_dir, cli_name)
        else:
            version = BITCOIN_VERSION if software == "bitcoin" else WHIVE_VERSION
            cli_path = os.path.join(bin_path, f"{software}-{version}", "bin", cli_name)
        
        try:
            result = subprocess.check_output([cli_path, "getblockchaininfo"], stderr=subprocess.STDOUT).decode()
            self.update_output(f"{software.capitalize()} Node Status:\n{result}", "success")
        except subprocess.CalledProcessError as e:
            self.update_output(f"Error checking {software} status: {e.output.decode()}", "error")
        except Exception as e:
            self.update_output(f"Failed to check {software} status: {e}", "error")

    def run_bitcoin_miner(self):
        if not messagebox.askyesno("Disclaimer", "Mining may cause hardware wear. Proceed?"):
            return

        bitcoin_address = simpledialog.askstring("Input", "Enter Bitcoin address:", parent=self)
        if not bitcoin_address or not self.validate_btc_address(bitcoin_address):
            self.update_output("Invalid or no Bitcoin address provided. Please use a valid BTC address (e.g., bc1q... or 1...)", "error")
            return
        machine_name = simpledialog.askstring("Input", "Enter machine name (worker ID):", parent=self)
        if not machine_name:
            self.update_output("No machine name provided.", "error")
            return

        whive_path = os.path.expanduser('~/whive-core')
        minerd_path = os.path.join(whive_path, "whive", "miner", "minerd")
        
        if platform.system() == "Windows":
            minerd_path += ".exe"
            
        if not os.path.exists(minerd_path):
            self.update_output("Bitcoin miner not found. Please install Whive Core first.", "error")
            return

        pool_url = self.bitcoin_pool_options[self.bitcoin_pool.get()]
        cmd = f'{minerd_path} -a sha256d -o {pool_url} -u {bitcoin_address}.{machine_name} -p x'
        self.run_terminal_command(cmd, "Bitcoin")

    def run_whive_miner(self):
        if not messagebox.askyesno("Disclaimer", "Mining may cause hardware wear. Proceed?"):
            return

        whive_address = simpledialog.askstring("Input", "Enter Whive address:", parent=self)
        if not whive_address:
            self.update_output("No Whive address provided.", "error")
            return

        whive_path = os.path.expanduser('~/whive-core')
        minerd_path = os.path.join(whive_path, "whive", "miner", "minerd")
        
        if platform.system() == "Windows":
            minerd_path += ".exe"
            
        if not os.path.exists(minerd_path):
            self.update_output("Whive miner not found. Please install Whive Core first.", "error")
            return

        cmd = f'{minerd_path} -a yespower -o stratum+tcp://206.189.2.17:3333 -u {whive_address}.w1 -t 2'
        self.run_terminal_command(cmd, "Whive")

    def run_whive(self):
        os_type = platform.system()
        exe_ext = get_executable_extension()
        
        whive_path = os.path.join(os.path.expanduser('~'), "whive-core")
        binary_name = f"whive-qt{exe_ext}"
        
        # Find the binary directory
        bin_dir = self.find_bin_directory(whive_path, "whive")
        if bin_dir:
            whive_path = os.path.join(bin_dir, binary_name)
        else:
            whive_path = os.path.join(whive_path, "whive", "bin", binary_name)
        
        if not os.path.exists(whive_path):
            if os_type == "Darwin" and messagebox.askyesno("Whive Missing", "Whive GUI not found. Install DMG?"):
                dmg_path = os.path.expanduser("~/Downloads/whive-22.2.3-osx-unsigned.dmg")
                urllib.request.urlretrieve("https://github.com/whiveio/whive_releases/releases/download/22.2.3/whive-22.2.3-osx-unsigned.dmg", dmg_path)
                subprocess.Popen(["open", dmg_path])
            else:
                self.update_output("Whive GUI not found. Please install Whive Core first.", "error")
            return
        
        self.run_software(whive_path)

    def run_terminal_command(self, cmd, software):
        os_type = platform.system()
        try:
            if os_type == "Darwin":  # macOS
                osascript_cmd = f'osascript -e \'tell application "Terminal" to do script "{cmd}"\''
                subprocess.Popen(osascript_cmd, shell=True)
            elif os_type == "Linux":
                # Try common Linux terminal emulators
                terminals = ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"]
                terminal_cmd = None
                
                for term in terminals:
                    try:
                        if subprocess.call(["which", term], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
                            if term == "gnome-terminal":
                                terminal_cmd = [term, "--", "bash", "-c", f"{cmd}; exec bash"]
                            else:
                                terminal_cmd = [term, "-e", f"{cmd}"]
                            break
                    except:
                        continue
                
                if terminal_cmd:
                    subprocess.Popen(terminal_cmd)
                else:
                    self.update_output("No suitable terminal found. Try installing xterm.", "error")
                    return
            elif os_type == "Windows":
                # Windows command prompt
                subprocess.Popen(["cmd.exe", "/c", "start", "cmd", "/k", cmd])
            else:
                self.update_output(f"Unsupported platform: {os_type}", "error")
                return
                
            pool_name = self.bitcoin_pool.get() if hasattr(self, 'bitcoin_pool') else "default pool"
            self.update_output(f"Started {software} mining on {pool_name}...", "success")
            logging.info(f"Started {software} miner with command: {cmd}")
        except Exception as e:
            self.update_output(f"Failed to start {software} miner: {e}", "error")
            logging.error(f"Failed to start {software} miner: {e}")

    def run_software(self, software_path, *args):
        try:
            # Ensure the binary is executable
            ensure_binary_permissions(software_path)
            
            # Resolve path for bitcoin/whive based on version and architecture
            if not os.path.exists(software_path):
                base_dir = os.path.dirname(os.path.dirname(software_path))
                binary_name = os.path.basename(software_path)
                version = BITCOIN_VERSION if "bitcoin" in binary_name else WHIVE_VERSION
                
                # Try to find the correct binary path
                bin_dir = self.find_bin_directory(base_dir, "bitcoin" if "bitcoin" in binary_name else "whive")
                if bin_dir:
                    for file in os.listdir(bin_dir):
                        if binary_name in file:
                            software_path = os.path.join(bin_dir, file)
                            break
            
            if not os.path.exists(software_path):
                self.update_output(f"Software not found at {software_path}", "error")
                return
                
            subprocess.Popen([software_path, *args])
            self.update_output(f"Started {os.path.basename(software_path)}...", "success")
            logging.info(f"Started {software_path}")
        except Exception as e:
            self.update_output(f"Failed to start {software_path}: {e}", "error")
            logging.error(f"Failed to start {software_path}: {e}")

    def validate_btc_address(self, address):
        pattern = r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-zA-HJ-NP-Z0-9]{38,58}$"
        is_valid = bool(re.match(pattern, address))
        if not is_valid:
            logging.warning(f"Invalid Bitcoin address entered: {address}")
        return is_valid

    def display_help(self):
        help_text = (
            "Melanin Click Help:\n"
            "- Install: Download and set up Bitcoin or Whive Core.\n"
            "- Run Full Node: Start a full Bitcoin node (requires ~600GB).\n"
            "- Run Pruned Node: Start a pruned Bitcoin node (~10GB).\n"
            "- Run Miner: Connect to a selected pool (CKPool, Public Pool, Ocean Pool, Ocean Pool Alt).\n"
            "- Check Status: View node sync progress.\n"
            "- Bitcoin Address: Use a valid BTC address (e.g., 1..., 3..., bc1...).\n"
            "Contact support at support@melaninclick.com for assistance."
        )
        self.update_output(help_text)
        
    def update_output(self, message, tag=None):
        """Update the output text widget"""
        self.output.config(state='normal')
        self.output.insert('end', message + "\n", tag)
        self.output.config(state='disabled')
        self.output.see('end')
        
    def process_queue(self):
        """Process messages from the queue"""
        try:
            while not self.message_queue.empty():
                msg = self.message_queue.get()
                if isinstance(msg, tuple):
                    message, tag = msg
                else:
                    message, tag = msg, None
                self.update_output(message, tag)
                
            # Schedule next processing
            self.after(100, self.process_queue)
        except Exception as e:
            logging.error(f"Error processing message queue: {e}")
            self.after(100, self.process_queue)
            
    def cancel_install(self):
        """Cancel any ongoing installation"""
        self.cancel_flag = True
        self.update_output("Cancelling installation...", "error")
        
    def destroy(self):
        """Save config when the frame is destroyed"""
        self.save_config()
        super().destroy()

# Main application startup
if __name__ == "__main__":
    try:
        # Print debug information
        print(f"Starting Melanin Click on {platform.system()} ({get_architecture()})")
        
        # Set TK_SILENCE_DEPRECATION to suppress the deprecation warning on macOS
        if platform.system() == "Darwin":
            os.environ['TK_SILENCE_DEPRECATION'] = '1'
        
        # Create and start the application
        app = Application()
        
        # Platform-specific style customization
        os_type = platform.system()
        
        # Log platform info
        logging.info(f"Starting Melanin Click on {os_type} ({get_architecture()})")
        
        # Apply styles based on platform
        if os_type == "Windows":
            # Windows doesn't use ttk styling as much
            pass
        else:
            # macOS and Linux styling with ttk
            style = ttk.Style()
            
            # Base styles for Unix-like platforms
            style.configure("TFrame", background="#2e2e2e")
            style.configure("TLabel", background="#2e2e2e", foreground="white")
            style.configure("TButton", background="#444444", foreground="white")
            style.configure("Card.TFrame", background="#3a3a3a", relief="raised", borderwidth=2)
            
            # Choose appropriate font family
            if os_type == "Darwin":  # macOS
                font_family = "Helvetica"
            else:  # Linux
                font_family = "DejaVu Sans"
                try:
                    tk.font.Font(family=font_family, size=10)
                except:
                    font_family = "Sans"
            
            # Configure button styles
            style.configure("Accent.TButton", font=(font_family, 10, "bold"), 
                            foreground="white", background="#0078d7")
            style.map("Accent.TButton", background=[("active", "#005bb5")])
            style.configure("Secondary.TButton", font=(font_family, 10), 
                            foreground="white", background="#555555")
            style.map("Secondary.TButton", background=[("active", "#444444")])
            style.configure("TLabelFrame", background="#2e2e2e", foreground="white", 
                            font=(font_family, 12, "bold"))
            
            # Add more padding for Linux
            if os_type == "Linux":
                style.configure("TButton", padding=3)
        
        # Set background color for the main application window
        if os_type != "Windows":
            app.configure(bg="#2e2e2e")
        
        print("Starting main application loop...")
        
        # Start the application
        app.mainloop()
        
    except Exception as e:
        print(f"ERROR: Application failed to start: {e}")
        import traceback
        traceback.print_exc() 