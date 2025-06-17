"""
Unit tests for error logging functionality
Testing structured logging and error handling
"""

import json
import logging
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project root to path
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.error_logger import (
    ErrorLogger, StructuredFormatter, setup_error_logger,
    log_error, log_warning, log_info, log_critical, log_performance
)


class TestStructuredFormatter(unittest.TestCase):
    """Test cases for StructuredFormatter"""
    
    def setUp(self):
        """Set up test environment"""
        self.formatter = StructuredFormatter()
    
    def test_basic_format(self):
        """Test basic log record formatting"""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=42,
            msg="Test error message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        
        formatted = self.formatter.format(record)
        
        # Should be valid JSON
        log_data = json.loads(formatted)
        
        # Check required fields
        self.assertIn("timestamp", log_data)
        self.assertIn("level", log_data)
        self.assertIn("module", log_data)
        self.assertIn("function", log_data)
        self.assertIn("line", log_data)
        self.assertIn("message", log_data)
        
        # Check values
        self.assertEqual(log_data["level"], "ERROR")
        self.assertEqual(log_data["module"], "test_module")
        self.assertEqual(log_data["function"], "test_function")
        self.assertEqual(log_data["line"], 42)
        self.assertEqual(log_data["message"], "Test error message")
    
    def test_format_with_exception(self):
        """Test formatting with exception info"""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="/test/path.py",
                lineno=42,
                msg="Error with exception",
                args=(),
                exc_info=(type(e), e, e.__traceback__)
            )
            record.module = "test_module"
            record.funcName = "test_function"
            
            formatted = self.formatter.format(record)
            log_data = json.loads(formatted)
            
            # Should have exception info
            self.assertIn("exception", log_data)
            self.assertEqual(log_data["exception"]["type"], "ValueError")
            self.assertEqual(log_data["exception"]["message"], "Test exception")
            self.assertIn("traceback", log_data["exception"])
    
    def test_format_with_context(self):
        """Test formatting with context"""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message with context",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.context = {"user_id": 123, "operation": "test_op"}
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        # Should have context
        self.assertIn("context", log_data)
        self.assertEqual(log_data["context"]["user_id"], 123)
        self.assertEqual(log_data["context"]["operation"], "test_op")
    
    def test_timestamp_format(self):
        """Test timestamp format is ISO format"""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        # Should be parseable as datetime
        try:
            datetime.fromisoformat(log_data["timestamp"])
        except ValueError:
            self.fail("Timestamp is not in valid ISO format")


class TestErrorLogger(unittest.TestCase):
    """Test cases for ErrorLogger class"""
    
    def setUp(self):
        """Set up test environment"""
        self.error_logger = ErrorLogger()
    
    def test_init(self):
        """Test ErrorLogger initialization"""
        self.assertIsInstance(self.error_logger.logger, logging.Logger)
        self.assertEqual(self.error_logger.logger.name, "crypto_bot_errors")
    
    @patch('src.utils.error_logger.setup_error_logger')
    def test_log_error_without_exception(self, mock_setup):
        """Test log_error without exception"""
        mock_logger = MagicMock()
        mock_setup.return_value = mock_logger
        
        error_logger = ErrorLogger()
        error_logger.log_error("Test error message")
        
        mock_logger.error.assert_called_once_with("Test error message", extra={})
    
    @patch('src.utils.error_logger.setup_error_logger')
    def test_log_error_with_exception(self, mock_setup):
        """Test log_error with exception"""
        mock_logger = MagicMock()
        mock_setup.return_value = mock_logger
        
        error_logger = ErrorLogger()
        test_exception = ValueError("Test exception")
        error_logger.log_error("Test error", exception=test_exception)
        
        mock_logger.error.assert_called_once_with(
            "Test error", 
            exc_info=test_exception, 
            extra={}
        )
    
    @patch('src.utils.error_logger.setup_error_logger')
    def test_log_error_with_context(self, mock_setup):
        """Test log_error with context"""
        mock_logger = MagicMock()
        mock_setup.return_value = mock_logger
        
        error_logger = ErrorLogger()
        context = {"operation": "test", "user_id": 123}
        error_logger.log_error("Test error", context=context)
        
        mock_logger.error.assert_called_once_with(
            "Test error", 
            extra={"context": context}
        )
    
    @patch('src.utils.error_logger.setup_error_logger')
    def test_log_warning(self, mock_setup):
        """Test log_warning method"""
        mock_logger = MagicMock()
        mock_setup.return_value = mock_logger
        
        error_logger = ErrorLogger()
        context = {"operation": "test_warning"}
        error_logger.log_warning("Test warning", context=context)
        
        mock_logger.warning.assert_called_once_with(
            "Test warning", 
            extra={"context": context}
        )
    
    @patch('src.utils.error_logger.setup_error_logger')
    def test_log_info(self, mock_setup):
        """Test log_info method"""
        mock_logger = MagicMock()
        mock_setup.return_value = mock_logger
        
        error_logger = ErrorLogger()
        error_logger.log_info("Test info message")
        
        mock_logger.info.assert_called_once_with("Test info message", extra={})
    
    @patch('src.utils.error_logger.setup_error_logger')
    def test_log_critical(self, mock_setup):
        """Test log_critical method"""
        mock_logger = MagicMock()
        mock_setup.return_value = mock_logger
        
        error_logger = ErrorLogger()
        test_exception = RuntimeError("Critical error")
        context = {"severity": "high"}
        
        error_logger.log_critical("Critical system error", exception=test_exception, context=context)
        
        mock_logger.critical.assert_called_once_with(
            "Critical system error", 
            exc_info=test_exception, 
            extra={"context": context}
        )
    
    @patch('src.utils.error_logger.setup_error_logger')
    def test_log_performance(self, mock_setup):
        """Test log_performance method"""
        mock_logger = MagicMock()
        mock_setup.return_value = mock_logger
        
        error_logger = ErrorLogger()
        error_logger.log_performance("database_query", 0.125, {"query": "SELECT * FROM users"})
        
        expected_context = {
            "operation": "database_query",
            "duration_ms": 125.0,
            "query": "SELECT * FROM users"
        }
        
        mock_logger.info.assert_called_once_with(
            "Performance: database_query completed in 0.125s",
            extra={"context": expected_context}
        )


