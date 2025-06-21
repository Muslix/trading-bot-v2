"""
Modular Web API Server für Crypto Trading Bot Dashboard
Plugin-based Flask API with improved architecture
"""

import asyncio
import logging
import os
import sys
import threading
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.api import create_api_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/web_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ModularWebAPI:
    """Modular Web API with plugin architecture"""
    
    def __init__(self, host='0.0.0.0', port=5000, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.api_manager = None
        self.app = None
        self.socketio = None
        self.logger = logging.getLogger('web_api')
        
    async def initialize(self):
        """Initialize the modular web API"""
        try:
            self.logger.info("🚀 Initializing Modular Web API...")
            
            # Create API manager with plugin architecture
            config = {
                'host': self.host,
                'port': self.port,
                'debug': self.debug
            }
            
            self.api_manager = await create_api_manager(config)
            self.app = self.api_manager.app
            self.socketio = self.api_manager.socketio
            
            # Setup WebSocket events if WebSocket plugin is loaded
            websocket_plugin = self.api_manager.get_plugin('websocket')
            if websocket_plugin:
                websocket_plugin.setup_socketio_events(self.socketio)
                self.logger.info("🔌 WebSocket events configured")
            
            # Add global error handlers
            self._setup_error_handlers()
            
            # Add health check endpoint
            self._setup_health_endpoint()
            
            self.logger.info(f"✅ Modular Web API initialized with {len(self.api_manager.list_plugins())} plugins")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Web API: {e}")
            return False
    
    def _setup_error_handlers(self):
        """Setup global error handlers"""
        @self.app.errorhandler(404)
        def not_found(error):
            return {'error': 'Endpoint not found'}, 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return {'error': 'Internal server error'}, 500
        
        self.logger.info("🛡️ Global error handlers configured")
    
    def _setup_health_endpoint(self):
        """Setup health check endpoint"""
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """API health check"""
            try:
                health_data = self.api_manager.health_check()
                health_data['timestamp'] = datetime.now().isoformat()
                return health_data
            except Exception as e:
                return {'status': 'error', 'error': str(e)}, 500
        
        @self.app.route('/api/plugins', methods=['GET'])
        def list_plugins():
            """List loaded plugins"""
            try:
                plugins = self.api_manager.list_plugins()
                return {
                    'plugins': plugins,
                    'count': len(plugins),
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                return {'error': str(e)}, 500
        
        self.logger.info("🏥 Health endpoints configured")
    
    def run(self):
        """Run the web API server"""
        try:
            self.logger.info(f"🌐 Starting Web API server on {self.host}:{self.port}")
            self.logger.info(f"📊 Loaded plugins: {', '.join(self.api_manager.list_plugins())}")
            
            # Run SocketIO server
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=self.debug,
                allow_unsafe_werkzeug=True
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error running Web API server: {e}")
    
    def shutdown(self):
        """Shutdown the web API server"""
        try:
            if self.api_manager:
                self.api_manager.cleanup()
            self.logger.info("🛑 Web API server shutdown complete")
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")


async def main():
    """Main entry point for the modular web API"""
    try:
        # Create and initialize the modular web API
        web_api = ModularWebAPI(
            host='0.0.0.0',
            port=5000,
            debug=False
        )
        
        success = await web_api.initialize()
        if success:
            # Run in a separate thread to allow for graceful shutdown
            server_thread = threading.Thread(target=web_api.run, daemon=True)
            server_thread.start()
            
            logger.info("✅ Modular Web API started successfully")
            logger.info("🔗 Available endpoints:")
            logger.info("   • /health - API health check")
            logger.info("   • /api/plugins - List loaded plugins")
            logger.info("   • /api/* - Plugin endpoints")
            logger.info("   • WebSocket: / - Real-time updates")
            
            # Keep the main thread alive
            try:
                server_thread.join()
            except KeyboardInterrupt:
                logger.info("🛑 Shutting down Web API...")
                web_api.shutdown()
        else:
            logger.error("❌ Failed to start Web API")
            
    except Exception as e:
        logger.error(f"❌ Critical error in Web API: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Web API stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")