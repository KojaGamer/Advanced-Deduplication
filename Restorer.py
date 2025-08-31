#!/usr/bin/env python3
"""
Directory Optimizer Reversal Manager

Handles the reversal of directory optimization operations by processing
the optimization log and restoring the original directory structure.
"""

import os
import json
import shutil
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ReversalManager:
    def __init__(self, base_path: str, progress_callback=None):
        self.base_path = Path(base_path)
        self.state_file = self.base_path / ".optimizer_state.json"
        self.progress_callback = progress_callback
        self.reversal_log = []
    
    def update_progress(self, message: str):
        """Update progress through callback"""
        if self.progress_callback:
            self.progress_callback(message)
    
    def log_reversal_action(self, action: str, details: Dict):
        """Log reversal actions"""
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "action": action,
            "details": details
        }
        self.reversal_log.append(log_entry)
        
        if self.progress_callback:
            self.progress_callback(f"[REVERSAL-{action}] {details}")
    
    def load_optimization_state(self) -> Optional[Dict]:
        """Load the optimization state file"""
        if not self.state_file.exists():
            self.update_progress("No optimization state file found")
            return None
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            self.update_progress(f"Loaded state from {state['timestamp']}")
            return state
        except Exception as e:
            self.update_progress(f"Error loading state file: {e}")
            return None
    
    def restore_duplicate_files(self, optimization_log: List[Dict]) -> bool:
        """Restore duplicate files from Base Files backup"""
        self.update_progress("=== Phase 2 Reversal: Restoring duplicate files ===")
        
        base_files_dirs = []
        duplicate_restorations = []
        
        # Find Base Files directories and collect file restoration info
        for log_entry in optimization_log:
            if log_entry["action"] == "PHASE2_START":
                base_files_dir = Path(log_entry["details"]["base_files_dir"])
                if base_files_dir.exists():
                    base_files_dirs.append(base_files_dir)
                    self.update_progress(f"Found Base Files directory: {base_files_dir}")
            
            elif log_entry["action"] == "BACKUP_DUPLICATE":
                duplicate_restorations.append(log_entry["details"])
        
        if not base_files_dirs:
            self.update_progress("No Base Files directories found")
            return True
        
        # Restore duplicate files
        restored_count = 0
        for restoration in duplicate_restorations:
            backup_location = Path(restoration["backup_location"])
            duplicate_locations = restoration["duplicate_locations"]
            
            if backup_location.exists():
                # Restore each duplicate file location
                for dup_location in duplicate_locations:
                    dup_path = Path(dup_location)
                    
                    # Ensure parent directory exists
                    dup_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        shutil.copy2(backup_location, dup_path)
                        restored_count += 1
                        self.log_reversal_action("RESTORE_DUPLICATE_FILE", {
                            "from": str(backup_location),
                            "to": str(dup_path)
                        })
                    except Exception as e:
                        self.update_progress(f"Error restoring {dup_path}: {e}")
            else:
                self.update_progress(f"Backup file not found: {backup_location}")
        
        self.update_progress(f"Restored {restored_count} duplicate files")
        
        # Remove Base Files directories
        for base_files_dir in base_files_dirs:
            try:
                shutil.rmtree(base_files_dir)
                self.log_reversal_action("REMOVE_BASE_FILES_DIR", {
                    "directory": str(base_files_dir)
                })
                self.update_progress(f"Removed Base Files directory: {base_files_dir}")
            except Exception as e:
                self.update_progress(f"Error removing Base Files directory {base_files_dir}: {e}")
        
        return True
    
    def restore_directory_structure(self, optimization_log: List[Dict]) -> bool:
        """Restore original directory structure (Phase 1 reversal)"""
        self.update_progress("=== Phase 1 Reversal: Restoring directory structure ===")
        
        # Find directory moves to reverse (in reverse order)
        directory_moves = []
        phase1_groups = []
        
        for log_entry in optimization_log:
            if log_entry["action"] == "PHASE1_START":
                phase1_groups.append(log_entry["details"])
            elif log_entry["action"] == "MOVE_DIRECTORY":
                directory_moves.append(log_entry["details"])
        
        if not directory_moves:
            self.update_progress("No directory moves found to reverse")
            return True
        
        # Reverse directory moves (last move first)
        directory_moves.reverse()
        moved_count = 0
        
        for move in directory_moves:
            from_path = Path(move["from"])
            to_path = Path(move["to"])
            
            if to_path.exists():
                try:
                    # Ensure the destination parent directory exists
                    from_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.move(str(to_path), str(from_path))
                    moved_count += 1
                    
                    self.log_reversal_action("REVERSE_MOVE_DIRECTORY", {
                        "from": str(to_path),
                        "to": str(from_path)
                    })
                    self.update_progress(f"Restored: {from_path.name}")
                    
                except Exception as e:
                    self.update_progress(f"Error moving {to_path} to {from_path}: {e}")
            else:
                self.update_progress(f"Directory not found: {to_path}")
        
        self.update_progress(f"Restored {moved_count} directories to original locations")
        
        # Remove empty parent directories created during optimization
        for phase1_group in phase1_groups:
            parent_dir = Path(phase1_group["parent_dir"])
            if parent_dir.exists() and not any(parent_dir.iterdir()):
                try:
                    parent_dir.rmdir()
                    self.log_reversal_action("REMOVE_EMPTY_PARENT_DIR", {
                        "directory": str(parent_dir)
                    })
                    self.update_progress(f"Removed empty parent directory: {parent_dir}")
                except Exception as e:
                    self.update_progress(f"Error removing empty directory {parent_dir}: {e}")
        
        return True
    
    def restore_renamed_base_files(self, optimization_log: List[Dict]) -> bool:
        """Restore any renamed existing Base Files directories"""
        self.update_progress("=== Restoring renamed Base Files directories ===")
        
        renamed_dirs = []
        for log_entry in optimization_log:
            if log_entry["action"] == "RENAME_EXISTING_BASE_FILES":
                renamed_dirs.append(log_entry["details"])
        
        if not renamed_dirs:
            self.update_progress("No renamed Base Files directories found")
            return True
        
        restored_count = 0
        for rename in renamed_dirs:
            old_path = Path(rename["old_path"])
            new_path = Path(rename["new_path"])
            
            if new_path.exists():
                try:
                    shutil.move(str(new_path), str(old_path))
                    restored_count += 1
                    
                    self.log_reversal_action("RESTORE_RENAMED_BASE_FILES", {
                        "from": str(new_path),
                        "to": str(old_path)
                    })
                    self.update_progress(f"Restored: {old_path.name}")
                    
                except Exception as e:
                    self.update_progress(f"Error restoring {new_path} to {old_path}: {e}")
            else:
                self.update_progress(f"Renamed directory not found: {new_path}")
        
        self.update_progress(f"Restored {restored_count} renamed Base Files directories")
        return True
    
    def save_reversal_log(self):
        """Save the reversal log"""
        reversal_log_file = self.base_path / f".reversal_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        reversal_state = {
            "timestamp": datetime.datetime.now().isoformat(),
            "base_path": str(self.base_path),
            "reversal_log": self.reversal_log
        }
        
        try:
            with open(reversal_log_file, 'w') as f:
                json.dump(reversal_state, f, indent=2)
            self.update_progress(f"Reversal log saved to {reversal_log_file}")
        except Exception as e:
            self.update_progress(f"Error saving reversal log: {e}")
    
    def cleanup_state_file(self):
        """Remove the optimization state file after successful reversal"""
        try:
            if self.state_file.exists():
                # Create a backup before removing
                backup_name = f".optimizer_state_reversed_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                backup_path = self.base_path / backup_name
                shutil.copy2(self.state_file, backup_path)
                
                self.state_file.unlink()
                self.update_progress(f"State file archived as {backup_name}")
        except Exception as e:
            self.update_progress(f"Error cleaning up state file: {e}")
    
    def reverse_optimization(self) -> bool:
        """Main reversal function - reverses the last optimization"""
        self.update_progress("Starting optimization reversal...")
        
        # Load the optimization state
        state = self.load_optimization_state()
        if not state:
            return False
        
        optimization_log = state.get("log", [])
        if not optimization_log:
            self.update_progress("No optimization log found in state file")
            return False
        
        self.update_progress(f"Processing {len(optimization_log)} log entries...")
        
        try:
            # Step 1: Restore duplicate files (reverse Phase 2)
            if not self.restore_duplicate_files(optimization_log):
                return False
            
            # Step 2: Restore directory structure (reverse Phase 1)
            if not self.restore_directory_structure(optimization_log):
                return False
            
            # Step 3: Restore any renamed Base Files directories
            if not self.restore_renamed_base_files(optimization_log):
                return False
            
            # Step 4: Save reversal log and cleanup
            self.save_reversal_log()
            self.cleanup_state_file()
            
            self.update_progress("=== Optimization reversal completed successfully ===")
            return True
            
        except Exception as e:
            self.update_progress(f"Error during reversal: {e}")
            return False
    
    def can_reverse(self) -> Tuple[bool, str]:
        """Check if reversal is possible and return status message"""
        if not self.state_file.exists():
            return False, "No optimization state file found"
        
        try:
            state = self.load_optimization_state()
            if not state:
                return False, "Could not load optimization state"
            
            if not state.get("log"):
                return False, "No optimization log found in state file"
            
            # Check if required directories/files still exist
            base_files_found = False
            for log_entry in state["log"]:
                if log_entry["action"] == "PHASE2_START":
                    base_files_dir = Path(log_entry["details"]["base_files_dir"])
                    if base_files_dir.exists():
                        base_files_found = True
                        break
            
            optimization_date = state.get("timestamp", "Unknown")
            return True, f"Can reverse optimization from {optimization_date}"
            
        except Exception as e:
            return False, f"Error checking reversal status: {e}"
