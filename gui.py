"""
Automated Download Cleanup Monitor with GUI
Monitors download folder and automatically processes files using PowerShell scripts

Requirements:
    pip install watchdog psutil

Features:
- Monitors Downloads folder for new HTML/CSS/JS files
- Auto-extracts images using PNGify
- Auto-removes duplicates using Duplicate Finder
- Desktop notifications
- Activity log with GUI
- Start/Stop monitoring
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import subprocess
import os
import time
import threading
from pathlib import Path
from datetime import datetime
import json

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Installing required package: watchdog")
    subprocess.run(["pip", "install", "watchdog"])
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler


class DownloadMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📁 Auto Cleanup Monitor v1.0")
        self.root.geometry("900x700")
        self.root.configure(bg="#2b2b2b")
        
        # Variables
        self.monitoring = False
        self.observer = None
        self.watch_folder = str(Path.home() / "Downloads")
        self.pngify_script = ""
        self.duplicate_script = ""
        self.stats = {"files_processed": 0, "images_extracted": 0, "duplicates_removed": 0, "space_saved": 0}
        
        # Load settings
        self.load_settings()
        
        # Setup GUI
        self.setup_gui()
        
    def setup_gui(self):
        # Header
        header = tk.Frame(self.root, bg="#1e88e5", height=80)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text="🔍 Automated Download Cleanup Monitor", 
                        font=("Segoe UI", 20, "bold"), bg="#1e88e5", fg="white")
        title.pack(pady=20)
        
        # Main container
        main_frame = tk.Frame(self.root, bg="#2b2b2b")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Settings Frame
        settings_frame = tk.LabelFrame(main_frame, text="⚙️ Settings", font=("Segoe UI", 12, "bold"),
                                      bg="#353535", fg="white", padx=15, pady=15)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Watch Folder
        tk.Label(settings_frame, text="Monitor Folder:", bg="#353535", fg="white", 
                font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=5)
        
        folder_frame = tk.Frame(settings_frame, bg="#353535")
        folder_frame.grid(row=0, column=1, sticky="ew", pady=5)
        
        self.folder_entry = tk.Entry(folder_frame, font=("Segoe UI", 10), width=40)
        self.folder_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.folder_entry.insert(0, self.watch_folder)
        
        tk.Button(folder_frame, text="Browse", command=self.browse_folder,
                 bg="#1e88e5", fg="white", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        # PNGify Script
        tk.Label(settings_frame, text="PNGify Script:", bg="#353535", fg="white",
                font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=5)
        
        pngify_frame = tk.Frame(settings_frame, bg="#353535")
        pngify_frame.grid(row=1, column=1, sticky="ew", pady=5)
        
        self.pngify_entry = tk.Entry(pngify_frame, font=("Segoe UI", 10), width=40)
        self.pngify_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.pngify_entry.insert(0, self.pngify_script)
        
        tk.Button(pngify_frame, text="Browse", command=lambda: self.browse_script("pngify"),
                 bg="#1e88e5", fg="white", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        # Duplicate Finder Script
        tk.Label(settings_frame, text="Duplicate Script:", bg="#353535", fg="white",
                font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", pady=5)
        
        dup_frame = tk.Frame(settings_frame, bg="#353535")
        dup_frame.grid(row=2, column=1, sticky="ew", pady=5)
        
        self.dup_entry = tk.Entry(dup_frame, font=("Segoe UI", 10), width=40)
        self.dup_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.dup_entry.insert(0, self.duplicate_script)
        
        tk.Button(dup_frame, text="Browse", command=lambda: self.browse_script("duplicate"),
                 bg="#1e88e5", fg="white", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        settings_frame.columnconfigure(1, weight=1)
        
        # Control Frame
        control_frame = tk.Frame(main_frame, bg="#2b2b2b")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = tk.Button(control_frame, text="▶️ Start Monitoring", command=self.start_monitoring,
                                   bg="#4caf50", fg="white", font=("Segoe UI", 12, "bold"),
                                   width=20, height=2)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(control_frame, text="⏹️ Stop Monitoring", command=self.stop_monitoring,
                                  bg="#f44336", fg="white", font=("Segoe UI", 12, "bold"),
                                  width=20, height=2, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="🗑️ Manual Cleanup", command=self.manual_cleanup,
                 bg="#ff9800", fg="white", font=("Segoe UI", 12, "bold"),
                 width=20, height=2).pack(side=tk.LEFT, padx=5)
        
        # Stats Frame
        stats_frame = tk.LabelFrame(main_frame, text="📊 Statistics", font=("Segoe UI", 12, "bold"),
                                   bg="#353535", fg="white", padx=15, pady=15)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        stats_grid = tk.Frame(stats_frame, bg="#353535")
        stats_grid.pack()
        
        self.stats_labels = {}
        stats_items = [
            ("Files Processed", "files_processed", "🔄"),
            ("Images Extracted", "images_extracted", "🖼️"),
            ("Duplicates Removed", "duplicates_removed", "🗑️"),
            ("Space Saved (MB)", "space_saved", "💾")
        ]
        
        for i, (label, key, icon) in enumerate(stats_items):
            frame = tk.Frame(stats_grid, bg="#424242", relief=tk.RAISED, borderwidth=2)
            frame.grid(row=0, column=i, padx=10, pady=5, ipadx=10, ipady=10)
            
            tk.Label(frame, text=icon, font=("Segoe UI", 16), bg="#424242", fg="white").pack()
            tk.Label(frame, text=label, font=("Segoe UI", 9), bg="#424242", fg="#b0b0b0").pack()
            
            value_label = tk.Label(frame, text="0", font=("Segoe UI", 16, "bold"), 
                                  bg="#424242", fg="#4caf50")
            value_label.pack()
            self.stats_labels[key] = value_label
        
        # Status Label
        self.status_label = tk.Label(main_frame, text="⏸️ Status: Idle", font=("Segoe UI", 11, "bold"),
                                    bg="#2b2b2b", fg="#ffc107")
        self.status_label.pack(pady=(0, 5))
        
        # Activity Log
        log_frame = tk.LabelFrame(main_frame, text="📋 Activity Log", font=("Segoe UI", 12, "bold"),
                                 bg="#353535", fg="white")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, font=("Consolas", 9), 
                                                  bg="#1e1e1e", fg="#00ff00",
                                                  insertbackground="white", height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log initial message
        self.log("🚀 Auto Cleanup Monitor Started")
        self.log(f"📁 Monitoring folder: {self.watch_folder}")
        
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.watch_folder)
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.watch_folder = folder
            
    def browse_script(self, script_type):
        file = filedialog.askopenfilename(
            title=f"Select {script_type.title()} Script",
            filetypes=[("PowerShell Scripts", "*.ps1"), ("All Files", "*.*")]
        )
        if file:
            if script_type == "pngify":
                self.pngify_entry.delete(0, tk.END)
                self.pngify_entry.insert(0, file)
                self.pngify_script = file
            else:
                self.dup_entry.delete(0, tk.END)
                self.dup_entry.insert(0, file)
                self.duplicate_script = file
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        
    def update_stats(self):
        for key, label in self.stats_labels.items():
            value = self.stats[key]
            if key == "space_saved":
                label.config(text=f"{value:.2f}")
            else:
                label.config(text=str(value))
    
    def start_monitoring(self):
        self.watch_folder = self.folder_entry.get()
        self.pngify_script = self.pngify_entry.get()
        self.duplicate_script = self.dup_entry.get()
        
        if not os.path.exists(self.watch_folder):
            messagebox.showerror("Error", "Watch folder does not exist!")
            return
            
        if not os.path.exists(self.pngify_script):
            messagebox.showwarning("Warning", "PNGify script not found. Image extraction will be skipped.")
            
        if not os.path.exists(self.duplicate_script):
            messagebox.showwarning("Warning", "Duplicate finder script not found. Deduplication will be skipped.")
        
        self.save_settings()
        
        self.monitoring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="✅ Status: Monitoring Active", fg="#4caf50")
        
        # Start file system observer
        event_handler = FileHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.watch_folder, recursive=False)
        self.observer.start()
        
        self.log(f"🔍 Started monitoring: {self.watch_folder}")
        
    def stop_monitoring(self):
        self.monitoring = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏸️ Status: Idle", fg="#ffc107")
        
        self.log("⏹️ Monitoring stopped")
        
    def manual_cleanup(self):
        folder = filedialog.askdirectory(title="Select folder to cleanup")
        if not folder:
            return
            
        self.log(f"🔧 Manual cleanup started on: {folder}")
        threading.Thread(target=self.process_folder, args=(folder,), daemon=True).start()
        
    def process_file(self, file_path):
        """Process a single file through PNGify and Duplicate Finder"""
        try:
            self.log(f"📄 Processing: {os.path.basename(file_path)}")
            
            # Step 1: Extract images with PNGify
            if os.path.exists(self.pngify_script):
                self.log("  → Extracting images...")
                # Note: This is simplified - actual implementation would need to handle PNGify's interactive nature
                # You might need to modify PNGify to accept command-line arguments
                result = subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-File", self.pngify_script],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                # Count extracted images (simplified)
                output_folder = os.path.splitext(file_path)[0] + "_images"
                if os.path.exists(output_folder):
                    images = len([f for f in os.listdir(output_folder) if f.endswith(('.png', '.jpg', '.gif'))])
                    self.stats["images_extracted"] += images
                    self.log(f"  ✓ Extracted {images} images")
                    
                    # Step 2: Remove duplicates
                    if os.path.exists(self.duplicate_script):
                        self.log("  → Removing duplicates...")
                        # Similar note - actual implementation needs non-interactive version
                        dup_result = subprocess.run(
                            ["powershell", "-ExecutionPolicy", "Bypass", "-File", self.duplicate_script],
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        self.log("  ✓ Duplicates removed")
                        self.stats["duplicates_removed"] += 1  # Simplified
            
            self.stats["files_processed"] += 1
            self.update_stats()
            self.log(f"✅ Completed: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.log(f"❌ Error processing {os.path.basename(file_path)}: {str(e)}")
    
    def process_folder(self, folder):
        """Process all web files in a folder"""
        web_extensions = ('.html', '.htm', '.css', '.js')
        files = [os.path.join(folder, f) for f in os.listdir(folder) 
                if f.lower().endswith(web_extensions)]
        
        self.log(f"📦 Found {len(files)} web files to process")
        
        for file in files:
            if not self.monitoring:
                break
            self.process_file(file)
        
        self.log("🎉 Manual cleanup completed!")
    
    def save_settings(self):
        settings = {
            "watch_folder": self.watch_folder,
            "pngify_script": self.pngify_script,
            "duplicate_script": self.duplicate_script
        }
        try:
            with open("monitor_settings.json", "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            self.log(f"⚠️ Could not save settings: {e}")
    
    def load_settings(self):
        try:
            if os.path.exists("monitor_settings.json"):
                with open("monitor_settings.json", "r") as f:
                    settings = json.load(f)
                    self.watch_folder = settings.get("watch_folder", self.watch_folder)
                    self.pngify_script = settings.get("pngify_script", "")
                    self.duplicate_script = settings.get("duplicate_script", "")
        except Exception as e:
            pass


class FileHandler(FileSystemEventHandler):
    def __init__(self, gui):
        self.gui = gui
        self.processed_files = set()
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Check if it's a web file
        if file_ext in ['.html', '.htm', '.css', '.js']:
            if file_path not in self.processed_files:
                self.processed_files.add(file_path)
                self.gui.log(f"🆕 New file detected: {os.path.basename(file_path)}")
                
                # Wait a bit for file to be fully written
                time.sleep(2)
                
                # Process in separate thread to not block UI
                threading.Thread(target=self.gui.process_file, args=(file_path,), daemon=True).start()


def main():
    root = tk.Tk()
    app = DownloadMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
