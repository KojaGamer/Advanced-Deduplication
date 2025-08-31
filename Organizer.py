#!/usr/bin/env python3
"""
Directory Optimizer Core Logic - Phases 1 & 2

Handles directory optimization including:
- Phase 1: Directory name optimization by extracting common prefixes
- Phase 2: File deduplication with Base Files backup
"""

import os
import json
import shutil
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class DirectoryOptimizer:
    def __init__(self, base_path: str, dry_run: bool = False, progress_callback=None):
        self.base_path = Path(base_path)
        self.dry_run = dry_run
        self.state_file = self.base_path / ".optimizer_state.json"
        self.base_files_prefix = "DedupeBase"
        self.optimization_log = []
        self.progress_callback = progress_callback
        
    def log_action(self, action: str, details: Dict):
        """Log all actions for reversibility"""
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "action": action,
            "details": details
        }
        self.optimization_log.append(log_entry)
        
        if self.progress_callback:
            self.progress_callback(f"[{action}] {details}")
    
    def update_progress(self, message: str):
        """Update progress through callback"""
        if self.progress_callback:
            self.progress_callback(message)
    
    def save_state(self):
        """Save optimization state for reversal"""
        state = {
            "timestamp": datetime.datetime.now().isoformat(),
            "base_path": str(self.base_path),
            "log": self.optimization_log
        }
        
        if not self.dry_run:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            self.update_progress(f"State saved to {self.state_file}")
    
    def load_state(self) -> Optional[Dict]:
        """Load previous optimization state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return None
    
    def find_common_prefix(self, names: List[str]) -> str:
        """Find longest common prefix among directory names"""
        if not names:
            return ""
        
        prefix = names[0]
        for name in names[1:]:
            while not name.startswith(prefix) and prefix:
                prefix = prefix[:-1]
        
        if prefix and len(prefix) < min(len(n) for n in names):
            boundaries = ['.', '_', '-', ' ']
            last_boundary = -1
            for i, char in enumerate(prefix):
                if char in boundaries:
                    last_boundary = i + 1
            
            if last_boundary > 0:
                prefix = prefix[:last_boundary]
        
        return prefix if len(prefix) > 1 else ""
    
    def resolve_name_conflicts(self, unique_parts: List[str]) -> List[str]:
        """Resolve naming conflicts in unique parts"""
        resolved = []
        name_counts = defaultdict(int)
        
        for part in unique_parts:
            if part in [item.split('_')[0] for item in resolved]:
                name_counts[part] += 1
                resolved.append(f"{part}_{name_counts[part]}")
            else:
                resolved.append(part)
                name_counts[part] = 0
        
        return resolved
    
    def handle_existing_base_files(self, directory: Path) -> str:
        """Handle existing Base Files folders by renaming them"""
        existing_base_files = []
        for item in directory.iterdir():
            if item.is_dir() and ("base" in item.name.lower() and "files" in item.name.lower()):
                existing_base_files.append(item)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for bf_dir in existing_base_files:
            new_name = f"Original_{bf_dir.name}_{timestamp}"
            new_path = bf_dir.parent / new_name
            
            self.log_action("RENAME_EXISTING_BASE_FILES", {
                "old_path": str(bf_dir),
                "new_path": str(new_path)
            })
            
            if not self.dry_run:
                bf_dir.rename(new_path)
        
        return f"{self.base_files_prefix}_{timestamp}"
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.update_progress(f"Error hashing {file_path}: {e}")
            return ""
    
    def find_duplicate_files(self, directories: List[Path]) -> Dict[str, List[Path]]:
        """Find duplicate files across directories by content hash"""
        file_hashes = defaultdict(list)
        total_files = sum(len(list(directory.rglob("*"))) for directory in directories)
        processed_files = 0
        
        for directory in directories:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    processed_files += 1
                    if processed_files % 10 == 0:  # Update progress every 10 files
                        self.update_progress(f"Scanning files: {processed_files}/{total_files}")
                    
                    file_hash = self.calculate_file_hash(file_path)
                    if file_hash:
                        file_hashes[file_hash].append(file_path)
        
        duplicates = {hash_val: paths for hash_val, paths in file_hashes.items() if len(paths) > 1}
        return duplicates
    
    def phase1_folder_treatment(self, target_dirs: List[Path]) -> Optional[Path]:
        """Phase 1: Optimize directory names by extracting common prefixes"""
        if len(target_dirs) < 2:
            self.update_progress("Need at least 2 directories for optimization")
            return None
        
        dir_names = [d.name for d in target_dirs]
        common_prefix = self.find_common_prefix(dir_names)
        
        if not common_prefix:
            self.update_progress("No common prefix found")
            return None
        
        parent_dir = target_dirs[0].parent / common_prefix.rstrip('.')
        unique_parts = [name[len(common_prefix):] for name in dir_names]
        unique_parts = self.resolve_name_conflicts(unique_parts)
        
        self.log_action("PHASE1_START", {
            "original_dirs": [str(d) for d in target_dirs],
            "common_prefix": common_prefix,
            "parent_dir": str(parent_dir),
            "unique_parts": unique_parts
        })
        
        if not self.dry_run:
            parent_dir.mkdir(exist_ok=True)
            
            for i, (orig_dir, unique_part) in enumerate(zip(target_dirs, unique_parts)):
                new_path = parent_dir / unique_part
                shutil.move(str(orig_dir), str(new_path))
                
                self.log_action("MOVE_DIRECTORY", {
                    "from": str(orig_dir),
                    "to": str(new_path)
                })
        
        return parent_dir
    
    def phase2_file_deduplication(self, parent_dir: Path) -> str:
        """Phase 2: Remove duplicate files with Base Files backup"""
        subdirs = [d for d in parent_dir.iterdir() if d.is_dir()]
        
        base_files_name = self.handle_existing_base_files(parent_dir)
        base_files_dir = parent_dir / base_files_name
        
        self.update_progress("Scanning for duplicate files...")
        duplicates = self.find_duplicate_files(subdirs)
        
        if not duplicates:
            self.update_progress("No duplicate files found")
            return base_files_name
        
        self.log_action("PHASE2_START", {
            "parent_dir": str(parent_dir),
            "base_files_dir": str(base_files_dir),
            "duplicate_count": len(duplicates),
            "total_duplicate_files": sum(len(paths) for paths in duplicates.values())
        })
        
        if not self.dry_run:
            base_files_dir.mkdir(exist_ok=True)
        
        for i, (file_hash, duplicate_paths) in enumerate(duplicates.items()):
            self.update_progress(f"Processing duplicates: {i+1}/{len(duplicates)}")
            
            canonical_file = duplicate_paths[0]
            relative_path = canonical_file.relative_to(parent_dir)
            base_file_path = base_files_dir / relative_path
            
            if not self.dry_run:
                base_file_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(canonical_file, base_file_path)
            
            self.log_action("BACKUP_DUPLICATE", {
                "hash": file_hash,
                "canonical_file": str(canonical_file),
                "backup_location": str(base_file_path),
                "duplicate_locations": [str(p) for p in duplicate_paths]
            })
            
            for dup_file in duplicate_paths:
                if not self.dry_run:
                    dup_file.unlink()
                
                self.log_action("REMOVE_DUPLICATE", {
                    "file": str(dup_file),
                    "hash": file_hash
                })
        
        return base_files_name
    
    def optimize_directories(self, directory_patterns: List[str]) -> None:
        """Main optimization function"""
        self.update_progress(f"Starting optimization in: {self.base_path}")
        self.update_progress(f"Dry run mode: {self.dry_run}")
        
        all_dirs = []
        for pattern in directory_patterns:
            matching_dirs = list(self.base_path.glob(pattern))
            matching_dirs = [d for d in matching_dirs if d.is_dir()]
            all_dirs.extend(matching_dirs)
        
        if not all_dirs:
            self.update_progress("No matching directories found")
            return
        
        self.update_progress(f"Found {len(all_dirs)} directories to process: {[d.name for d in all_dirs]}")
        
        optimization_groups = []
        remaining_dirs = all_dirs.copy()
        
        while len(remaining_dirs) >= 2:
            current_group = [remaining_dirs.pop(0)]
            group_names = [current_group[0].name]
            
            i = 0
            while i < len(remaining_dirs):
                test_names = group_names + [remaining_dirs[i].name]
                if self.find_common_prefix(test_names):
                    current_group.append(remaining_dirs.pop(i))
                    group_names.append(current_group[-1].name)
                else:
                    i += 1
            
            if len(current_group) >= 2:
                optimized_parent = self.phase1_folder_treatment(current_group)
                if optimized_parent:
                    self.phase2_file_deduplication(optimized_parent)
                    optimization_groups.append(optimized_parent)
            else:
                remaining_dirs.append(current_group[0])
                break
        
        self.save_state()
        self.update_progress(f"Optimization complete! Processed {len(optimization_groups)} groups.")