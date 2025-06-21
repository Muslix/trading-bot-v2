"""
System Health Monitor Utility Plugin - system monitoring functionality
"""

import psutil
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta

from ..base import UtilPlugin, UtilConfig


class SystemHealthUtil(UtilPlugin):
    """
    System health monitoring utility plugin.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.health_history = []
        self.last_cleanup = datetime.now()
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0
        }
    
    async def _initialize_util(self) -> bool:
        """Initialize system health utility."""
        try:
            # Import original system health monitor functionality if exists
            from ..system_health_monitor import (
                get_system_health,
                check_memory_usage,
                check_disk_space
            )
            
            self.get_system_health = get_system_health
            self.check_memory_usage = check_memory_usage  
            self.check_disk_space = check_disk_space
            
        except ImportError:
            # Use built-in functionality
            self.get_system_health = self._get_system_health_internal
            self.check_memory_usage = self._check_memory_usage_internal
            self.check_disk_space = self._check_disk_space_internal
        
        self.logger.info("System health utility initialized")
        return True
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process system health operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "health_check")
        
        if action == "health_check":
            return await self._perform_health_check(data)
        elif action == "memory_check":
            return await self._check_memory(data)
        elif action == "disk_check":
            return await self._check_disk(data)
        elif action == "cpu_check":
            return await self._check_cpu(data)
        elif action == "full_report":
            return await self._get_full_system_report()
        elif action == "set_thresholds":
            return self._set_alert_thresholds(data)
        elif action == "get_history":
            return self._get_health_history(data)
        elif action == "cleanup":
            return await self._cleanup_resources()
        else:
            raise ValueError(f"Unknown system health action: {action}")
    
    async def _perform_health_check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a comprehensive health check."""
        try:
            health_data = await self._get_system_health_comprehensive()
            
            # Store in history
            self.health_history.append({
                "timestamp": datetime.now().isoformat(),
                "health_data": health_data
            })
            
            # Keep only last 100 entries
            if len(self.health_history) > 100:
                self.health_history = self.health_history[-100:]
            
            # Check for alerts
            alerts = self._check_health_alerts(health_data)
            
            return {
                "success": True,
                "health_data": health_data,
                "alerts": alerts,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_system_health_comprehensive(self) -> Dict[str, Any]:
        """Get comprehensive system health data."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "status": "normal" if cpu_percent < self.alert_thresholds["cpu_percent"] else "high"
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "status": "normal" if memory.percent < self.alert_thresholds["memory_percent"] else "high"
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                    "status": "normal" if (disk.used / disk.total) * 100 < self.alert_thresholds["disk_percent"] else "high"
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "processes": {
                    "count": process_count
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system health: {e}")
            return {"error": str(e)}
    
    def _get_system_health_internal(self) -> Dict[str, Any]:
        """Fallback system health check."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0,
                "status": "ok"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def _check_memory_usage_internal(self) -> Dict[str, Any]:
        """Fallback memory check."""
        try:
            memory = psutil.virtual_memory()
            return {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "status": "ok" if memory.percent < 85 else "warning"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _check_disk_space_internal(self) -> Dict[str, Any]:
        """Fallback disk check."""
        try:
            disk = psutil.disk_usage('/')
            percent = (disk.used / disk.total) * 100
            return {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": percent,
                "status": "ok" if percent < 90 else "warning"
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _check_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            result = self.check_memory_usage()
            return {"success": True, "memory_check": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _check_disk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check disk usage."""
        try:
            result = self.check_disk_space()
            return {"success": True, "disk_check": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _check_cpu(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            return {
                "success": True,
                "cpu_check": {
                    "percent": cpu_percent,
                    "status": "normal" if cpu_percent < self.alert_thresholds["cpu_percent"] else "high"
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_full_system_report(self) -> Dict[str, Any]:
        """Get a full system report."""
        try:
            health_data = await self._get_system_health_comprehensive()
            
            # Add additional system info
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            report = {
                "health_data": health_data,
                "system_info": {
                    "boot_time": boot_time.isoformat(),
                    "uptime_seconds": uptime.total_seconds(),
                    "uptime_human": str(uptime)
                },
                "plugin_stats": self._get_health_stats(),
                "timestamp": datetime.now().isoformat()
            }
            
            return {"success": True, "report": report}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _check_health_alerts(self, health_data: Dict[str, Any]) -> list:
        """Check if any health metrics exceed thresholds."""
        alerts = []
        
        # Check CPU
        if "cpu" in health_data and health_data["cpu"].get("status") == "high":
            alerts.append({
                "type": "cpu_high",
                "message": f"CPU usage high: {health_data['cpu']['percent']:.1f}%",
                "threshold": self.alert_thresholds["cpu_percent"],
                "current": health_data["cpu"]["percent"]
            })
        
        # Check Memory
        if "memory" in health_data and health_data["memory"].get("status") == "high":
            alerts.append({
                "type": "memory_high",
                "message": f"Memory usage high: {health_data['memory']['percent']:.1f}%",
                "threshold": self.alert_thresholds["memory_percent"],
                "current": health_data["memory"]["percent"]
            })
        
        # Check Disk
        if "disk" in health_data and health_data["disk"].get("status") == "high":
            alerts.append({
                "type": "disk_high",
                "message": f"Disk usage high: {health_data['disk']['percent']:.1f}%",
                "threshold": self.alert_thresholds["disk_percent"],
                "current": health_data["disk"]["percent"]
            })
        
        return alerts
    
    def _set_alert_thresholds(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set alert thresholds."""
        thresholds = data.get("thresholds", {})
        
        for key, value in thresholds.items():
            if key in self.alert_thresholds and isinstance(value, (int, float)):
                self.alert_thresholds[key] = float(value)
        
        return {
            "success": True,
            "updated_thresholds": self.alert_thresholds
        }
    
    def _get_health_history(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get health check history."""
        limit = data.get("limit", 10)
        
        return {
            "success": True,
            "history": self.health_history[-limit:],
            "total_entries": len(self.health_history)
        }
    
    async def _cleanup_resources(self) -> Dict[str, Any]:
        """Clean up resources and old data."""
        try:
            # Clean up old history entries
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            original_count = len(self.health_history)
            self.health_history = [
                entry for entry in self.health_history
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
            ]
            cleaned_count = original_count - len(self.health_history)
            
            self.last_cleanup = datetime.now()
            
            return {
                "success": True,
                "cleaned_entries": cleaned_count,
                "remaining_entries": len(self.health_history),
                "last_cleanup": self.last_cleanup.isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_health_stats(self) -> Dict[str, Any]:
        """Get health monitoring statistics."""
        return {
            "total_health_checks": len(self.health_history),
            "last_cleanup": self.last_cleanup.isoformat(),
            "alert_thresholds": self.alert_thresholds,
            "plugin_name": self.name,
            "enabled": self.config.enabled
        }