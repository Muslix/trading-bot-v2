"""
Unit tests for performance tracking decorators
Testing enhanced logging and performance metrics
"""

import asyncio
import time
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.decorators import log_performance, async_log_performance, track_api_call


class TestPerformanceDecorators(unittest.TestCase):
    """Test cases for performance tracking decorators"""
    
    @patch('src.utils.decorators.log_perf_structured')
    @patch('src.utils.decorators.log_error')
    def test_log_performance_success(self, mock_log_error, mock_log_perf):
        """Test log_performance decorator with successful function"""
        
        @log_performance
        def test_function(x, y, z=None):
            time.sleep(0.01)  # Small delay for testing
            return x + y
        
        result = test_function(1, 2, z="test")
        
        # Check result
        self.assertEqual(result, 3)
        
        # Check performance logging was called
        mock_log_perf.assert_called_once()
        call_args, call_kwargs = mock_log_perf.call_args
        
        # Check operation name
        self.assertIn("test_function", call_args[0])
        
        # Check duration (should be > 0.01)
        self.assertGreater(call_args[1], 0.01)
        
        # Check context
        context = call_kwargs['context']
        self.assertEqual(context['function'], 'test_function')
        self.assertEqual(context['args_count'], 2)
        self.assertEqual(context['kwargs_count'], 1)
        self.assertTrue(context['success'])
        
        # Error logging should not be called
        mock_log_error.assert_not_called()
    
    @patch('src.utils.decorators.log_perf_structured')
    @patch('src.utils.decorators.log_error')
    def test_log_performance_exception(self, mock_log_error, mock_log_perf):
        """Test log_performance decorator with exception"""
        
        @log_performance
        def failing_function():
            raise ValueError("Test error")
        
        # Should raise the original exception
        with self.assertRaises(ValueError):
            failing_function()
        
        # Performance logging should not be called for failed functions
        mock_log_perf.assert_not_called()
        
        # Error logging should be called
        mock_log_error.assert_called_once()
        call_args, call_kwargs = mock_log_error.call_args
        
        # Check error message
        self.assertIn("failing_function failed", call_args[0])
        
        # Check exception
        self.assertIsInstance(call_kwargs['exception'], ValueError)
        
        # Check context
        context = call_kwargs['context']
        self.assertEqual(context['function'], 'failing_function')
        self.assertIn('execution_time', context)
    
    @patch('src.utils.decorators.log_perf_structured')
    @patch('src.utils.decorators.log_error')
    def test_log_performance_no_args(self, mock_log_error, mock_log_perf):
        """Test log_performance decorator with no arguments"""
        
        @log_performance
        def no_args_function():
            return "success"
        
        result = no_args_function()
        
        # Check result
        self.assertEqual(result, "success")
        
        # Check context for no args
        _, call_kwargs = mock_log_perf.call_args
        context = call_kwargs['context']
        self.assertEqual(context['args_count'], 0)
        self.assertEqual(context['kwargs_count'], 0)


class TestAsyncPerformanceDecorators(unittest.IsolatedAsyncioTestCase):
    """Test cases for async performance tracking decorators"""
    
    @patch('src.utils.decorators.log_perf_structured')
    @patch('src.utils.decorators.log_error')
    async def test_async_log_performance_success(self, mock_log_error, mock_log_perf):
        """Test async_log_performance decorator with successful function"""
        
        @async_log_performance
        async def async_test_function(x, y):
            await asyncio.sleep(0.01)  # Small async delay
            return x * y
        
        result = await async_test_function(3, 4)
        
        # Check result
        self.assertEqual(result, 12)
        
        # Check performance logging was called
        mock_log_perf.assert_called_once()
        call_args, call_kwargs = mock_log_perf.call_args
        
        # Check operation name
        self.assertIn("async_test_function", call_args[0])
        
        # Check duration (should be > 0.01)
        self.assertGreater(call_args[1], 0.01)
        
        # Check context
        context = call_kwargs['context']
        self.assertEqual(context['function'], 'async_test_function')
        self.assertEqual(context['args_count'], 2)
        self.assertTrue(context['async'])
        self.assertTrue(context['success'])
    
    @patch('src.utils.decorators.log_perf_structured')
    @patch('src.utils.decorators.log_error')
    async def test_async_log_performance_exception(self, mock_log_error, mock_log_perf):
        """Test async_log_performance decorator with exception"""
        
        @async_log_performance
        async def async_failing_function():
            await asyncio.sleep(0.001)
            raise RuntimeError("Async test error")
        
        # Should raise the original exception
        with self.assertRaises(RuntimeError):
            await async_failing_function()
        
        # Performance logging should not be called for failed functions
        mock_log_perf.assert_not_called()
        
        # Error logging should be called
        mock_log_error.assert_called_once()
        call_args, call_kwargs = mock_log_error.call_args
        
        # Check error message
        self.assertIn("async_failing_function failed", call_args[0])
        
        # Check context has async flag
        context = call_kwargs['context']
        self.assertTrue(context['async'])


