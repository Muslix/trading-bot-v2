# 🏗️ Universal Core Pattern Documentation

## 📚 Übersicht

Das **Universal Core Pattern** ist das Fundament für alle Module im Trading Bot. Es bietet eine einheitliche, wiederverwendbare Architektur für:

- 🚨 **Alerts** (Arbitrage, Performance, Technical, etc.)
- 📊 **Data Sources** (Binance, CoinGecko, Yahoo Finance, etc.)
- 💾 **Database Repositories** (Prices, Alerts, Metrics, etc.)
- 🌐 **API Routes** (REST Endpoints als Plugins)
- ⚙️ **Configurations** (Type-safe settings)

## 🎯 Kernprinzipien

### ✅ **Konsistenz**
Alle Module folgen dem gleichen Pattern - einmal gelernt, überall anwendbar.

### ✅ **Plugin-Architektur**
Jedes Modul ist erweiterbar durch Plugins ohne Core-Code-Änderungen.

### ✅ **Type-Safety**
Typisierte Konfigurationen und Interfaces für weniger Runtime-Errors.

### ✅ **Observability**
Eingebaute Health Checks, Metrics und Logging für alle Module.

## 🏗️ Core Components

### 1. **UniversalPlugin** (Base Class)
```python
from src.core import UniversalPlugin, ModuleConfig

class MyAlert(UniversalPlugin):
    @property
    def plugin_type(self) -> str:
        return "alert"
    
    async def _initialize(self) -> bool:
        # Plugin-specific setup
        return True
    
    async def _execute(self, data: dict) -> dict:
        # Plugin-specific logic
        return {"result": "success"}
```

### 2. **UniversalManager** (Orchestrator)
```python
from src.core import UniversalManager

# Create manager for any module
manager = UniversalManager("alerts")

# Register plugins
await manager.register_plugin("arbitrage", ArbitrageAlert, config)

# Execute plugins
result = await manager.execute_plugin("arbitrage", data)
results = await manager.execute_all(data)  # All plugins

# Health monitoring
health = await manager.health_check_all()
metrics = manager.get_metrics()
```

### 3. **UniversalFactory** (Creator)
```python
from src.core import UniversalFactory

factory = UniversalFactory("alerts")

# Manual registration
factory.register("arbitrage", ArbitrageAlert)

# Auto-discovery from package
factory.auto_discover("src.alerts.plugins")

# Create instances
plugin = factory.create("arbitrage", config)
```

### 4. **ModuleConfig** (Configuration)
```python
from src.core import ModuleConfig

config = ModuleConfig(
    enabled=True,
    priority=1,
    timeout=30.0,
    retry_count=3,
    custom_settings={
        "threshold": 2.0,
        "cooldown": 300
    }
)
```

## 🚀 Quick Start

### 1. **Erstelle einen neuen Alert Plugin:**
```python
# src/alerts/plugins/volume_spike_alert.py
from src.core import UniversalPlugin

class VolumeSpikeAlert(UniversalPlugin):
    @property
    def plugin_type(self) -> str:
        return "alert"
    
    async def _initialize(self) -> bool:
        return True
    
    async def _execute(self, data: dict) -> dict:
        volume_change = data.get('volume_24h_change', 0)
        threshold = self.config.custom_settings.get('threshold', 500)
        
        if volume_change > threshold:
            return {
                "triggered": True,
                "message": f"🔥 Volume Spike: {data['symbol']} +{volume_change:.0f}%"
            }
        
        return {"triggered": False}
```

### 2. **Verwende den Alert:**
```python
from src.core import UniversalManager, ModuleConfig

# Setup
manager = UniversalManager("alerts")
config = ModuleConfig(custom_settings={"threshold": 300})

# Register
await manager.register_plugin("volume_spike", VolumeSpikeAlert, config)

# Execute
result = await manager.execute_plugin("volume_spike", {
    "symbol": "BTC/USD",
    "volume_24h_change": 450
})

print(result)  # {"success": True, "result": {"triggered": True, "message": "🔥 Volume Spike..."}}
```

## 📋 Module Beispiele

### 🚨 **Alerts Module**
```python
# All alerts follow the same pattern
class ArbitrageAlert(UniversalPlugin):
    plugin_type = "alert"
    # Implementation...

class PerformanceAlert(UniversalPlugin):
    plugin_type = "alert"
    # Implementation...
```

