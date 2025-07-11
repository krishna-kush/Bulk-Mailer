import logging
import configparser
import os
import shutil
import sys
from datetime import datetime

# Get the base directory (project root - parent of modules directory)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AppLogger:
    def __init__(self, base_dir, config_path="config.ini"):
        self.base_dir = base_dir
        self.config_path = os.path.join(self.base_dir, config_path)
        self.config = self._get_config()
        self.logger = self._setup_logging()

    def _get_config(self):
        config = configparser.ConfigParser()
        config.read(self.config_path)
        return config

    def _get_log_dir(self):
        """Get the dynamic log directory path from config."""
        try:
            log_dir = self.config["LOGGING"]["log_dir"]
            # If it's a relative path, make it relative to BASE_DIR
            if not os.path.isabs(log_dir):
                log_dir = os.path.join(self.base_dir, log_dir)
            return log_dir
        except KeyError:
            # Fallback to default
            return os.path.join(self.base_dir, "logs")

    def _setup_logging(self):
        """Sets up multi-level logging configuration with separate files per log level in timestamped folders."""
        log_dir = self._get_log_dir()
        
        # Create main logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Generate timestamped run folder with cleaner naming: YYYY-MM-DD_HHMMSS
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        run_folder = os.path.join(log_dir, timestamp)
        os.makedirs(run_folder, exist_ok=True)
        
        # Get logging configuration
        console_level = self.config.get("LOGGING", "console_level", fallback="INFO").upper()
        file_levels = [level.strip().upper() for level in self.config.get("LOGGING", "file_levels", fallback="DEBUG,INFO,WARNING,ERROR,CRITICAL").split(",")]
        max_log_files = int(self.config.get("LOGGING", "max_log_files_to_keep", fallback="10"))
        
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Set up file handlers for each log level
        file_handlers = []
        log_files = {}
        
        for level in file_levels:
            if level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                log_file = os.path.join(run_folder, f"{level.lower()}.log")
                log_files[level] = log_file
                
                # Create file handler
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(getattr(logging, level))
                file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s"))
                
                # Add filter to only show this level
                file_handler.addFilter(lambda record, lvl=level: record.levelname == lvl)
                file_handlers.append(file_handler)
        
        # Create console handler with configured level
        console_handler = logging.StreamHandler()
        try:
            console_handler.setLevel(getattr(logging, console_level))
        except AttributeError:
            console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s"))
        
        # Create "all" log file that contains everything
        all_log_file = os.path.join(run_folder, "all.log")
        log_files["ALL"] = all_log_file
        all_handler = logging.FileHandler(all_log_file)
        all_handler.setLevel(logging.DEBUG)
        all_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s"))
        
        # Configure root logger
        root_logger.setLevel(logging.DEBUG)
        for handler in file_handlers:
            root_logger.addHandler(handler)
        root_logger.addHandler(all_handler)
        root_logger.addHandler(console_handler)
        
        logger = logging.getLogger(__name__)
        
        # Write CLI command and configuration to all log files
        cli_command = " ".join(sys.argv)
        config_info = f"Console Level: {console_level}, File Levels: {file_levels}"
        header = f"CLI Command: {cli_command}\nLogging Config: {config_info}\n{'=' * 80}\n\n"
        
        for log_file in log_files.values():
            with open(log_file, "w") as f:
                f.write(header)
        
        logger.info(f"Multi-level logging initialized in: {run_folder}")
        logger.info(f"CLI Command: {cli_command}")
        logger.info(f"Console showing: {console_level} level logs")
        logger.info(f"File levels: {', '.join(file_levels)}")
        
        # Clean up old log folders
        self._cleanup_old_logs(log_dir, max_log_files)        
        return logger

    def _cleanup_old_logs(self, log_dir, max_files_to_keep):
        """Clean up old log folders, keeping only the most recent ones."""
        try:
            if not os.path.exists(log_dir):
                return
            
            # Get all timestamped folders (YYYY-MM-DD_HHMMSS format)
            log_folders = []
            for item in os.listdir(log_dir):
                item_path = os.path.join(log_dir, item)
                if os.path.isdir(item_path) and self._is_valid_log_folder(item):
                    log_folders.append((item_path, os.path.getctime(item_path)))
            
            # Sort by creation time (newest first)
            log_folders.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old folders if we exceed the limit
            if len(log_folders) > max_files_to_keep:
                folders_to_remove = log_folders[max_log_files_to_keep:]
                for folder_path, _ in folders_to_remove:
                    try:
                        shutil.rmtree(folder_path)
                        logging.debug(f"Removed old log folder: {folder_path}")
                    except Exception as e:
                        logging.warning(f"Could not remove old log folder {folder_path}: {e}")
        
        except Exception as e:
            logging.warning(f"Error during log cleanup: {e}")

    def _is_valid_log_folder(self, folder_name):
        """Check if folder name matches the expected timestamped format: YYYY-MM-DD_HHMMSS."""
        try:
            # Try to parse the folder name as a timestamp
            datetime.strptime(folder_name, "%Y-%m-%d_%H%M%S")
            return True
        except ValueError:
            return False

    def get_logger(self):
        return self.logger

# Example usage (for testing or direct import):
# if __name__ == "__main__":
#     # Assuming config.ini is in the same directory as logger.py for this example
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     app_logger = AppLogger(current_dir)
#     logger = app_logger.get_logger()
#     logger.info("This is an info message from the main script.")
#     logger.debug("This is a debug message.")
#     logger.warning("This is a warning message.")
#     logger.error("This is an error message.")
#     logger.critical("This is a critical message.")


