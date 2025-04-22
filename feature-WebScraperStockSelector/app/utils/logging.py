import logging
import logging.handlers
import os
from datetime import datetime
from collections import deque

class ScraperLogger:
    def __init__(self, max_logs=1000):
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)
        self.setup_logger()

    def setup_logger(self):
        """Setup the logger with file and console handlers."""
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Create logger
        self.logger = logging.getLogger('scraper')
        self.logger.setLevel(logging.INFO)

        # Create file handler
        log_file = f'logs/scraper_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log(self, level, message):
        """Log a message and store it in memory."""
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        
        # Log using the appropriate level
        if level == 'INFO':
            self.logger.info(message)
        elif level == 'WARNING':
            self.logger.warning(message)
        elif level == 'ERROR':
            self.logger.error(message)
        elif level == 'DEBUG':
            self.logger.debug(message)

    def info(self, message):
        """Log an info message."""
        self.log('INFO', message)

    def warning(self, message):
        """Log a warning message."""
        self.log('WARNING', message)

    def error(self, message):
        """Log an error message."""
        self.log('ERROR', message)

    def debug(self, message):
        """Log a debug message."""
        self.log('DEBUG', message)

    def get_recent_logs(self, limit=20):
        """Get recent logs up to the specified limit."""
        return [f"{log['timestamp']} - {log['level']} - {log['message']}" 
                for log in list(self.logs)[-limit:]]

def setup_logger(name=__name__):
    """
    Set up logging configuration with both file and console handlers.
    
    File logs: Technical and operational issues
    Console logs: Immediate feedback during development
    Database logs: Handled separately for business metrics
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    # File handler with rotation
    log_file = f"logs/scraper_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s - %(message)s'
    ))

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_logger(name=__name__):
    """Get an existing logger or create a new one."""
    return logging.getLogger(name) 