#!/usr/bin/env python3
"""
ErrorLogger Module

Centralized error handling and logging functionality for the Directory Optimizer.
Provides consistent error and logging practices across the application.
"""

import datetime
import logging
import sys
import traceback
from typing import Optional, Callable, Any
from pathlib import Path


class ErrorLogger:
    """
    Centralized error handling and logging system with support for both
    console/file logging and GUI callback updates.
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize the ErrorLogger.
        
        Args:
            log_file: Optional path to log file. If None, only console logging is used.
        """
        self.gui_callback: Optional[Callable[[str], None]] = None
        self.log_file = log_file
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup the logging configuration."""
        # Create logger
        self.logger = logging.getLogger('DirectoryOptimizer')
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if log file is specified
        if self.log_file:
            try:
                file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Could not create log file {self.log_file}: {e}")
    
    def set_gui_callback(self, callback: Callable[[str], None]):
        """
        Set the GUI callback for updating GUI elements with log messages.
        
        Args:
            callback: Function to call with log messages for GUI updates
        """
        self.gui_callback = callback
    
    def clear_gui_callback(self):
        """Clear the GUI callback."""
        self.gui_callback = None
    
    def get_timestamp(self, format_type: str = 'standard') -> str:
        """
        Get formatted timestamp.
        
        Args:
            format_type: Type of timestamp format
                - 'standard': YYYY-MM-DD HH:MM:SS
                - 'time_only': HH:MM:SS  
                - 'iso': ISO format
                - 'filename': Safe for filenames (YYYYMMDD_HHMMSS)
        
        Returns:
            Formatted timestamp string
        """
        now = datetime.datetime.now()
        
        if format_type == 'time_only':
            return now.strftime("%H:%M:%S")
        elif format_type == 'iso':
            return now.isoformat()
        elif format_type == 'filename':
            return now.strftime("%Y%m%d_%H%M%S")
        else:  # standard
            return now.strftime("%Y-%m-%d %H:%M:%S")
    
    def log_message(self, message: str, level: str = 'info', update_gui: bool = True):
        """
        Log a message to both the logging system and optionally the GUI.
        
        Args:
            message: The message to log
            level: Log level ('debug', 'info', 'warning', 'error', 'critical')
            update_gui: Whether to update the GUI via callback
        """
        # Log to the logging system
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(message)
        
        # Update GUI if callback is set and requested
        if update_gui and self.gui_callback:
            timestamp = self.get_timestamp('time_only')
            gui_message = f"[{timestamp}] {message}"
            try:
                self.gui_callback(gui_message)
            except Exception as e:
                # Avoid infinite recursion by not calling log_message here
                self.logger.error(f"Error in GUI callback: {e}")
    
    def handle_exception(self, 
                        exception: Exception, 
                        context: str = "", 
                        show_gui_error: bool = False,
                        gui_error_callback: Optional[Callable[[str, str], None]] = None) -> str:
        """
        Handle an exception by logging it and optionally showing GUI error.
        
        Args:
            exception: The exception that occurred
            context: Additional context about where the exception occurred
            show_gui_error: Whether to show error in GUI
            gui_error_callback: Callback for showing GUI error dialogs (title, message)
        
        Returns:
            String representation of the exception for further handling
        """
        # Format the exception
        exc_type = type(exception).__name__
        exc_message = str(exception)
        exc_traceback = traceback.format_exc()
        
        # Create error message
        if context:
            error_msg = f"{context}: {exc_type}: {exc_message}"
        else:
            error_msg = f"{exc_type}: {exc_message}"
        
        # Log the exception with full traceback
        self.log_message(f"EXCEPTION: {error_msg}", level='error')
        self.logger.error(f"Traceback:\n{exc_traceback}")
        
        # Show GUI error if requested
        if show_gui_error and gui_error_callback:
            try:
                gui_error_callback("Error", error_msg)
            except Exception as gui_e:
                self.logger.error(f"Error showing GUI error dialog: {gui_e}")
        
        return error_msg
    
    def log_action(self, action: str, details: Any):
        """
        Log an action with details (for optimization/reversal tracking).
        
        Args:
            action: The action being performed
            details: Details about the action (will be converted to string)
        """
        message = f"[{action}] {details}"
        self.log_message(message, level='info')
    
    def create_log_entry(self, action: str, details: dict) -> dict:
        """
        Create a structured log entry for JSON logging.
        
        Args:
            action: The action being performed
            details: Dictionary of details about the action
        
        Returns:
            Dictionary with timestamp, action, and details
        """
        return {
            "timestamp": self.get_timestamp('iso'),
            "action": action,
            "details": details
        }


# Global instance for easy access throughout the application
_global_logger: Optional[ErrorLogger] = None

def get_logger() -> ErrorLogger:
    """
    Get the global ErrorLogger instance, creating it if it doesn't exist.
    
    Returns:
        The global ErrorLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = ErrorLogger()
    return _global_logger

def initialize_logger(log_file: Optional[str] = None, gui_callback: Optional[Callable[[str], None]] = None):
    """
    Initialize the global logger with specific settings.
    
    Args:
        log_file: Optional path to log file
        gui_callback: Optional GUI callback for log updates
    """
    global _global_logger
    _global_logger = ErrorLogger(log_file)
    if gui_callback:
        _global_logger.set_gui_callback(gui_callback)

def log_message(message: str, level: str = 'info', update_gui: bool = True):
    """Convenience function to log a message using the global logger."""
    get_logger().log_message(message, level, update_gui)

def handle_exception(exception: Exception, 
                    context: str = "", 
                    show_gui_error: bool = False,
                    gui_error_callback: Optional[Callable[[str, str], None]] = None) -> str:
    """Convenience function to handle an exception using the global logger."""
    return get_logger().handle_exception(exception, context, show_gui_error, gui_error_callback)

def log_action(action: str, details: Any):
    """Convenience function to log an action using the global logger."""
    get_logger().log_action(action, details)

def get_timestamp(format_type: str = 'standard') -> str:
    """Convenience function to get a timestamp using the global logger."""
    return get_logger().get_timestamp(format_type)