### 📊 **Data Sources Module**
```python
# All data sources follow the same pattern
class BinanceDataSource(UniversalPlugin):
    plugin_type = "data_source"
    # Implementation...

class CoinGeckoDataSource(UniversalPlugin):
    plugin_type = "data_source"
    # Implementation...
```

### 💾 **Database Module**
```python
# All repositories follow the same pattern
class PriceRepository(UniversalPlugin):
    plugin_type = "repository"
    # Implementation...

class AlertRepository(UniversalPlugin):
    plugin_type = "repository"
    # Implementation...
```

## 🔧 Advanced Features

### **Auto-Discovery**
```python
# Automatically load all plugins from a package
manager = UniversalManager("alerts", auto_discover_path="src.alerts.plugins")
await manager.initialize()  # Loads all plugins automatically
```

### **Priority Execution**
```python
# Configure plugin priorities
high_priority = ModuleConfig(priority=10)
low_priority = ModuleConfig(priority=1)

# Execute in priority order
results = await manager.execute_all(data, prioritized=True)
```

### **Health Monitoring**
```python
# Check health of all plugins
health = await manager.health_check_all()

if health['overall_health'] != 'healthy':
    print(f"Issues detected: {health['healthy_plugins']}/{health['total_plugins']} healthy")
    
    for plugin_name, plugin_health in health['plugins'].items():
        if plugin_health['status'] != 'healthy':
            print(f"❌ {plugin_name}: {plugin_health.get('error', 'Unknown issue')}")
```

### **Metrics Collection**
```python
# Get detailed metrics
metrics = manager.get_metrics()

print(f"Total Executions: {metrics['execution_stats']['total_executions']}")
print(f"Success Rate: {metrics['execution_stats']['success_rate']:.1f}%")

# Per-plugin metrics
for plugin_name, plugin_metrics in metrics['plugins'].items():
    print(f"{plugin_name}: {plugin_metrics['execution_count']} executions")
```

## 🧪 Testing

Run the included test to validate everything works:

```bash
python test_universal_pattern.py
```

This will test:
- ✅ Factory registration
- ✅ Manager initialization
- ✅ Plugin execution
- ✅ Health checks
- ✅ Metrics collection
- ✅ Error handling

## 📈 Benefits

### **🔧 Developer Experience**
- **5-minute plugin development** - Copy pattern, implement logic, done!
- **Consistent interfaces** - Same methods across all modules
- **Auto-discovery** - No manual registration needed
- **Type-safe** - Configuration errors caught at startup

### **🚀 Operations**
- **Health monitoring** - Built-in health checks for all plugins
- **Metrics collection** - Automatic execution statistics
- **Error handling** - Consistent error propagation and logging
- **Resource management** - Automatic cleanup and connection pooling

### **📊 Business Value**
- **Faster development** - New features in minutes instead of hours
- **Community contributions** - Easy for others to add plugins
- **Enterprise ready** - Scalable, maintainable architecture
- **Future-proof** - Easy to extend and modify

## 🔄 Migration Guide

### **From Monolithic to Universal Pattern:**

1. **Extract existing logic into plugins**:
   ```python
   # Old: Everything in one class
   class SmartAlerts:
       def check_arbitrage(self): pass
       def check_performance(self): pass
   
   # New: Each as separate plugin
   class ArbitrageAlert(UniversalPlugin): pass
   class PerformanceAlert(UniversalPlugin): pass
   ```

2. **Replace direct calls with manager execution**:
   ```python
   # Old: Direct instantiation
   alerts = SmartAlerts()
   alerts.check_arbitrage(data)
   
   # New: Manager execution
   manager = UniversalManager("alerts")
   await manager.execute_plugin("arbitrage", data)
   ```

3. **Add configuration schemas**:
   ```python
   # Old: Hardcoded values
   THRESHOLD = 2.0
   
   # New: Configurable
   config = ModuleConfig(custom_settings={"threshold": 2.0})
   ```

## 📞 Support

For questions about the Universal Pattern:
1. Check the test file: `test_universal_pattern.py`
2. Review existing plugins in `src/alerts/plugins/`
3. Read the core source: `src/core/`

The pattern is designed to be self-documenting and consistent! 🎯
