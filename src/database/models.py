"""
Database Models - Type-safe data models for all database entities.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import json


@dataclass
class BaseModel:
    """Base model with common functionality"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations"""
        data = asdict(self)
        # Convert datetime to string for SQLite
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary"""
        # Convert string dates back to datetime
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        # Filter out unknown fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)


@dataclass
class PriceData(BaseModel):
    """Model for price history data"""
    symbol: str = ""
    exchange: str = ""
    price: float = 0.0
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass 
class ArbitrageAlert(BaseModel):
    """Model for arbitrage alert data"""
    symbol: str = ""
    buy_exchange: str = ""
    sell_exchange: str = ""
    buy_price: float = 0.0
    sell_price: float = 0.0
    profit_percentage: float = 0.0
    profit_amount: float = 0.0
    volume_available: Optional[float] = None
    alert_sent: bool = False
    telegram_message_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        # Calculate profit if not provided
        if self.profit_amount == 0.0 and self.buy_price > 0:
            self.profit_amount = self.sell_price - self.buy_price
        
        if self.profit_percentage == 0.0 and self.buy_price > 0:
            self.profit_percentage = ((self.sell_price - self.buy_price) / self.buy_price) * 100


@dataclass
class PerformanceData(BaseModel):
    """Model for cryptocurrency performance analysis data"""
    symbol: str = ""
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    annual_return: float = 0.0
    volatility: float = 0.0
    max_drawdown: float = 0.0
    var_95: float = 0.0
    beta_vs_btc: float = 1.0
    current_price: float = 0.0
    data_source: str = "unknown"
    analysis_date: Optional[datetime] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.analysis_date is None:
            self.analysis_date = datetime.now()


@dataclass
class BotStatistics(BaseModel):
    """Model for bot runtime statistics"""
    total_arbitrage_checks: int = 0
    total_performance_analyses: int = 0
    arbitrage_opportunities_found: int = 0
    alerts_sent: int = 0
    uptime_hours: float = 0.0
    session_start: Optional[datetime] = None
    session_end: Optional[datetime] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TelegramMessage(BaseModel):
    """Model for Telegram message logs"""
    chat_id: str = ""
    message_type: str = ""
    message_text: str = ""
    telegram_message_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PortfolioSnapshot(BaseModel):
    """Model for portfolio analysis snapshots"""
    snapshot_type: str = "performance_check"
    top_performers: str = ""  # JSON string
    total_coins_analyzed: int = 0
    avg_sharpe_ratio: float = 0.0
    best_performer_symbol: str = ""
    best_performer_sharpe: float = 0.0
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def set_top_performers(self, performers_list: list):
        """Set top performers from list and encode as JSON"""
        self.top_performers = json.dumps(performers_list, default=str)
    
    def get_top_performers(self) -> list:
        """Get top performers as list from JSON"""
        try:
            return json.loads(self.top_performers) if self.top_performers else []
        except json.JSONDecodeError:
            return []


# Model Registry for dynamic access
MODEL_REGISTRY = {
    'price_data': PriceData,
    'arbitrage_alert': ArbitrageAlert,
    'performance_data': PerformanceData,
    'bot_statistics': BotStatistics,
    'telegram_message': TelegramMessage,
    'portfolio_snapshot': PortfolioSnapshot
}


def get_model_class(model_name: str):
    """Get model class by name"""
    return MODEL_REGISTRY.get(model_name)