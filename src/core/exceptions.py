"""
Universal exceptions for all trading bot modules.

This module defines all exceptions that can be raised across different modules
to ensure consistent error handling throughout the application.
"""


class ModuleError(Exception):
    """Base exception for all trading bot modules."""
    
    def __init__(self, message: str, module: str = None, plugin: str = None):
        super().__init__(message)
        self.message = message
        self.module = module
        self.plugin = plugin
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.module:
            parts.append(f"module={self.module}")
        if self.plugin:
            parts.append(f"plugin={self.plugin}")
        return f"{self.__class__.__name__}: {' | '.join(parts)}"


class PluginNotFoundError(ModuleError):
    """Raised when a requested plugin is not found or not registered."""
    
    def __init__(self, plugin_name: str, module: str = None):
        message = f"Plugin '{plugin_name}' not found"
        if module:
            message += f" in module '{module}'"
        super().__init__(message, module=module, plugin=plugin_name)


class PluginExecutionError(ModuleError):
    """Raised when plugin execution fails."""
    
    def __init__(self, plugin_name: str, original_error: str, module: str = None):
        message = f"Plugin '{plugin_name}' execution failed: {original_error}"
        super().__init__(message, module=module, plugin=plugin_name)
        self.original_error = original_error


class PluginInitializationError(ModuleError):
    """Raised when plugin initialization fails."""
    
    def __init__(self, plugin_name: str, reason: str, module: str = None):
        message = f"Plugin '{plugin_name}' initialization failed: {reason}"
        super().__init__(message, module=module, plugin=plugin_name)
        self.reason = reason


class ConfigurationError(ModuleError):
    """Raised when there's a configuration error."""
    
    def __init__(self, setting: str, value: str, reason: str, module: str = None):
        message = f"Configuration error for '{setting}={value}': {reason}"
        super().__init__(message, module=module)
        self.setting = setting
        self.value = value
        self.reason = reason


class ManagerError(ModuleError):
    """Raised when manager operations fail."""
    
    def __init__(self, operation: str, reason: str, module: str = None):
        message = f"Manager operation '{operation}' failed: {reason}"
        super().__init__(message, module=module)
        self.operation = operation
        self.reason = reason


class FactoryError(ModuleError):
    """Raised when factory operations fail."""
    
    def __init__(self, operation: str, target: str, reason: str, module: str = None):
        message = f"Factory operation '{operation}' for '{target}' failed: {reason}"
        super().__init__(message, module=module)
        self.operation = operation
        self.target = target
        self.reason = reason


class ValidationError(ModuleError):
    """Raised when data validation fails."""
    
    def __init__(self, field: str, value: str, constraint: str, module: str = None):
        message = f"Validation failed for '{field}={value}': {constraint}"
        super().__init__(message, module=module)
        self.field = field
        self.value = value
        self.constraint = constraint


class TimeoutError(ModuleError):
    """Raised when operations exceed timeout limits."""
    
    def __init__(self, operation: str, timeout: float, module: str = None, plugin: str = None):
        message = f"Operation '{operation}' timed out after {timeout}s"
        super().__init__(message, module=module, plugin=plugin)
        self.operation = operation
        self.timeout = timeout


class RetryExhaustedError(ModuleError):
    """Raised when all retry attempts have been exhausted."""
    
    def __init__(self, operation: str, attempts: int, last_error: str, module: str = None, plugin: str = None):
        message = f"Operation '{operation}' failed after {attempts} attempts. Last error: {last_error}"
        super().__init__(message, module=module, plugin=plugin)
        self.operation = operation
        self.attempts = attempts
        self.last_error = last_error
