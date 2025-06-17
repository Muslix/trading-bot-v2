"""
Tests für utils/decorators.py
Teste Performance-Logging und Error-Handling Decorators
"""

import pytest
import asyncio
import time
from unittest.mock import patch
from src.utils.decorators import log_performance, async_log_performance


class TestLogPerformance:
    """Tests für den log_performance Decorator"""
    
    def test_successful_function_execution(self, capsys):
        """Test dass erfolgreiche Funktionen korrekt geloggt werden"""
        @log_performance
        def test_function():
            time.sleep(0.1)
            return "success"
        
        result = test_function()
        captured = capsys.readouterr()
        
        assert result == "success"
        assert "✅ test_function" in captured.out
        assert "0.1" in captured.out  # Execution time
    
    def test_function_with_parameters(self, capsys):
        """Test Decorator mit Funktionsparametern"""
        @log_performance
        def add_numbers(a, b):
            return a + b
        
        result = add_numbers(5, 3)
        captured = capsys.readouterr()
        
        assert result == 8
        assert "✅ add_numbers" in captured.out
    
    def test_function_with_exception(self, capsys):
        """Test Error-Handling im Decorator"""
        @log_performance
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            failing_function()
        
        captured = capsys.readouterr()
        assert "❌ failing_function FEHLER" in captured.out
        assert "Test error" in captured.out
    
    def test_decorator_preserves_function_metadata(self):
        """Test dass der Decorator Funktions-Metadaten erhält"""
        @log_performance
        def documented_function():
            """This is a test function"""
            pass
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function"


class TestAsyncLogPerformance:
    """Tests für den async_log_performance Decorator"""
    
    @pytest.mark.asyncio
    async def test_successful_async_function(self, capsys):
        """Test erfolgreiche async Funktions-Ausführung"""
        @async_log_performance
        async def async_test_function():
            await asyncio.sleep(0.1)
            return "async_success"
        
        result = await async_test_function()
        captured = capsys.readouterr()
        
        assert result == "async_success"
        assert "✅ async_test_function" in captured.out
    
    @pytest.mark.asyncio
    async def test_async_function_with_exception(self, capsys):
        """Test Error-Handling bei async Funktionen"""
        @async_log_performance
        async def failing_async_function():
            await asyncio.sleep(0.05)
            raise RuntimeError("Async test error")
        
        with pytest.raises(RuntimeError, match="Async test error"):
            await failing_async_function()
        
        captured = capsys.readouterr()
        assert "❌ failing_async_function FEHLER" in captured.out
        assert "Async test error" in captured.out
    
    @pytest.mark.asyncio
    async def test_async_decorator_timing(self, capsys):
        """Test dass Timing für async Funktionen korrekt ist"""
        @async_log_performance
        async def timed_async_function():
            await asyncio.sleep(0.2)
            return "timed"
        
        start_time = time.time()
        result = await timed_async_function()
        end_time = time.time()
        
        captured = capsys.readouterr()
        
        assert result == "timed"
        assert "✅ timed_async_function" in captured.out
        # Verify timing is approximately correct
        assert 0.15 < (end_time - start_time) < 0.25


class TestDecoratorIntegration:
    """Integration Tests für beide Decorators"""
    
    def test_multiple_decorated_functions(self, capsys):
        """Test mehrere decorierte Funktionen in Folge"""
        @log_performance
        def function_one():
            return 1
        
        @log_performance  
        def function_two():
            return 2
        
        result1 = function_one()
        result2 = function_two()
        captured = capsys.readouterr()
        
        assert result1 == 1
        assert result2 == 2
        assert captured.out.count("✅") == 2
        assert "function_one" in captured.out
        assert "function_two" in captured.out
    
    @pytest.mark.asyncio
    async def test_mixed_sync_async_functions(self, capsys):
        """Test Kombination von sync und async dekorierten Funktionen"""
        @log_performance
        def sync_function():
            return "sync"
        
        @async_log_performance
        async def async_function():
            return "async"
        
        sync_result = sync_function()
        async_result = await async_function()
        captured = capsys.readouterr()
        
        assert sync_result == "sync"
        assert async_result == "async"
        assert captured.out.count("✅") == 2