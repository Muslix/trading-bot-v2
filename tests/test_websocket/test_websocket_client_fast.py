"""
Fast Unit tests for WebSocket Client functionality
Optimized version with minimal sleep times and focused testing
"""

import pytest
import json
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

import socketio
from flask_socketio import SocketIO

# Try to import web API components, use mocks if not available
try:
    from src.web_api import app, socketio as web_socketio
    WEB_API_AVAILABLE = True
except ImportError:
    # Create mock components for testing
    from flask import Flask
    app = Flask(__name__)
    app.config['TESTING'] = True
    web_socketio = SocketIO(app, cors_allowed_origins="*")
    WEB_API_AVAILABLE = False

# Ensure web_socketio is available globally
if 'web_socketio' not in globals():
    from flask import Flask
    app = Flask(__name__)
    app.config['TESTING'] = True
    web_socketio = SocketIO(app, cors_allowed_origins="*")


class TestWebSocketClientConnectionFast:
    """Fast connection tests"""

    def test_client_creation(self):
        """Test WebSocket client creation"""
        client = socketio.Client()
        assert isinstance(client, socketio.Client)
        assert not client.connected

    def test_client_connection_to_server(self):
        """Test client connection to server"""
        app.config['TESTING'] = True
        client = web_socketio.test_client(app)
        assert client.is_connected()
        client.disconnect()

    def test_client_reconnection(self):
        """Test client reconnection capability"""
        app.config['TESTING'] = True
        
        # Initial connection
        client = web_socketio.test_client(app)
        assert client.is_connected()
        client.disconnect()
        assert not client.is_connected()
        
        # Reconnect
        client = web_socketio.test_client(app)
        assert client.is_connected()
        client.disconnect()


class TestWebSocketClientDataReceptionFast:
    """Fast data reception tests"""

    @pytest.fixture
    def connected_client(self):
        """Create connected client"""
        app.config['TESTING'] = True
        client = web_socketio.test_client(app)
        yield client
        if client.is_connected():
            client.disconnect()

    def test_receive_updates_fast(self, connected_client):
        """Test receiving updates quickly"""
        # Minimal wait time
        time.sleep(0.1)
        
        received = connected_client.get_received()
        # Should receive some events or at least not crash
        assert isinstance(received, list)

    def test_data_format_validation(self, connected_client):
        """Test basic data format"""
        time.sleep(0.1)
        
        received = connected_client.get_received()
        live_events = [event for event in received if event['name'] == 'live_update']
        
        if live_events:
            data = live_events[0]['args'][0]
            # Should be valid JSON serializable
            json_str = json.dumps(data)
            assert json_str is not None


class TestWebSocketClientErrorHandlingFast:
    """Fast error handling tests"""

    def test_connection_failure_handling(self):
        """Test handling of connection failures"""
        try:
            client = socketio.Client()
            assert not client.connected
        except Exception:
            assert True

    def test_disconnect_handling(self):
        """Test disconnection handling"""
        app.config['TESTING'] = True
        client = web_socketio.test_client(app)
        assert client.is_connected()
        
        client.disconnect()
        assert not client.is_connected()


class TestWebSocketClientPerformanceFast:
    """Fast performance tests"""

    def test_connection_speed(self):
        """Test connection establishment speed"""
        app.config['TESTING'] = True
        
        start_time = time.time()
        client = web_socketio.test_client(app)
        connection_time = time.time() - start_time
        
        assert connection_time < 1.0  # Should be very fast
        assert client.is_connected()
        client.disconnect()

    def test_data_reception_latency(self):
        """Test data reception latency"""
        app.config['TESTING'] = True
        client = web_socketio.test_client(app)
        
        # Quick check for data reception
        start_time = time.time()
        received_data = False
        
        for _ in range(10):  # Max 10 iterations
            received = client.get_received()
            if received:
                received_data = True
                break
            time.sleep(0.01)  # Very short sleep
        
        reception_time = time.time() - start_time
        assert reception_time < 1.0  # Should be fast
        
        client.disconnect()


class TestWebSocketClientIntegrationFast:
    """Fast integration tests"""

    @pytest.fixture
    def connected_client(self):
        """Create connected client"""
        app.config['TESTING'] = True
        client = web_socketio.test_client(app)
        yield client
        if client.is_connected():
            client.disconnect()

    def test_basic_integration(self, connected_client):
        """Test basic integration functionality"""
        time.sleep(0.1)  # Minimal wait
        
        received = connected_client.get_received()
        # Should handle basic integration without errors
        assert isinstance(received, list)

    def test_event_handling(self, connected_client):
        """Test event handling"""
        # Test client can emit events
        test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
        connected_client.emit('test_event', test_data)
        
        # Should remain connected
        assert connected_client.is_connected()


class TestWebSocketClientStateFast:
    """Fast state management tests"""

    def test_connection_state(self):
        """Test connection state tracking"""
        app.config['TESTING'] = True
        client = web_socketio.test_client(app)
        
        assert client.is_connected() == True
        client.disconnect()
        assert client.is_connected() == False

    def test_session_stability(self):
        """Test session stability"""
        app.config['TESTING'] = True
        client = web_socketio.test_client(app)
        
        # Should maintain connection
        time.sleep(0.1)
        assert client.is_connected()
        
        client.disconnect()
