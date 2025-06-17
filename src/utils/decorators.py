"""
Decorators für automatisches Logging aller Trades und Signale
Performance-Tracking für Trading-Strategien
Error-Handling für API-Ausfälle
"""

import time
from functools import wraps


def log_performance(func):
    """Decorator für automatisches Logging aller Trades und Signale"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            print(f"✅ {function_name} - {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {function_name} FEHLER nach {execution_time:.2f}s: {str(e)}")
            raise e
    return wrapper


def async_log_performance(func):
    """Async Decorator für Performance-Tracking"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            print(f"✅ {function_name} - {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {function_name} FEHLER nach {execution_time:.2f}s: {str(e)}")
            raise e
    return wrapper