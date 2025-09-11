#!/usr/bin/env python3
"""
Directory Optimizer GUI Application

A modern GUI for the Directory Comparison and Optimization Tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import datetime
import threading
from pathlib import Path
from typing import List
import queue

# Import the core modules
from Organizer import DirectoryOptimizer
from Restorer import ReversalManager
import ErrorLogger


class DirectoryOptimizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Directory Optimizer")
        self.root.geometry("800x700")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.base_path_var = tk.StringVar()
        self.patterns_var = tk.StringVar(value="*")
        self.dry_run_var = tk.BooleanVar(value=True)
        
        # Queue for thread communication
        self.progress_queue = queue.Queue()
        
        # Initialize ErrorLogger with GUI callback
        ErrorLogger.initialize_logger(gui_callback=self.log_message_to_text)
        
        self.create_widgets()
        self.check_progress_queue()
        self.update_reversal_button_state()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Directory Optimizer", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Base path selection
        ttk.Label(main_frame, text="Base Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        path_frame.columnconfigure(0, weight=1)
        
        self.path_entry = ttk.Entry(path_frame, textvariable=self.base_path_var, width=60)
        self.path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.path_entry.bind('<KeyRelease>', self.on_path_change)
        
        browse_button = ttk.Button(path_frame, text="Browse", command=self.browse_directory)
        browse_button.grid(row=0, column=1)
        
        # Patterns
        ttk.Label(main_frame, text="Directory Patterns:").grid(row=2, column=0, sticky=tk.W, pady=5)
        pattern_entry = ttk.Entry(main_frame, textvariable=self.patterns_var, width=50)
        pattern_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))
        
        ttk.Label(main_frame, text="(e.g., Make.*, Project.*, *)", 
                 font=('Arial', 8), foreground='gray').grid(row=2, column=2, sticky=tk.W)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        options_frame.columnconfigure(0, weight=1)
        
        dry_run_check = ttk.Checkbutton(options_frame, text="Dry Run (Preview mode - no actual changes)", 
                                       variable=self.dry_run_var)
        dry_run_check.grid(row=0, column=0, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.optimize_button = ttk.Button(button_frame, text="Start Optimization", 
                                         command=self.start_optimization, style='Accent.TButton')
        self.optimize_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reverse_button = ttk.Button(button_frame, text="Reverse Last Optimization", 
                                        command=self.reverse_optimization)
        self.reverse_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.scan_button = ttk.Button(button_frame, text="Scan Directory", 
                                     command=self.scan_directory)
        self.scan_button.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, text="Status:").grid(row=5, column=0, sticky=tk.W, pady=(20, 5))
        self.status_label = ttk.Label(main_frame, textvariable=self.progress_var, 
                                     foreground='blue')
        self.status_label.grid(row=5, column=1, columnspan=2, sticky=tk.W, pady=(20, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        clear_button = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_button.grid(row=1, column=0, pady=(10, 0))
        
        # Configure styles
        style = ttk.Style()
        style.configure('Accent.TButton', foreground='white')
        
    def on_path_change(self, event=None):
        """Called when path changes to update reversal button state"""
        self.root.after(100, self.update_reversal_button_state)
        
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.base_path_var.set(directory)
            self.log_message(f"Selected directory: {directory}")
            self.update_reversal_button_state()
    
    def log_message_to_text(self, message):
        """Add message to log text widget (used as GUI callback)"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def log_message(self, message):
        """Add message to log with timestamp using ErrorLogger"""
        ErrorLogger.log_message(message)
    
    def clear_log(self):
        self.log_text.delete('1.0', tk.END)
    
    def update_status(self, message):
        self.progress_var.set(message)
        self.root.update_idletasks()
    
    def progress_callback(self, message):
        """Callback for optimizer progress updates"""
        self.progress_queue.put(message)
    
    def check_progress_queue(self):
        """Check for progress updates from worker thread"""
        try:
            while True:
                message = self.progress_queue.get_nowait()
                self.log_message(message)
                self.update_status("Processing...")
        except queue.Empty:
            pass
        
        self.root.after(100, self.check_progress_queue)
    
    def update_reversal_button_state(self):
        """Update the state of the reversal button based on available state"""
        if not self.base_path_var.get() or not os.path.exists(self.base_path_var.get()):
            self.reverse_button.configure(state='disabled')
            return
        
        try:
            reversal_manager = ReversalManager(self.base_path_var.get())
            can_reverse, message = reversal_manager.can_reverse()
            
            if can_reverse:
                self.reverse_button.configure(state='normal')
                # Update tooltip or button text if needed
            else:
                self.reverse_button.configure(state='disabled')
                
        except Exception:
            # Log the exception but don't show GUI error for this
            self.reverse_button.configure(state='disabled')
    
    def validate_inputs(self):
        if not self.base_path_var.get():
            ErrorLogger.handle_exception(
                ValueError("Please select a base directory"), 
                "Input validation",
                show_gui_error=True,
                gui_error_callback=lambda title, msg: messagebox.showerror(title, msg)
            )
            return False
        
        if not os.path.exists(self.base_path_var.get()):
            ErrorLogger.handle_exception(
                ValueError("Selected directory does not exist"), 
                "Input validation",
                show_gui_error=True,
                gui_error_callback=lambda title, msg: messagebox.showerror(title, msg)
            )
            return False
        
        return True
    
    def scan_directory(self):
        """Scan directory and show what would be optimized"""
        if not self.validate_inputs():
            return
        
        try:
            base_path = Path(self.base_path_var.get())
            patterns = [p.strip() for p in self.patterns_var.get().split(',') if p.strip()]
            
            all_dirs = []
            for pattern in patterns:
                matching_dirs = list(base_path.glob(pattern))
                matching_dirs = [d for d in matching_dirs if d.is_dir()]
                all_dirs.extend(matching_dirs)
            
            self.log_message("=== Directory Scan Results ===")
            self.log_message(f"Base directory: {base_path}")
            self.log_message(f"Patterns: {patterns}")
            self.log_message(f"Found {len(all_dirs)} directories:")
            
            for directory in sorted(all_dirs):
                self.log_message(f"  • {directory.name}")
            
            if len(all_dirs) < 2:
                self.log_message("⚠️ Need at least 2 directories for optimization")
            else:
                self.log_message(f"✓ Ready to optimize {len(all_dirs)} directories")
                
                # Show potential groupings
                optimizer = DirectoryOptimizer(str(base_path), dry_run=True)
                remaining_dirs = all_dirs.copy()
                group_count = 0
                
                self.log_message("\n=== Potential Groupings ===")
                while len(remaining_dirs) >= 2:
                    current_group = [remaining_dirs.pop(0)]
                    group_names = [current_group[0].name]
                    
                    i = 0
                    while i < len(remaining_dirs):
                        test_names = group_names + [remaining_dirs[i].name]
                        if optimizer.find_common_prefix(test_names):
                            current_group.append(remaining_dirs.pop(i))
                            group_names.append(current_group[-1].name)
                        else:
                            i += 1
                    
                    if len(current_group) >= 2:
                        group_count += 1
                        common_prefix = optimizer.find_common_prefix([d.name for d in current_group])
                        self.log_message(f"Group {group_count} (prefix: '{common_prefix}'):")
                        for directory in current_group:
                            self.log_message(f"  • {directory.name}")
                    else:
                        remaining_dirs.append(current_group[0])
                        break
                
                if group_count == 0:
                    self.log_message("No common prefixes found for grouping")
                
        except Exception as e:
            error_msg = ErrorLogger.handle_exception(
                e, 
                "Directory scan",
                show_gui_error=True,
                gui_error_callback=lambda title, msg: messagebox.showerror("Scan Error", msg)
            )
    
    def start_optimization(self):
        """Start the optimization process in a separate thread"""
        if not self.validate_inputs():
            return
        
        # Disable buttons during processing
        self.optimize_button.configure(state='disabled')
        self.reverse_button.configure(state='disabled')
        self.scan_button.configure(state='disabled')
        self.progress_bar.start(10)
        
        def run_optimization():
            try:
                base_path = self.base_path_var.get()
                patterns = [p.strip() for p in self.patterns_var.get().split(',') if p.strip()]
                dry_run = self.dry_run_var.get()
                
                optimizer = DirectoryOptimizer(base_path, dry_run=dry_run, 
                                             progress_callback=self.progress_callback)
                optimizer.optimize_directories(patterns)
                
                self.progress_queue.put("=== Optimization Complete ===")
                
            except Exception as e:
                error_msg = ErrorLogger.handle_exception(e, "Optimization process")
                self.progress_queue.put(f"ERROR: {error_msg}")
            finally:
                # Re-enable buttons
                self.root.after(0, self.enable_buttons)
        
        thread = threading.Thread(target=run_optimization)
        thread.daemon = True
        thread.start()
    
    def reverse_optimization(self):
        """Reverse the last optimization"""
        if not self.validate_inputs():
            return
        
        base_path = self.base_path_var.get()
        
        # Check if reversal is possible
        reversal_manager = ReversalManager(base_path)
        can_reverse, message = reversal_manager.can_reverse()
        
        if not can_reverse:
            messagebox.showwarning("Cannot Reverse", message)
            return
        
        result = messagebox.askyesno("Confirm Reversal", 
                                   f"Are you sure you want to reverse the last optimization?\n\n"
                                   f"{message}\n\n"
                                   f"This will restore the original directory structure and "
                                   f"duplicate files.")
        if not result:
            return
        
        # Disable buttons during processing
        self.optimize_button.configure(state='disabled')
        self.reverse_button.configure(state='disabled')
        self.scan_button.configure(state='disabled')
        self.progress_bar.start(10)
        
        def run_reversal():
            try:
                reversal_manager = ReversalManager(base_path, 
                                                 progress_callback=self.progress_callback)
                success = reversal_manager.reverse_optimization()
                
                if success:
                    self.progress_queue.put("=== Reversal Complete ===")
                    # Update reversal button state after successful reversal
                    self.root.after(0, self.update_reversal_button_state)
                else:
                    self.progress_queue.put("=== Reversal Failed ===")
                    
            except Exception as e:
                error_msg = ErrorLogger.handle_exception(e, "Reversal process")
                self.progress_queue.put(f"REVERSAL ERROR: {error_msg}")
            finally:
                # Re-enable buttons
                self.root.after(0, self.enable_buttons)
        
        thread = threading.Thread(target=run_reversal)
        thread.daemon = True
        thread.start()
    
    def enable_buttons(self):
        """Re-enable buttons after processing"""
        self.optimize_button.configure(state='normal')
        self.scan_button.configure(state='normal')
        self.progress_bar.stop()
        self.update_status("Ready")
        self.update_reversal_button_state()


def main():
    root = tk.Tk()
    app = DirectoryOptimizerGUI(root)
    
    # Handle window closing
    def on_closing():
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
