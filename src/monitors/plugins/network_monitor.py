"""
Network Monitor Plugin - Network and system monitoring
"""

import psutil
import asyncio
from typing import Dict, List, Any
import logging

from ..base import BaseMonitor
from src.utils.decorators import async_log_performance


class NetworkMonitor(BaseMonitor):
    """System and network monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.check_interval = config.get("check_interval", 60)  # seconds
        self.cpu_threshold = config.get("cpu_threshold", 80)    # percent
        self.memory_threshold = config.get("memory_threshold", 85)  # percent
        self.disk_threshold = config.get("disk_threshold", 90)  # percent
        
    def get_monitor_type(self) -> str:
        return "network"
        
    @async_log_performance
    async def monitor(self, target: Any, **kwargs) -> Dict[str, Any]:
        """
        Monitor system health and network status
        
        Args:
            target: str - Type of monitoring ('system', 'network', 'all')
            kwargs: Additional parameters
        """
        monitor_type = target if isinstance(target, str) else "all"
        
        try:
            result = {
                "monitor_type": monitor_type,
                "timestamp": kwargs.get("timestamp", "unknown")
            }
            
            if monitor_type in ["system", "all"]:
                result["system"] = await self._get_system_metrics()
                
            if monitor_type in ["network", "all"]:
                result["network"] = await self._get_network_metrics()
                
            # Add health status
            result["health_status"] = self._calculate_health_status(result)
            
            return result
            
        except Exception as e:
            return {"error": f"Network monitoring failed: {str(e)}"}
            
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Process count
            process_count = len(psutil.pids())
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "core_count": cpu_count,
                    "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                    "free_percent": round(100 - memory.percent, 2)
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 2)
                },
                "processes": {
                    "count": process_count
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {"error": str(e)}
            
    async def _get_network_metrics(self) -> Dict[str, Any]:
        """Get network performance metrics"""
        try:
            # Network I/O
            net_io = psutil.net_io_counters()
            
            # Network connections
            connections = psutil.net_connections()
            
            # Test internet connectivity
            connectivity = await self._test_connectivity()
            
            return {
                "io": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "errors_in": net_io.errin,
                    "errors_out": net_io.errout
                },
                "connections": {
                    "total": len(connections),
                    "established": len([c for c in connections if c.status == 'ESTABLISHED']),
                    "listening": len([c for c in connections if c.status == 'LISTEN'])
                },
                "connectivity": connectivity
            }
            
        except Exception as e:
            self.logger.error(f"Error getting network metrics: {e}")
            return {"error": str(e)}
            
    async def _test_connectivity(self) -> Dict[str, bool]:
        """Test connectivity to important services"""
        test_urls = [
            "https://api.binance.com",
            "https://api.exchange.coinbase.com", 
            "https://api.coingecko.com"
        ]
        
        connectivity = {}
        
        for url in test_urls:
            try:
                import aiohttp
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as response:
                        connectivity[url] = response.status < 400
            except Exception:
                connectivity[url] = False
                
        return connectivity
        
    def _calculate_health_status(self, metrics: Dict[str, Any]) -> str:
        """Calculate overall health status"""
        issues = []
        
        if "system" in metrics and isinstance(metrics["system"], dict):
            system = metrics["system"]
            
            # Check CPU
            if "cpu" in system and system["cpu"].get("usage_percent", 0) > self.cpu_threshold:
                issues.append("high_cpu")
                
            # Check memory
            if "memory" in system and system["memory"].get("used_percent", 0) > self.memory_threshold:
                issues.append("high_memory")
                
            # Check disk
            if "disk" in system and system["disk"].get("used_percent", 0) > self.disk_threshold:
                issues.append("high_disk")
                
        if "network" in metrics and isinstance(metrics["network"], dict):
            network = metrics["network"]
            
            # Check connectivity
            if "connectivity" in network:
                failed_connections = sum(1 for connected in network["connectivity"].values() if not connected)
                if failed_connections > 0:
                    issues.append("connectivity_issues")
                    
        if not issues:
            return "healthy"
        elif len(issues) == 1:
            return "warning"
        else:
            return "critical"