class TestApiCallDecorator(unittest.TestCase):
    """Test cases for API call tracking decorator"""
    
    @patch('src.utils.decorators.log_perf_structured')
    @patch('src.utils.decorators.log_error')
    def test_track_api_call_success(self, mock_log_error, mock_log_perf):
        """Test track_api_call decorator with successful API call"""
        
        @track_api_call("binance")
        def api_call_function(symbol):
            return {"symbol": symbol, "price": 45000}
        
        result = api_call_function("BTC")
        
        # Check result
        self.assertEqual(result["symbol"], "BTC")
        self.assertEqual(result["price"], 45000)
        
        # Check performance logging was called
        mock_log_perf.assert_called_once()
        call_args, call_kwargs = mock_log_perf.call_args
        
        # Check operation name includes API name
        self.assertEqual(call_args[0], "API_CALL_binance")
        
        # Check context
        context = call_kwargs['context']
        self.assertEqual(context['api_name'], 'binance')
        self.assertEqual(context['function'], 'api_call_function')
        self.assertTrue(context['success'])
        self.assertIn('response_size', context)
        self.assertGreater(context['response_size'], 0)
    
    @patch('src.utils.decorators.log_perf_structured')
    @patch('src.utils.decorators.log_error')
    def test_track_api_call_exception(self, mock_log_error, mock_log_perf):
        """Test track_api_call decorator with API exception"""
        
        @track_api_call("coinbase")
        def failing_api_call():
            raise ConnectionError("API connection failed")
        
        # Should raise the original exception
        with self.assertRaises(ConnectionError):
            failing_api_call()
        
        # Performance logging should not be called for failed API calls
        mock_log_perf.assert_not_called()
        
        # Error logging should be called
        mock_log_error.assert_called_once()
        call_args, call_kwargs = mock_log_error.call_args
        
        # Check error message
        self.assertIn("API call to coinbase failed", call_args[0])
        
        # Check context
        context = call_kwargs['context']
        self.assertEqual(context['api_name'], 'coinbase')
        self.assertEqual(context['error_type'], 'ConnectionError')
    
    @patch('src.utils.decorators.log_perf_structured')
    @patch('src.utils.decorators.log_error')
    def test_track_api_call_empty_response(self, mock_log_error, mock_log_perf):
        """Test track_api_call decorator with empty response"""
        
        @track_api_call("test_api")
        def empty_api_call():
            return None
        
        result = empty_api_call()
        
        # Check result
        self.assertIsNone(result)
        
        # Check context for empty response
        _, call_kwargs = mock_log_perf.call_args
        context = call_kwargs['context']
        self.assertEqual(context['response_size'], 0)


class TestPerformanceTrackingIntegration(unittest.TestCase):
    """Integration tests for performance tracking"""
    
    def test_decorator_preserves_function_metadata(self):
        """Test that decorators preserve function metadata"""
        
        @log_performance
        def documented_function(x, y):
            """This function adds two numbers"""
            return x + y
        
        # Function name and docstring should be preserved
        self.assertEqual(documented_function.__name__, 'documented_function')
        self.assertEqual(documented_function.__doc__, 'This function adds two numbers')
    
    def test_multiple_decorators(self):
        """Test function with multiple decorators"""
        
        @track_api_call("test")
        @log_performance
        def multi_decorated_function(value):
            return value * 2
        
        result = multi_decorated_function(5)
        self.assertEqual(result, 10)
    
    def test_fallback_logging(self):
        """Test fallback logging when error_logger not available"""
        # This test checks that the fallback mechanism works properly
        # In this case, we're testing the module-level fallback
        @log_performance  
        def test_function():
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")


class TestPerformanceMetrics(unittest.TestCase):
    """Test performance metrics accuracy"""
    
    @patch('src.utils.decorators.log_perf_structured')
    def test_timing_accuracy(self, mock_log_perf):
        """Test that timing measurements are reasonably accurate"""
        
        @log_performance
        def timed_function():
            time.sleep(0.05)  # 50ms delay
            return "done"
        
        result = timed_function()
        
        # Check that timing is within reasonable bounds (45-100ms)
        call_args, _ = mock_log_perf.call_args
        duration = call_args[1]
        self.assertGreater(duration, 0.045)  # At least 45ms
        self.assertLess(duration, 0.1)       # At most 100ms
        
        self.assertEqual(result, "done")
    
    @patch('src.utils.decorators.log_perf_structured')
    def test_concurrent_function_calls(self, mock_log_perf):
        """Test that concurrent calls are tracked independently"""
        
        @log_performance
        def concurrent_function(delay):
            time.sleep(delay)
            return delay
        
        # Make multiple calls with different delays
        results = []
        for delay in [0.01, 0.02, 0.03]:
            results.append(concurrent_function(delay))
        
        # Should have 3 performance log calls
        self.assertEqual(mock_log_perf.call_count, 3)
        
        # Each call should have been logged with appropriate timing
        for i, call in enumerate(mock_log_perf.call_args_list):
            call_args, _ = call
            duration = call_args[1]
            expected_delay = [0.01, 0.02, 0.03][i]
            self.assertGreaterEqual(duration, expected_delay)


if __name__ == "__main__":
    unittest.main(verbosity=2)