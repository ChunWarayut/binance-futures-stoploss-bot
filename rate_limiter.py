import time
import threading
from typing import Callable, Any
from functools import wraps

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls_per_second: int = 10):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0
        self.lock = threading.Lock()
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to rate limit function calls"""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with self.lock:
                current_time = time.time()
                time_since_last = current_time - self.last_call_time
                
                if time_since_last < self.min_interval:
                    sleep_time = self.min_interval - time_since_last
                    time.sleep(sleep_time)
                
                self.last_call_time = time.time()
                return func(*args, **kwargs)
        
        return wrapper

class RetryHandler:
    """Handle retries for failed API calls"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to handle retries"""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    else:
                        raise last_exception
            
            return None
        
        return wrapper 