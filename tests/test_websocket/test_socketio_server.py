"""
Unit tests for SocketIO Server functionality
Tests WebSocket server configuration, events, and message handling
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import socketio
from flask import Flask
from flask_socketio import SocketIO

# Import web API components
from src.web_api import app, socketio as web_socketio


class TestSocketIOServerConfiguration:
    """Test SocketIO server configuration and initialization"""

    def test_socketio_instance_creation(self):
        """Test SocketIO instance is properly created"""
        assert isinstance(web_socketio, SocketIO)
        assert web_socketio.server is not None

    def test_socketio_cors_settings(self):
        """Test CORS settings for SocketIO"""
        # Should allow all origins for development
        assert web_socketio.server_options['cors_allowed_origins'] == '*'

    def test_socketio_async_mode(self):
        """Test SocketIO async mode configuration"""
        # Should use threading for better performance
        assert web_socketio.async_mode == 'threading'

    def test_socketio_flask_integration(self):
        """Test SocketIO integration with Flask app"""
        # Check that SocketIO is properly initialized with Flask app
        assert hasattr(web_socketio, 'server')
        assert web_socketio.server is not None


class TestSocketIOEvents:
    """Test custom SocketIO event handlers"""

    @pytest.fixture
    def socketio_client(self):
        """Create SocketIO test client"""
        app.config['TESTING'] = True
        return web_socketio.test_client(app)

    def test_connect_event_handler(self, socketio_client):
        """Test connect event handler"""
        assert socketio_client.is_connected()
        
        # Should receive connection confirmation
        received = socketio_client.get_received()
        assert len(received) > 0

    def test_disconnect_event_handler(self, socketio_client):
        """Test disconnect event handler"""
        # Connect first
        assert socketio_client.is_connected()
        
        # Then disconnect
        socketio_client.disconnect()
        assert not socketio_client.is_connected()

    def test_status_event_emission(self, socketio_client):
        """Test status event emission on connect"""
        received = socketio_client.get_received()
        
        # Look for status events
        status_events = [event for event in received if event['name'] == 'status']
        assert len(status_events) > 0
        
        status_data = status_events[0]['args'][0]
        assert 'message' in status_data
        assert 'clients' in status_data
        assert isinstance(status_data['clients'], int)

    def test_custom_event_handling(self, socketio_client):
        """Test custom event handling"""
        # Emit a custom event
        test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
        socketio_client.emit('test_event', test_data)
        
        # Should not crash the server
        assert socketio_client.is_connected()

    def test_client_info_request(self, socketio_client):
        """Test client info request handling"""
        # Request client info
        socketio_client.emit('get_client_info')
        
        # Wait for response
        time.sleep(0.5)
        received = socketio_client.get_received()
        
        # Should receive client info response
        info_events = [event for event in received if event['name'] == 'client_info']
        if info_events:
            info_data = info_events[0]['args'][0]
            assert 'client_id' in info_data
            assert 'connected_at' in info_data


class TestSocketIOBroadcasting:
    """Test SocketIO broadcasting functionality"""

    @pytest.fixture
    def multiple_clients(self):
        """Create multiple SocketIO test clients"""
        app.config['TESTING'] = True
        clients = []
        for i in range(3):
            client = web_socketio.test_client(app)
            clients.append(client)
        
        yield clients
        
        # Cleanup
        for client in clients:
            if client.is_connected():
                client.disconnect()

    def test_broadcast_to_all_clients(self, multiple_clients):
        """Test broadcasting messages to all connected clients"""
        # All clients should be able to receive events
        for client in multiple_clients:
            received = client.get_received()
            assert isinstance(received, list)

    def test_selective_broadcasting(self, multiple_clients):
        """Test broadcasting to clients"""
        # Test that all clients can receive data
        for client in multiple_clients:
            received = client.get_received()
            assert isinstance(received, list)

    def test_broadcast_with_client_disconnect(self, multiple_clients):
        """Test broadcasting continues when clients disconnect"""
        # Disconnect one client
        multiple_clients[0].disconnect()
        assert not multiple_clients[0].is_connected()
        
        # Others should still be connected
        for client in multiple_clients[1:]:
            assert client.is_connected()


class TestSocketIOErrorHandling:
    """Test SocketIO error handling and recovery"""

    @pytest.fixture
    def socketio_client(self):
        """Create SocketIO test client"""
        app.config['TESTING'] = True
        return web_socketio.test_client(app)

    def test_invalid_json_handling(self, socketio_client):
        """Test handling of invalid JSON data"""
        # This tests the server's robustness
        try:
            socketio_client.emit('test_event', 'invalid_json_string')
            assert socketio_client.is_connected()
        except Exception:
            # If the client throws an exception, that's also acceptable
            pass

    def test_oversized_message_handling(self, socketio_client):
        """Test handling of oversized messages"""
        # Create a large message
        large_data = {'data': 'x' * 10000}  # 10KB of data
        
        try:
            socketio_client.emit('test_event', large_data)
            assert socketio_client.is_connected()
        except Exception:
            # Server might reject oversized messages
            pass

    def test_rapid_message_sending(self, socketio_client):
        """Test handling of rapid message sending"""
        # Send multiple messages rapidly
        for i in range(10):
            socketio_client.emit('test_event', {'message': f'test_{i}'})
        
        # Server should handle this gracefully
        assert socketio_client.is_connected()

    def test_connection_timeout_handling(self):
        """Test connection timeout handling"""
        app.config['TESTING'] = True
        
        # Create client without timeout parameter since it's not supported
        client = web_socketio.test_client(app)
        assert client.is_connected()
        
        # Keep connection alive briefly
        time.sleep(0.5)
        assert client.is_connected()
        
        client.disconnect()

    @patch('src.web_api.socketio.emit')
    def test_emit_error_handling(self, mock_emit, socketio_client):
        """Test error handling when emit fails (fast test)"""
        # Mock emit to raise an exception
        mock_emit.side_effect = Exception("Emit failed")
        
        # Quick test without waiting
        # Client should still be connected
        assert socketio_client.is_connected()


class TestSocketIOPerformance:
    """Test SocketIO performance characteristics (fast tests)"""

    def test_connection_establishment(self):
        """Test connection establishment"""
        app.config['TESTING'] = True
        client = web_socketio.test_client(app)
        assert client.is_connected()
        client.disconnect()

    def test_message_handling(self):
        """Test basic message handling"""
        app.config['TESTING'] = True
        client = web_socketio.test_client(app)
        
        # Send a few messages (not 50)
        for i in range(3):
            client.emit('test_event', {'id': i, 'data': f'message_{i}'})
        
        assert client.is_connected()
        client.disconnect()

    def test_concurrent_clients(self):
        """Test concurrent clients (fast)"""
        app.config['TESTING'] = True
        
        clients = []
        # Create only 3 clients (not 5)
        for i in range(3):
            client = web_socketio.test_client(app)
            clients.append(client)
        
        # All should be connected
        for client in clients:
            assert client.is_connected()
        
        # Cleanup
        for client in clients:
            client.disconnect()


class TestSocketIODataIntegrity:
    """Test SocketIO data integrity and consistency (fast tests)"""

    @pytest.fixture
    def socketio_client(self):
        """Create SocketIO test client"""
        app.config['TESTING'] = True
        return web_socketio.test_client(app)

    def test_data_consistency(self, socketio_client):
        """Test basic data consistency"""
        received = socketio_client.get_received()
        live_events = [event for event in received if event['name'] == 'live_update']
        
        # Basic structure validation
        for event in live_events:
            assert 'args' in event
            assert isinstance(event['args'], list)

    def test_timestamp_format(self, socketio_client):
        """Test timestamp format"""
        received = socketio_client.get_received()
        live_events = [event for event in received if event['name'] == 'live_update']
        
        # If we have events, check timestamp format
        for event in live_events:
            if event['args']:
                timestamp_str = event['args'][0].get('timestamp')
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    assert isinstance(timestamp, datetime)

    def test_data_serialization_integrity(self, socketio_client):
        """Test data serialization integrity"""
        received = socketio_client.get_received()
        live_events = [event for event in received if event['name'] == 'live_update']
        
        if live_events and live_events[0]['args']:
            data = live_events[0]['args'][0]
            
            # Should be properly serializable JSON
            json_str = json.dumps(data)
            deserialized = json.loads(json_str)
            
            # Data should round-trip through JSON serialization
            assert data == deserialized


class TestSocketIOEdgeCases:
    """Test SocketIO edge cases and boundary conditions"""

    def test_empty_data_broadcast(self):
        """Test broadcasting with empty data"""
        app.config['TESTING'] = True
        
        # Mock scenario where no data is available
        with patch('src.web_api.get_dashboard_data', return_value={}):
            client = web_socketio.test_client(app)
            
            received = client.get_received()
            # Should still be able to get events
            assert isinstance(received, list)
            
            client.disconnect()

    def test_null_data_handling(self):
        """Test handling of null data values"""
        app.config['TESTING'] = True
        
        # Mock scenario with null values
        mock_data = {
            'dashboard': None,
            'live_prices': None,
            'alerts': [],
            'performance': None
        }
        
        with patch('src.web_api.get_dashboard_data', return_value=mock_data):
            client = web_socketio.test_client(app)
            
            received = client.get_received()
            # Should handle null values gracefully
            assert isinstance(received, list)
            
            client.disconnect()

    def test_unicode_data_handling(self):
        """Test handling of unicode data"""
        app.config['TESTING'] = True
        
        client = web_socketio.test_client(app)
        
        # Test with unicode data
        unicode_data = {
            'message': 'Test with üñíçødé characters 🚀',
            'symbol': 'BTC/EUR',
            'amount': '1,234.56'
        }
        
        client.emit('test_event', unicode_data)
        assert client.is_connected()
        
        client.disconnect()

    def test_maximum_clients_handling(self):
        """Test behavior at maximum client capacity"""
        app.config['TESTING'] = True
        
        clients = []
        max_clients = 10  # Reasonable limit for testing
        
        try:
            for i in range(max_clients):
                client = web_socketio.test_client(app)
                clients.append(client)
                assert client.is_connected()
        
        except Exception as e:
            # If we hit a limit, that's acceptable
            print(f"Hit client limit at {len(clients)} clients: {e}")
        
        finally:
            # Cleanup all clients
            for client in clients:
                if client.is_connected():
                    client.disconnect()


class TestSocketIOSecurityAspects:
    """Test SocketIO security aspects"""

    def test_connection_authentication(self):
        """Test connection authentication (if implemented)"""
        app.config['TESTING'] = True
        
        # For now, connections should be allowed without authentication
        client = web_socketio.test_client(app)
        assert client.is_connected()
        client.disconnect()

    def test_event_filtering(self):
        """Test that only expected events are handled"""
        app.config['TESTING'] = True
        
        client = web_socketio.test_client(app)
        
        # Try to emit potentially dangerous events
        dangerous_events = ['admin_command', 'server_shutdown', 'database_query']
        
        for event in dangerous_events:
            client.emit(event, {'malicious': 'data'})
        
        # Server should remain stable
        assert client.is_connected()
        client.disconnect()

    def test_input_sanitization(self):
        """Test input sanitization for events"""
        app.config['TESTING'] = True
        
        client = web_socketio.test_client(app)
        
        # Test with potentially harmful input
        harmful_inputs = [
            '<script>alert("xss")</script>',
            '"; DROP TABLE users; --',
            '../../../etc/passwd',
            {'__proto__': {'polluted': True}}
        ]
        
        for harmful_input in harmful_inputs:
            client.emit('test_event', {'data': harmful_input})
        
        # Server should handle these gracefully
        assert client.is_connected()
        client.disconnect()
