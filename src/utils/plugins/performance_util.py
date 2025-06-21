"""
Performance Utility Plugin - decorators and performance monitoring
"""

import time
from functools import wraps
from typing import Dict, Any, Callable
from datetime import datetime

from ..base import UtilPlugin, UtilConfig


class PerformanceUtil(UtilPlugin):
    """
    Performance utility plugin for decorators and monitoring.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.performance_history = {}
        self.call_counts = {}
    
    async def _initialize_util(self) -> bool:
        """Initialize performance utility."""
        self.logger.info("Performance utility initialized")
        return True
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process performance-related operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "log_performance")
        
        if action == "log_performance":
            return await self._log_performance(data)
        elif action == "create_decorator":
            return self._create_performance_decorator(data)
        elif action == "get_stats":
            return self._get_performance_stats()
        elif action == "clear_history":
            return self._clear_performance_history()
        else:
            raise ValueError(f"Unknown performance action: {action}")
    
    async def _log_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log performance data."""
        func_name = data.get("func_name", "unknown")
        duration = data.get("duration", 0)
        module_name = data.get("module", "unknown")
        context = data.get("context", {})
        
        # Store performance data
        key = f"{module_name}.{func_name}"
        if key not in self.performance_history:
            self.performance_history[key] = []
            self.call_counts[key] = 0
        
        self.performance_history[key].append({
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "context": context
        })
        self.call_counts[key] += 1
        
        # Keep only last 100 entries per function
        if len(self.performance_history[key]) > 100:
            self.performance_history[key] = self.performance_history[key][-100:]
        
        # Log to structured logger if available
        try:
            from ..error_logger import log_performance as log_perf_structured
            log_perf_structured(key, duration, context)
        except ImportError:
            self.logger.info(f"Performance: {key} - {duration:.3f}s")
        
        return {
            "logged": True,
            "function": key,
            "duration": duration,
            "total_calls": self.call_counts[key]
        }
    
    def _create_performance_decorator(self, data: Dict[str, Any]) -> Callable:
        """Create a performance logging decorator."""
        async_mode = data.get("async", False)
        
        if async_mode:
            return self._async_log_performance_decorator()
        else:
            return self._sync_log_performance_decorator()
    
    def _sync_log_performance_decorator(self) -> Callable:
        """Create sync performance decorator."""
        
        def log_performance(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                function_name = func.__name__
                module_name = func.__module__

                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Log performance
                    context = {
                        "module": module_name,
                        "function": function_name,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                        "success": True
                    }
                    
                    # Use the utility to log performance
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        loop.create_task(self._log_performance({
                            "func_name": function_name,
                            "duration": execution_time,
                            "module": module_name,
                            "context": context
                        }))
                    except RuntimeError:
                        # Fallback if no event loop
                        self.logger.info(f"✅ {function_name} - {execution_time:.2f}s")
                    
                    print(f"✅ {function_name} - {execution_time:.2f}s")
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    
                    context = {
                        "module": module_name,
                        "function": function_name,
                        "execution_time": execution_time,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs)
                    }
                    
                    try:
                        from ..error_logger import log_error
                        log_error(f"Function {function_name} failed after {execution_time:.3f}s", exception=e, context=context)
                    except ImportError:
                        self.logger.error(f"Function {function_name} failed: {e}")
                    
                    print(f"❌ {function_name} FEHLER nach {execution_time:.2f}s: {str(e)}")
                    raise e

            return wrapper
        
        return log_performance
    
    def _async_log_performance_decorator(self) -> Callable:
        """Create async performance decorator."""
        
        def async_log_performance(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                function_name = func.__name__
                module_name = func.__module__

                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    context = {
                        "module": module_name,
                        "function": function_name,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                        "success": True,
                        "async": True
                    }
                    
                    await self._log_performance({
                        "func_name": function_name,
                        "duration": execution_time,
                        "module": module_name,
                        "context": context
                    })
                    
                    print(f"✅ {function_name} - {execution_time:.2f}s")
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    
                    context = {
                        "module": module_name,
                        "function": function_name,
                        "execution_time": execution_time,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                        "async": True
                    }
                    
                    try:
                        from ..error_logger import log_error
                        log_error(f"Async function {function_name} failed after {execution_time:.3f}s", exception=e, context=context)
                    except ImportError:
                        self.logger.error(f"Async function {function_name} failed: {e}")
                    
                    print(f"❌ {function_name} FEHLER nach {execution_time:.2f}s: {str(e)}")
                    raise e

            return wrapper
        
        return async_log_performance
    
    def _get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {}
        
        for func_key, history in self.performance_history.items():
            if history:
                durations = [entry["duration"] for entry in history]
                stats[func_key] = {
                    "total_calls": self.call_counts.get(func_key, 0),
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "last_call": history[-1]["timestamp"],
                    "recent_calls": len(history)
                }
        
        return {
            "function_stats": stats,
            "total_functions_tracked": len(stats),
            "total_calls_tracked": sum(self.call_counts.values())
        }
    
    def _clear_performance_history(self) -> Dict[str, Any]:
        """Clear performance history."""
        functions_cleared = len(self.performance_history)
        calls_cleared = sum(self.call_counts.values())
        
        self.performance_history.clear()
        self.call_counts.clear()
        
        return {
            "cleared": True,
            "functions_cleared": functions_cleared,
            "calls_cleared": calls_cleared
        }
    
    def create_api_tracker(self, api_name: str) -> Callable:
        """Create an API call tracking decorator."""
        
        def track_api_call(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    context = {
                        "api_name": api_name,
                        "function": func.__name__,
                        "module": func.__module__,
                        "success": True,
                        "response_size": len(str(result)) if result else 0
                    }
                    
                    # Log performance
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        loop.create_task(self._log_performance({
                            "func_name": f"API_{api_name}",
                            "duration": execution_time,
                            "module": func.__module__,
                            "context": context
                        }))
                    except RuntimeError:
                        self.logger.info(f"API {api_name} - {execution_time:.3f}s")
                    
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
                    
                    try:
                        from ..error_logger import log_error
                        log_error(f"API call to {api_name} failed", exception=e, context=context)
                    except ImportError:
                        self.logger.error(f"API call to {api_name} failed: {e}")
                    
                    raise e
                    
            return wrapper
        
        return track_api_call