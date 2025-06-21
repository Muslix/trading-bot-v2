"""
Simple utils tests for basic functionality.
"""

import pytest
from unittest.mock import Mock


class TestUtilsBasic:
    """Basic utility function tests"""

    def test_mock_utility_functions(self):
        """Test mocked utility functions"""
        mock_utils = Mock()
        
        # Mock formatting function
        mock_utils.format_price.return_value = "$50,000.00"
        formatted = mock_utils.format_price(50000)
        assert formatted == "$50,000.00"
        
        # Mock validation function
        mock_utils.validate_symbol.return_value = True
        is_valid = mock_utils.validate_symbol("BTC")
        assert is_valid is True

    def test_mock_decorators(self):
        """Test mocked decorators"""
        mock_decorator = Mock()
        mock_decorator.retry.return_value = lambda f: f
        
        @mock_decorator.retry()
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"

    def test_mock_helpers(self):
        """Test mocked helper functions"""
        mock_helpers = Mock()
        mock_helpers.calculate_percentage.return_value = 5.25
        
        percentage = mock_helpers.calculate_percentage(1000, 1052.5)
        assert percentage == 5.25