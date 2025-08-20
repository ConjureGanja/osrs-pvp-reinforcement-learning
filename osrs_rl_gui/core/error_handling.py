"""Enhanced error handling and logging for OSRS RL system."""
import logging
import traceback
import sys
from contextlib import contextmanager
from typing import Optional, Type, Callable, Any
from functools import wraps
from pathlib import Path


class OSRSRLError(Exception):
    """Base exception for OSRS RL system errors."""
    pass


class TaskCreationError(OSRSRLError):
    """Raised when task creation fails."""
    pass


class EnvironmentError(OSRSRLError):
    """Raised when environment operations fail."""
    pass


class TrainingError(OSRSRLError):
    """Raised when training operations fail."""
    pass


class ConfigurationError(OSRSRLError):
    """Raised when configuration operations fail."""
    pass


class ConnectionError(OSRSRLError):
    """Raised when server/network connections fail."""
    pass


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console_output: bool = True
) -> logging.Logger:
    """Set up comprehensive logging for the application."""
    
    # Create main logger
    logger = logging.getLogger("osrs_rl")
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def handle_exceptions(
    exception_types: tuple = (Exception,),
    reraise: bool = True,
    default_return: Any = None,
    log_traceback: bool = True
):
    """Decorator for handling exceptions in methods."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                logger = logging.getLogger("osrs_rl.error_handler")
                
                error_msg = f"Error in {func.__name__}: {str(e)}"
                
                if log_traceback:
                    logger.error(f"{error_msg}\n{traceback.format_exc()}")
                else:
                    logger.error(error_msg)
                
                if reraise:
                    raise
                else:
                    return default_return
        return wrapper
    return decorator


@contextmanager
def error_context(operation_name: str, logger_name: str = "osrs_rl"):
    """Context manager for handling errors in operations."""
    logger = logging.getLogger(logger_name)
    try:
        logger.info(f"Starting: {operation_name}")
        yield
        logger.info(f"Completed: {operation_name}")
    except Exception as e:
        logger.error(f"Failed: {operation_name} - {str(e)}")
        logger.debug(f"Traceback for {operation_name}:\n{traceback.format_exc()}")
        raise


class RetryHandler:
    """Handle retrying operations with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Retry an operation with exponential backoff."""
        import time
        
        logger = logging.getLogger("osrs_rl.retry")
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = operation(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Operation succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"Operation failed after {self.max_retries + 1} attempts")
                    break
                
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
        
        raise last_exception


class ErrorReporter:
    """Collect and report errors for debugging."""
    
    def __init__(self, max_errors: int = 100):
        self.max_errors = max_errors
        self.errors = []
        self.error_counts = {}
    
    def report_error(self, error: Exception, context: str = ""):
        """Report an error for tracking."""
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        # Add to error list
        self.errors.append(error_info)
        
        # Maintain max size
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)
        
        # Update counts
        error_key = f"{error_info['type']}:{error_info['context']}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def get_error_summary(self) -> dict:
        """Get summary of reported errors."""
        return {
            'total_errors': len(self.errors),
            'error_counts': self.error_counts,
            'recent_errors': self.errors[-10:] if self.errors else []
        }
    
    def clear_errors(self):
        """Clear all reported errors."""
        self.errors.clear()
        self.error_counts.clear()


# Global error reporter instance
_global_error_reporter = ErrorReporter()

def get_error_reporter() -> ErrorReporter:
    """Get the global error reporter instance."""
    return _global_error_reporter


def safe_operation(operation_name: str):
    """Decorator to safely execute operations with comprehensive error handling."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("osrs_rl.safe_operation")
            error_reporter = get_error_reporter()
            
            try:
                with error_context(operation_name, "osrs_rl.safe_operation"):
                    return func(*args, **kwargs)
            except Exception as e:
                # Report the error
                error_reporter.report_error(e, operation_name)
                
                # Re-raise with additional context
                raise OSRSRLError(f"Safe operation '{operation_name}' failed: {str(e)}") from e
        return wrapper
    return decorator


def validate_input(validator: Callable[[Any], bool], error_message: str):
    """Decorator to validate input parameters."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate all arguments
            all_args = list(args) + list(kwargs.values())
            for arg in all_args:
                if not validator(arg):
                    raise ValueError(f"{error_message}: {arg}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Common validators
def non_empty_string(value: Any) -> bool:
    """Validate that value is a non-empty string."""
    return isinstance(value, str) and len(value.strip()) > 0

def positive_number(value: Any) -> bool:
    """Validate that value is a positive number."""
    return isinstance(value, (int, float)) and value > 0

def valid_port(value: Any) -> bool:
    """Validate that value is a valid port number."""
    return isinstance(value, int) and 1 <= value <= 65535