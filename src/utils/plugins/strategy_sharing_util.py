"""
Strategy Sharing Utility Plugin - community platform for trading strategies
"""

import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sqlite3
import os

from ..base import UtilPlugin, UtilConfig


class StrategySharing:
    """Strategy sharing data model"""
    
    def __init__(self, strategy_id: str, name: str, author: str, code: str, 
                 description: str, category: str, tags: List[str], 
                 performance_metrics: Dict[str, Any]):
        self.strategy_id = strategy_id
        self.name = name
        self.author = author
        self.code = code
        self.description = description
        self.category = category
        self.tags = tags
        self.performance_metrics = performance_metrics
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.downloads = 0
        self.rating = 0.0
        self.reviews = []
        self.verified = False


class StrategySharingUtil(UtilPlugin):
    """
    Strategy sharing utility plugin for community trading strategies.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.db_path = "data/strategy_sharing.db"
        self.strategies_shared = 0
        self.strategies_downloaded = 0
        self.last_operation_time = None
        
        # Strategy categories
        self.categories = [
            "arbitrage",
            "momentum", 
            "mean_reversion",
            "scalping",
            "swing_trading",
            "defi_yield",
            "grid_trading",
            "martingale",
            "technical_indicators",
            "machine_learning"
        ]
        
        # Risk levels
        self.risk_levels = ["low", "medium", "high", "extreme"]
        
        # Timeframes
        self.timeframes = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        
        # Performance thresholds for verification
        self.verification_thresholds = {
            "min_sharpe_ratio": 1.0,
            "min_total_return": 10.0,  # 10%
            "min_trades": 100,
            "max_drawdown": -20.0  # -20%
        }
    
    async def _initialize_util(self) -> bool:
        """Initialize strategy sharing utility."""
        try:
            # Create data directory
            os.makedirs("data", exist_ok=True)
            
            # Initialize database
            await self._init_database()
            
            self.logger.info("Strategy sharing utility initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize strategy sharing utility: {e}")
            return False
    
    async def _init_database(self):
        """Initialize SQLite database for strategy sharing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Strategies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                author TEXT NOT NULL,
                code TEXT NOT NULL,
                description TEXT,
                category TEXT,
                tags TEXT,
                performance_metrics TEXT,
                created_at TEXT,
                updated_at TEXT,
                downloads INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                verified BOOLEAN DEFAULT 0,
                risk_level TEXT,
                timeframe TEXT,
                min_capital REAL DEFAULT 1000
            )
        """)
        
        # Reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_reviews (
                review_id TEXT PRIMARY KEY,
                strategy_id TEXT,
                reviewer TEXT,
                rating INTEGER,
                comment TEXT,
                created_at TEXT,
                FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
            )
        """)
        
        # Downloads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_downloads (
                download_id TEXT PRIMARY KEY,
                strategy_id TEXT,
                user_id TEXT,
                downloaded_at TEXT,
                FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
            )
        """)
        
        # Strategy backtests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_backtests (
                backtest_id TEXT PRIMARY KEY,
                strategy_id TEXT,
                timeframe TEXT,
                start_date TEXT,
                end_date TEXT,
                initial_capital REAL,
                final_capital REAL,
                total_return REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                total_trades INTEGER,
                win_rate REAL,
                created_at TEXT,
                FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def _cleanup_util(self) -> None:
        """Clean up strategy sharing utility resources."""
        pass  # No specific cleanup needed for SQLite
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process strategy sharing operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "list_strategies")
        
        if action == "share_strategy":
            return await self._share_strategy(data)
        elif action == "get_strategy":
            return await self._get_strategy(data)
        elif action == "list_strategies":
            return await self._list_strategies(data)
        elif action == "search_strategies":
            return await self._search_strategies(data)
        elif action == "download_strategy":
            return await self._download_strategy(data)
        elif action == "rate_strategy":
            return await self._rate_strategy(data)
        elif action == "get_trending_strategies":
            return await self._get_trending_strategies(data)
        elif action == "verify_strategy":
            return await self._verify_strategy(data)
        elif action == "get_user_strategies":
            return await self._get_user_strategies(data)
        elif action == "update_strategy":
            return await self._update_strategy(data)
        elif action == "delete_strategy":
            return await self._delete_strategy(data)
        elif action == "get_platform_stats":
            return self._get_platform_stats()
        elif action == "get_stats":
            return self._get_sharing_stats()
        else:
            raise ValueError(f"Unknown strategy sharing action: {action}")
    
    async def _share_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Share a new trading strategy."""
        operation_start = datetime.now()
        name = data.get("name", "")
        author = data.get("author", "anonymous")
        code = data.get("code", "")
        description = data.get("description", "")
        category = data.get("category", "technical_indicators")
        tags = data.get("tags", [])
        performance_metrics = data.get("performance_metrics", {})
        risk_level = data.get("risk_level", "medium")
        timeframe = data.get("timeframe", "1h")
        min_capital = data.get("min_capital", 1000)
        
        self.logger.info(f"📤 New strategy submission: '{name}' by {author}")
        self.logger.info(f"   Category: {category}")
        self.logger.info(f"   Risk Level: {risk_level}")
        self.logger.info(f"   Timeframe: {timeframe}")
        self.logger.info(f"   Min Capital: ${min_capital:,}")
        self.logger.info(f"   Tags: {tags}")
        self.logger.info(f"   Code Length: {len(code)} characters")
        
        try:
            
            if not name or not code:
                self.logger.error(f"   ❌ Validation failed: Missing required fields")
                return {"success": False, "error": "Name and code are required"}
            
            if category not in self.categories:
                self.logger.error(f"   ❌ Validation failed: Invalid category '{category}'")
                return {"success": False, "error": f"Invalid category. Must be one of: {self.categories}"}
            
            # Generate strategy ID
            strategy_id = hashlib.md5(f"{name}_{author}_{datetime.now().isoformat()}".encode()).hexdigest()
            self.logger.info(f"   🆔 Generated strategy ID: {strategy_id}")
            
            # Validate code (basic syntax check)
            self.logger.info(f"   🔍 Validating strategy code...")
            validation_start = datetime.now()
            code_validation = self._validate_strategy_code(code)
            validation_duration = (datetime.now() - validation_start).total_seconds()
            
            if not code_validation["valid"]:
                self.logger.error(f"   ❌ Code validation failed after {validation_duration:.3f}s: {code_validation['error']}")
                return {"success": False, "error": f"Code validation failed: {code_validation['error']}"}
            
            self.logger.info(f"   ✅ Code validation passed ({validation_duration:.3f}s)")
            
            # Store in database
            self.logger.info(f"   💾 Storing strategy in database...")
            db_start = datetime.now()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO strategies 
                (strategy_id, name, author, code, description, category, tags, 
                 performance_metrics, created_at, updated_at, risk_level, timeframe, min_capital)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                strategy_id, name, author, code, description, category,
                json.dumps(tags), json.dumps(performance_metrics),
                datetime.now().isoformat(), datetime.now().isoformat(),
                risk_level, timeframe, min_capital
            ))
            
            conn.commit()
            conn.close()
            
            db_duration = (datetime.now() - db_start).total_seconds()
            operation_duration = (datetime.now() - operation_start).total_seconds()
            
            self.strategies_shared += 1
            self.last_operation_time = datetime.now()
            
            self.logger.info(f"   ✅ Strategy stored successfully ({db_duration:.3f}s)")
            self.logger.info(f"📤 Strategy sharing completed in {operation_duration:.3f}s")
            self.logger.info(f"   🎯 Total strategies shared: {self.strategies_shared}")
            
            return {
                "success": True,
                "strategy_id": strategy_id,
                "message": "Strategy shared successfully",
                "verification_pending": True,
                "operation_duration_seconds": operation_duration
            }
            
        except Exception as e:
            self.logger.error(f"Strategy sharing failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_strategy_code(self, code: str) -> Dict[str, Any]:
        """Validate strategy code for basic syntax and security."""
        try:
            # Basic syntax check
            compile(code, '<string>', 'exec')
            
            # Security checks - look for actual dangerous imports/calls, not just words
            dangerous_patterns = [
                'import os',
                'import sys', 
                'import subprocess',
                'from os',
                'from sys',
                'from subprocess',
                '__import__(',
                'eval(',
                'exec(',
                'open(',
                'file(',
                'input(',
                'raw_input('
            ]
            code_lower = code.lower()
            for dangerous in dangerous_patterns:
                if dangerous in code_lower:
                    return {"valid": False, "error": f"Dangerous pattern detected: {dangerous}"}
            
            # Check for required functions
            required_functions = ["strategy_logic", "get_signals"]
            for func in required_functions:
                if f"def {func}" not in code:
                    return {"valid": False, "error": f"Required function missing: {func}"}
            
            return {"valid": True}
            
        except SyntaxError as e:
            return {"valid": False, "error": f"Syntax error: {e}"}
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {e}"}
    
    async def _get_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific strategy by ID."""
        try:
            strategy_id = data.get("strategy_id", "")
            
            if not strategy_id:
                return {"success": False, "error": "Strategy ID is required"}
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM strategies WHERE strategy_id = ?", (strategy_id,))
            strategy = cursor.fetchone()
            
            if not strategy:
                conn.close()
                return {"success": False, "error": "Strategy not found"}
            
            # Get reviews
            cursor.execute("SELECT * FROM strategy_reviews WHERE strategy_id = ?", (strategy_id,))
            reviews = [dict(row) for row in cursor.fetchall()]
            
            # Get backtests
            cursor.execute("SELECT * FROM strategy_backtests WHERE strategy_id = ?", (strategy_id,))
            backtests = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            strategy_dict = dict(strategy)
            strategy_dict["tags"] = json.loads(strategy_dict.get("tags", "[]"))
            strategy_dict["performance_metrics"] = json.loads(strategy_dict.get("performance_metrics", "{}"))
            strategy_dict["reviews"] = reviews
            strategy_dict["backtests"] = backtests
            
            return {
                "success": True,
                "strategy": strategy_dict
            }
            
        except Exception as e:
            self.logger.error(f"Get strategy failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _list_strategies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """List strategies with filters."""
        try:
            category = data.get("category")
            risk_level = data.get("risk_level")
            timeframe = data.get("timeframe")
            verified_only = data.get("verified_only", False)
            limit = data.get("limit", 20)
            offset = data.get("offset", 0)
            sort_by = data.get("sort_by", "created_at")  # created_at, rating, downloads
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM strategies WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if risk_level:
                query += " AND risk_level = ?"
                params.append(risk_level)
            
            if timeframe:
                query += " AND timeframe = ?"
                params.append(timeframe)
            
            if verified_only:
                query += " AND verified = 1"
            
            # Sort
            if sort_by == "rating":
                query += " ORDER BY rating DESC"
            elif sort_by == "downloads":
                query += " ORDER BY downloads DESC"
            else:
                query += " ORDER BY created_at DESC"
            
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            strategies = []
            
            for row in cursor.fetchall():
                strategy = dict(row)
                strategy["tags"] = json.loads(strategy.get("tags", "[]"))
                strategy["performance_metrics"] = json.loads(strategy.get("performance_metrics", "{}"))
                # Don't include full code in list view
                strategy["code"] = "[Code available on download]"
                strategies.append(strategy)
            
            # Get total count
            count_query = query.replace("SELECT *", "SELECT COUNT(*)", 1).replace(" LIMIT ? OFFSET ?", "")
            cursor.execute(count_query, params[:-2])
            total_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "success": True,
                "strategies": strategies,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            self.logger.error(f"List strategies failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _download_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Download a strategy (increment download count)."""
        try:
            strategy_id = data.get("strategy_id", "")
            user_id = data.get("user_id", "anonymous")
            
            if not strategy_id:
                return {"success": False, "error": "Strategy ID is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if strategy exists
            cursor.execute("SELECT * FROM strategies WHERE strategy_id = ?", (strategy_id,))
            strategy = cursor.fetchone()
            
            if not strategy:
                conn.close()
                return {"success": False, "error": "Strategy not found"}
            
            # Record download
            download_id = hashlib.md5(f"{strategy_id}_{user_id}_{datetime.now().isoformat()}".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO strategy_downloads (download_id, strategy_id, user_id, downloaded_at)
                VALUES (?, ?, ?, ?)
            """, (download_id, strategy_id, user_id, datetime.now().isoformat()))
            
            # Increment download count
            cursor.execute("UPDATE strategies SET downloads = downloads + 1 WHERE strategy_id = ?", (strategy_id,))
            
            conn.commit()
            conn.close()
            
            self.strategies_downloaded += 1
            self.last_operation_time = datetime.now()
            
            return {
                "success": True,
                "message": "Strategy downloaded successfully",
                "download_id": download_id
            }
            
        except Exception as e:
            self.logger.error(f"Download strategy failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _rate_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Rate and review a strategy."""
        try:
            strategy_id = data.get("strategy_id", "")
            reviewer = data.get("reviewer", "anonymous")
            rating = data.get("rating", 5)
            comment = data.get("comment", "")
            
            if not strategy_id:
                return {"success": False, "error": "Strategy ID is required"}
            
            if not 1 <= rating <= 5:
                return {"success": False, "error": "Rating must be between 1 and 5"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if strategy exists
            cursor.execute("SELECT * FROM strategies WHERE strategy_id = ?", (strategy_id,))
            if not cursor.fetchone():
                conn.close()
                return {"success": False, "error": "Strategy not found"}
            
            # Add review
            review_id = hashlib.md5(f"{strategy_id}_{reviewer}_{datetime.now().isoformat()}".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO strategy_reviews (review_id, strategy_id, reviewer, rating, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (review_id, strategy_id, reviewer, rating, comment, datetime.now().isoformat()))
            
            # Recalculate average rating
            cursor.execute("SELECT AVG(rating) FROM strategy_reviews WHERE strategy_id = ?", (strategy_id,))
            avg_rating = cursor.fetchone()[0] or 0.0
            
            cursor.execute("UPDATE strategies SET rating = ? WHERE strategy_id = ?", (avg_rating, strategy_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Strategy rated successfully",
                "review_id": review_id,
                "new_average_rating": avg_rating
            }
            
        except Exception as e:
            self.logger.error(f"Rate strategy failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_trending_strategies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get trending strategies based on recent downloads and ratings."""
        try:
            timeframe_days = data.get("timeframe_days", 7)
            limit = data.get("limit", 10)
            
            since_date = (datetime.now() - timedelta(days=timeframe_days)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get strategies with recent activity
            cursor.execute("""
                SELECT s.*, 
                       COUNT(sd.download_id) as recent_downloads,
                       AVG(sr.rating) as recent_rating
                FROM strategies s
                LEFT JOIN strategy_downloads sd ON s.strategy_id = sd.strategy_id 
                    AND sd.downloaded_at >= ?
                LEFT JOIN strategy_reviews sr ON s.strategy_id = sr.strategy_id 
                    AND sr.created_at >= ?
                GROUP BY s.strategy_id
                ORDER BY (recent_downloads * 0.7 + (recent_rating * 20) * 0.3) DESC
                LIMIT ?
            """, (since_date, since_date, limit))
            
            trending = []
            for row in cursor.fetchall():
                strategy = dict(row)
                strategy["tags"] = json.loads(strategy.get("tags", "[]"))
                strategy["performance_metrics"] = json.loads(strategy.get("performance_metrics", "{}"))
                strategy["code"] = "[Code available on download]"
                trending.append(strategy)
            
            conn.close()
            
            return {
                "success": True,
                "trending_strategies": trending,
                "timeframe_days": timeframe_days,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Get trending strategies failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _search_strategies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Search strategies by keywords, tags, and filters."""
        try:
            query = data.get("query", "")
            category = data.get("category")
            tags = data.get("tags", [])
            min_rating = data.get("min_rating", 0)
            limit = data.get("limit", 20)
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build search query
            search_query = "SELECT * FROM strategies WHERE 1=1"
            params = []
            
            if query:
                search_query += " AND (name LIKE ? OR description LIKE ? OR author LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
            if category:
                search_query += " AND category = ?"
                params.append(category)
            
            if min_rating > 0:
                search_query += " AND rating >= ?"
                params.append(min_rating)
            
            # Tag filtering (if tags provided)
            if tags:
                for tag in tags:
                    search_query += " AND tags LIKE ?"
                    params.append(f"%{tag}%")
            
            search_query += " ORDER BY rating DESC, downloads DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(search_query, params)
            results = []
            
            for row in cursor.fetchall():
                strategy = dict(row)
                strategy["tags"] = json.loads(strategy.get("tags", "[]"))
                strategy["performance_metrics"] = json.loads(strategy.get("performance_metrics", "{}"))
                strategy["code"] = "[Code available on download]"  # Don't show full code in search
                results.append(strategy)
            
            conn.close()
            
            return {
                "success": True,
                "search_results": results,
                "query": query,
                "total_results": len(results),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Search strategies failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_user_strategies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get strategies by a specific user."""
        try:
            author = data.get("author", "")
            
            if not author:
                return {"success": False, "error": "Author is required"}
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM strategies WHERE author = ? ORDER BY created_at DESC", (author,))
            strategies = []
            
            for row in cursor.fetchall():
                strategy = dict(row)
                strategy["tags"] = json.loads(strategy.get("tags", "[]"))
                strategy["performance_metrics"] = json.loads(strategy.get("performance_metrics", "{}"))
                strategies.append(strategy)
            
            conn.close()
            
            return {
                "success": True,
                "user_strategies": strategies,
                "author": author,
                "total_strategies": len(strategies)
            }
            
        except Exception as e:
            self.logger.error(f"Get user strategies failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing strategy."""
        try:
            strategy_id = data.get("strategy_id", "")
            author = data.get("author", "")  # For authorization
            
            if not strategy_id or not author:
                return {"success": False, "error": "Strategy ID and author are required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if strategy exists and belongs to author
            cursor.execute("SELECT author FROM strategies WHERE strategy_id = ?", (strategy_id,))
            existing = cursor.fetchone()
            
            if not existing:
                conn.close()
                return {"success": False, "error": "Strategy not found"}
            
            if existing[0] != author:
                conn.close()
                return {"success": False, "error": "Not authorized to update this strategy"}
            
            # Update fields
            update_fields = []
            params = []
            
            for field in ["name", "description", "code", "category", "risk_level", "timeframe", "min_capital"]:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    params.append(data[field])
            
            if "tags" in data:
                update_fields.append("tags = ?")
                params.append(json.dumps(data["tags"]))
            
            if "performance_metrics" in data:
                update_fields.append("performance_metrics = ?")
                params.append(json.dumps(data["performance_metrics"]))
            
            if not update_fields:
                conn.close()
                return {"success": False, "error": "No fields to update"}
            
            # Add updated_at
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            # Add strategy_id for WHERE clause
            params.append(strategy_id)
            
            query = f"UPDATE strategies SET {', '.join(update_fields)} WHERE strategy_id = ?"
            cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Strategy updated successfully",
                "strategy_id": strategy_id
            }
            
        except Exception as e:
            self.logger.error(f"Update strategy failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _delete_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a strategy."""
        try:
            strategy_id = data.get("strategy_id", "")
            author = data.get("author", "")  # For authorization
            
            if not strategy_id or not author:
                return {"success": False, "error": "Strategy ID and author are required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if strategy exists and belongs to author
            cursor.execute("SELECT author FROM strategies WHERE strategy_id = ?", (strategy_id,))
            existing = cursor.fetchone()
            
            if not existing:
                conn.close()
                return {"success": False, "error": "Strategy not found"}
            
            if existing[0] != author:
                conn.close()
                return {"success": False, "error": "Not authorized to delete this strategy"}
            
            # Delete related records first
            cursor.execute("DELETE FROM strategy_reviews WHERE strategy_id = ?", (strategy_id,))
            cursor.execute("DELETE FROM strategy_downloads WHERE strategy_id = ?", (strategy_id,))
            cursor.execute("DELETE FROM strategy_backtests WHERE strategy_id = ?", (strategy_id,))
            cursor.execute("DELETE FROM strategies WHERE strategy_id = ?", (strategy_id,))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Strategy deleted successfully",
                "strategy_id": strategy_id
            }
            
        except Exception as e:
            self.logger.error(f"Delete strategy failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _verify_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a strategy based on performance thresholds."""
        try:
            strategy_id = data.get("strategy_id", "")
            
            if not strategy_id:
                return {"success": False, "error": "Strategy ID is required"}
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get strategy
            cursor.execute("SELECT * FROM strategies WHERE strategy_id = ?", (strategy_id,))
            strategy = cursor.fetchone()
            
            if not strategy:
                conn.close()
                return {"success": False, "error": "Strategy not found"}
            
            # Get backtests for verification
            cursor.execute("SELECT * FROM strategy_backtests WHERE strategy_id = ?", (strategy_id,))
            backtests = cursor.fetchall()
            
            if not backtests:
                conn.close()
                return {"success": False, "error": "No backtests available for verification"}
            
            # Analyze performance metrics
            verification_passed = True
            verification_details = []
            
            for backtest in backtests:
                sharpe_ratio = backtest["sharpe_ratio"] or 0
                total_return = backtest["total_return"] or 0
                total_trades = backtest["total_trades"] or 0
                max_drawdown = backtest["max_drawdown"] or 0
                
                if sharpe_ratio < self.verification_thresholds["min_sharpe_ratio"]:
                    verification_passed = False
                    verification_details.append(f"Sharpe ratio {sharpe_ratio:.2f} below threshold {self.verification_thresholds['min_sharpe_ratio']}")
                
                if total_return < self.verification_thresholds["min_total_return"]:
                    verification_passed = False
                    verification_details.append(f"Total return {total_return:.2f}% below threshold {self.verification_thresholds['min_total_return']}%")
                
                if total_trades < self.verification_thresholds["min_trades"]:
                    verification_passed = False
                    verification_details.append(f"Total trades {total_trades} below threshold {self.verification_thresholds['min_trades']}")
                
                if max_drawdown < self.verification_thresholds["max_drawdown"]:
                    verification_passed = False
                    verification_details.append(f"Max drawdown {max_drawdown:.2f}% exceeds threshold {self.verification_thresholds['max_drawdown']}%")
            
            # Update verification status
            if verification_passed:
                cursor.execute("UPDATE strategies SET verified = 1 WHERE strategy_id = ?", (strategy_id,))
                conn.commit()
            
            conn.close()
            
            return {
                "success": True,
                "verified": verification_passed,
                "verification_details": verification_details,
                "thresholds": self.verification_thresholds,
                "strategy_id": strategy_id
            }
            
        except Exception as e:
            self.logger.error(f"Verify strategy failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_platform_stats(self) -> Dict[str, Any]:
        """Get platform statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total strategies
            cursor.execute("SELECT COUNT(*) FROM strategies")
            total_strategies = cursor.fetchone()[0]
            
            # Verified strategies
            cursor.execute("SELECT COUNT(*) FROM strategies WHERE verified = 1")
            verified_strategies = cursor.fetchone()[0]
            
            # Total downloads
            cursor.execute("SELECT SUM(downloads) FROM strategies")
            total_downloads = cursor.fetchone()[0] or 0
            
            # Top categories
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM strategies 
                GROUP BY category 
                ORDER BY count DESC 
                LIMIT 5
            """)
            top_categories = [{"category": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            # Top rated strategies
            cursor.execute("""
                SELECT name, author, rating, downloads 
                FROM strategies 
                ORDER BY rating DESC, downloads DESC 
                LIMIT 5
            """)
            top_rated = []
            for row in cursor.fetchall():
                top_rated.append({
                    "name": row[0],
                    "author": row[1], 
                    "rating": row[2],
                    "downloads": row[3]
                })
            
            conn.close()
            
            return {
                "success": True,
                "platform_stats": {
                    "total_strategies": total_strategies,
                    "verified_strategies": verified_strategies,
                    "total_downloads": total_downloads,
                    "verification_rate": (verified_strategies / max(total_strategies, 1)) * 100,
                    "top_categories": top_categories,
                    "top_rated_strategies": top_rated,
                    "available_categories": self.categories,
                    "risk_levels": self.risk_levels,
                    "timeframes": self.timeframes
                }
            }
            
        except Exception as e:
            self.logger.error(f"Get platform stats failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_sharing_stats(self) -> Dict[str, Any]:
        """Get strategy sharing utility statistics."""
        return {
            "strategies_shared": self.strategies_shared,
            "strategies_downloaded": self.strategies_downloaded,
            "last_operation_time": self.last_operation_time.isoformat() if self.last_operation_time else None,
            "supported_categories": self.categories,
            "risk_levels": self.risk_levels,
            "timeframes": self.timeframes,
            "verification_thresholds": self.verification_thresholds,
            "plugin_name": self.name,
            "enabled": self.config.enabled
        }