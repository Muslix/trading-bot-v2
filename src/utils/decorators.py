"""
Decorators für automatisches Logging aller Trades und Signale
Performance-Tracking für Trading-Strategien
Error-Handling für API-Ausfälle
"""

import time
from functools import wraps
from typing import Any, Callable

try:
    from src.utils.error_logger import log_performance as log_perf_structured, log_error
except ImportError:
    # Fallback if error_logger not available
    def log_perf_structured(operation: str, duration: float, context: dict = None):
        print(f"Performance: {operation} - {duration:.3f}s")
    
    def log_error(message: str, exception: Exception = None, context: dict = None):
        print(f"Error: {message}")


def log_performance(func: Callable) -> Callable:
    """Decorator für automatisches Logging aller Trades und Signale mit strukturiertem Logging"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        function_name = func.__name__
        module_name = func.__module__

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Structured performance logging
            context = {
                "module": module_name,
                "function": function_name,
                "args_count": len(args),
                "kwargs_count": len(kwargs),
                "success": True
            }
            log_perf_structured(f"{module_name}.{function_name}", execution_time, context=context)
            
            # Console output for immediate feedback
            print(f"✅ {function_name} - {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Structured error logging
            context = {
                "module": module_name,
                "function": function_name,
                "execution_time": execution_time,
                "args_count": len(args),
                "kwargs_count": len(kwargs)
            }
            log_error(f"Function {function_name} failed after {execution_time:.3f}s", exception=e, context=context)
            
            # Console output for immediate feedback
            print(f"❌ {function_name} FEHLER nach {execution_time:.2f}s: {str(e)}")
            raise e

    return wrapper


def async_log_performance(func: Callable) -> Callable:
    """Async Decorator für Performance-Tracking mit strukturiertem Logging"""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        function_name = func.__name__
        module_name = func.__module__

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Structured performance logging
            context = {
                "module": module_name,
                "function": function_name,
                "args_count": len(args),
                "kwargs_count": len(kwargs),
                "success": True,
                "async": True
            }
            log_perf_structured(f"{module_name}.{function_name}", execution_time, context=context)
            
            # Console output for immediate feedback
            print(f"✅ {function_name} - {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Structured error logging
            context = {
                "module": module_name,
                "function": function_name,
                "execution_time": execution_time,
                "args_count": len(args),
                "kwargs_count": len(kwargs),
                "async": True
            }
            log_error(f"Async function {function_name} failed after {execution_time:.3f}s", exception=e, context=context)
            
            # Console output for immediate feedback
            print(f"❌ {function_name} FEHLER nach {execution_time:.2f}s: {str(e)}")
            raise e

    return wrapper


def track_api_call(api_name: str):
    """Decorator for tracking API calls with detailed metrics"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Detailed API call logging
                context = {
                    "api_name": api_name,
                    "function": func.__name__,
                    "module": func.__module__,
                    "success": True,
                    "response_size": len(str(result)) if result else 0
                }
                log_perf_structured(f"API_CALL_{api_name}", execution_time, context=context)
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                context = {
                    "api_name": api_name,
                    "function": func.__name__,
                    "module": func.__module__,
                    "execution_time": execution_time,
                    "error_type": type(e).__name__
                }
                log_error(f"API call to {api_name} failed", exception=e, context=context)
                raise e
                
        return wrapper
    return decorator