class TestSetupErrorLogger(unittest.TestCase):
    """Test cases for setup_error_logger function"""
    
    def test_setup_logger_basic(self):
        """Test basic logger setup"""
        logger = setup_error_logger()
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "crypto_bot_errors")
        self.assertEqual(logger.level, logging.INFO)
    
    def test_setup_logger_custom_level(self):
        """Test logger setup with custom level"""
        logger = setup_error_logger("DEBUG")
        
        self.assertEqual(logger.level, logging.DEBUG)
    
    def test_setup_logger_prevents_duplicate_handlers(self):
        """Test that setup prevents duplicate handlers"""
        # Setup logger twice
        logger1 = setup_error_logger()
        initial_handler_count = len(logger1.handlers)
        
        logger2 = setup_error_logger()
        final_handler_count = len(logger2.handlers)
        
        # Should be the same logger instance with same handlers
        self.assertEqual(initial_handler_count, final_handler_count)
        self.assertIs(logger1, logger2)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""
    
    @patch('src.utils.error_logger.error_logger')
    def test_log_error_function(self, mock_error_logger):
        """Test log_error convenience function"""
        log_error("Test error", context={"test": True})
        
        mock_error_logger.log_error.assert_called_once_with(
            "Test error", None, {"test": True}
        )
    
    @patch('src.utils.error_logger.error_logger')
    def test_log_warning_function(self, mock_error_logger):
        """Test log_warning convenience function"""
        log_warning("Test warning", context={"test": True})
        
        mock_error_logger.log_warning.assert_called_once_with(
            "Test warning", {"test": True}
        )
    
    @patch('src.utils.error_logger.error_logger')
    def test_log_info_function(self, mock_error_logger):
        """Test log_info convenience function"""
        log_info("Test info")
        
        mock_error_logger.log_info.assert_called_once_with("Test info", None)
    
    @patch('src.utils.error_logger.error_logger')
    def test_log_critical_function(self, mock_error_logger):
        """Test log_critical convenience function"""
        test_exception = Exception("Critical")
        log_critical("Critical error", exception=test_exception)
        
        mock_error_logger.log_critical.assert_called_once_with(
            "Critical error", test_exception, None
        )
    
    @patch('src.utils.error_logger.error_logger')
    def test_log_performance_function(self, mock_error_logger):
        """Test log_performance convenience function"""
        log_performance("test_operation", 0.5, {"test": True})
        
        mock_error_logger.log_performance.assert_called_once_with(
            "test_operation", 0.5, {"test": True}
        )


class TestErrorLoggingIntegration(unittest.TestCase):
    """Integration tests for error logging"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test_error.log")
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        os.rmdir(self.temp_dir)
    
    def test_end_to_end_logging(self):
        """Test end-to-end logging functionality"""
        # Create logger with custom file handler
        logger = logging.getLogger("test_crypto_bot_errors")
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Add file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
        
        # Create error logger with custom logger
        error_logger = ErrorLogger()
        error_logger.logger = logger
        
        # Log an error
        try:
            raise ValueError("Test integration error")
        except ValueError as e:
            error_logger.log_error("Integration test error", exception=e, 
                                 context={"test_case": "integration"})
        
        # Check that log was written
        self.assertTrue(os.path.exists(self.log_file))
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should be valid JSON
        log_data = json.loads(log_content)
        
        # Verify log structure
        self.assertEqual(log_data["level"], "ERROR")
        self.assertEqual(log_data["message"], "Integration test error")
        self.assertIn("exception", log_data)
        self.assertEqual(log_data["exception"]["type"], "ValueError")
        self.assertIn("context", log_data)
        self.assertEqual(log_data["context"]["test_case"], "integration")


if __name__ == "__main__":
    unittest.main(verbosity=2)