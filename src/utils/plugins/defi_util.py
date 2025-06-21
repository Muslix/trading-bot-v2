"""
DeFi Utility Plugin - decentralized finance integration and analysis
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time

from ..base import UtilPlugin, UtilConfig


class DeFiUtil(UtilPlugin):
    """
    DeFi utility plugin for decentralized finance operations.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.defi_operations = 0
        self.last_operation_time = None
        
        # DeFi protocol endpoints and configurations
        self.protocols = {
            "uniswap_v3": {
                "name": "Uniswap V3",
                "api_url": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
                "chain": "ethereum",
                "fee_tiers": [0.05, 0.3, 1.0],  # 0.05%, 0.3%, 1%
                "supported": True
            },
            "pancakeswap": {
                "name": "PancakeSwap",
                "api_url": "https://api.thegraph.com/subgraphs/name/pancakeswap/exchange",
                "chain": "binance_smart_chain",
                "fee_tiers": [0.25],  # 0.25%
                "supported": True
            },
            "sushiswap": {
                "name": "SushiSwap",
                "api_url": "https://api.thegraph.com/subgraphs/name/sushiswap/exchange",
                "chain": "ethereum",
                "fee_tiers": [0.3],  # 0.3%
                "supported": True
            },
            "curve": {
                "name": "Curve Finance",
                "api_url": "https://api.curve.fi/api/getPools/ethereum/main",
                "chain": "ethereum",
                "fee_tiers": [0.04, 0.04],  # Stable pools typically 0.04%
                "supported": True
            },
            "balancer": {
                "name": "Balancer",
                "api_url": "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2",
                "chain": "ethereum",
                "fee_tiers": [0.1, 0.3, 1.0],  # Variable fees
                "supported": True
            }
        }
        
        # Token mappings and addresses
        self.token_addresses = {
            "ethereum": {
                "USDC": "0xa0b86a33e6c6cd4c8b6b35fe7d4ab9b49af82d7c",
                "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                "WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                "DAI": "0x6b175474e89094c44da98b954eedeac495271d0f"
            },
            "binance_smart_chain": {
                "USDC": "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", 
                "USDT": "0x55d398326f99059ff775485246999027b3197955",
                "WBNB": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
                "BTCB": "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c",
                "BUSD": "0xe9e7cea3dedca5984780bafc599bd69add087d56"
            }
        }
        
        # DeFi yield farming pools
        self.yield_pools = {
            "uniswap_v3": [
                {"pair": "USDC/WETH", "fee": 0.3, "apy_range": [5, 15]},
                {"pair": "WBTC/WETH", "fee": 0.3, "apy_range": [8, 20]},
                {"pair": "USDC/USDT", "fee": 0.05, "apy_range": [2, 8]}
            ],
            "curve": [
                {"pair": "3pool", "fee": 0.04, "apy_range": [3, 10]},
                {"pair": "stETH", "fee": 0.04, "apy_range": [4, 12]}
            ]
        }
    
    async def _initialize_util(self) -> bool:
        """Initialize DeFi utility."""
        try:
            # Initialize HTTP session for DeFi API calls
            timeout_seconds = getattr(self.config, 'timeout_seconds', 60)
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout_seconds)
            )
            
            self.logger.info("DeFi utility initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize DeFi utility: {e}")
            return False
    
    async def _cleanup_util(self) -> None:
        """Clean up DeFi utility resources."""
        if hasattr(self, 'session') and self.session:
            await self.session.close()
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process DeFi operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "get_pools")
        
        if action == "get_pools":
            return await self._get_liquidity_pools(data)
        elif action == "find_arbitrage":
            return await self._find_defi_arbitrage(data)
        elif action == "calculate_yield":
            return await self._calculate_yield_opportunities(data)
        elif action == "get_token_price":
            return await self._get_token_price_defi(data)
        elif action == "simulate_swap":
            return await self._simulate_token_swap(data)
        elif action == "get_pool_info":
            return await self._get_pool_detailed_info(data)
        elif action == "analyze_impermanent_loss":
            return await self._analyze_impermanent_loss(data)
        elif action == "get_trending_pools":
            return await self._get_trending_pools(data)
        elif action == "get_protocol_stats":
            return self._get_protocol_stats()
        elif action == "get_stats":
            return self._get_defi_stats()
        else:
            raise ValueError(f"Unknown DeFi action: {action}")
    
    async def _get_liquidity_pools(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get liquidity pools from various DeFi protocols."""
        operation_start = datetime.now()
        protocols = data.get("protocols", list(self.protocols.keys()))
        token_pair = data.get("token_pair", "USDC/WETH")
        min_tvl = data.get("min_tvl", 1000000)
        
        self.logger.info(f"🏊 Starting DeFi pools lookup for {token_pair}")
        self.logger.info(f"   Protocols: {protocols}")
        self.logger.info(f"   Min TVL: ${min_tvl:,}")
        
        try:
            pools_data = {}
            
            for protocol in protocols:
                if protocol not in self.protocols or not self.protocols[protocol]["supported"]:
                    self.logger.warning(f"   ⚠️ Protocol {protocol} not supported, skipping")
                    continue
                
                protocol_start = datetime.now()
                self.logger.info(f"   🔍 Fetching pools from {protocol}...")
                
                try:
                    pools = await self._fetch_pools_from_protocol(protocol, token_pair, min_tvl)
                    pools_data[protocol] = pools
                    protocol_duration = (datetime.now() - protocol_start).total_seconds()
                    
                    if isinstance(pools, list):
                        self.logger.info(f"   ✅ {protocol}: {len(pools)} pools found ({protocol_duration:.2f}s)")
                        for pool in pools[:2]:  # Log first 2 pools
                            tvl = pool.get('tvl', 0)
                            apy = pool.get('apy', 0)
                            self.logger.debug(f"      📊 Pool: {pool.get('pool_id', 'unknown')} - TVL: ${tvl:,} - APY: {apy:.1f}%")
                    else:
                        self.logger.warning(f"   ⚠️ {protocol}: Unexpected response format")
                        
                except Exception as e:
                    protocol_duration = (datetime.now() - protocol_start).total_seconds()
                    self.logger.error(f"   ❌ {protocol} failed after {protocol_duration:.2f}s: {e}")
                    pools_data[protocol] = {"error": str(e)}
            
            operation_duration = (datetime.now() - operation_start).total_seconds()
            total_pools = sum(len(pools) if isinstance(pools, list) else 0 for pools in pools_data.values())
            
            self.defi_operations += 1
            self.last_operation_time = datetime.now()
            
            self.logger.info(f"🏊 DeFi pools lookup completed in {operation_duration:.2f}s")
            self.logger.info(f"   📊 Total pools found: {total_pools}")
            self.logger.info(f"   ✅ Successful protocols: {len([p for p in pools_data.values() if isinstance(p, list)])}/{len(protocols)}")
            
            return {
                "success": True,
                "pools": pools_data,
                "token_pair": token_pair,
                "min_tvl": min_tvl,
                "protocols_checked": len(protocols),
                "operation_duration_seconds": operation_duration,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"DeFi pools lookup failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _fetch_pools_from_protocol(self, protocol: str, token_pair: str, min_tvl: float) -> List[Dict]:
        """Fetch pools from a specific DeFi protocol."""
        # Simulate pool data for different protocols
        base_token, quote_token = token_pair.split("/")
        
        if protocol == "uniswap_v3":
            return [
                {
                    "pool_id": f"uniswap_v3_{base_token}_{quote_token}_3000",
                    "token0": base_token,
                    "token1": quote_token,
                    "fee_tier": 0.3,
                    "tvl": 12500000,
                    "volume_24h": 8900000,
                    "apy": 12.5,
                    "liquidity": 15600000,
                    "price_range": {"min": 0.98, "max": 1.02}
                },
                {
                    "pool_id": f"uniswap_v3_{base_token}_{quote_token}_500",
                    "token0": base_token,
                    "token1": quote_token,
                    "fee_tier": 0.05,
                    "tvl": 8900000,
                    "volume_24h": 5600000,
                    "apy": 8.2,
                    "liquidity": 9800000,
                    "price_range": {"min": 0.99, "max": 1.01}
                }
            ]
        
        elif protocol == "pancakeswap":
            return [
                {
                    "pool_id": f"pancakeswap_{base_token}_{quote_token}",
                    "token0": base_token,
                    "token1": quote_token,
                    "fee_tier": 0.25,
                    "tvl": 5600000,
                    "volume_24h": 3400000,
                    "apy": 15.8,
                    "liquidity": 6200000,
                    "chain": "bsc"
                }
            ]
        
        elif protocol == "curve":
            if base_token in ["USDC", "USDT", "DAI"]:
                return [
                    {
                        "pool_id": "curve_3pool",
                        "token0": "USDC",
                        "token1": "USDT",
                        "token2": "DAI",
                        "fee_tier": 0.04,
                        "tvl": 890000000,
                        "volume_24h": 45000000,
                        "apy": 6.8,
                        "liquidity": 920000000,
                        "stable_pool": True
                    }
                ]
        
        return []
    
    async def _find_defi_arbitrage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Find arbitrage opportunities across DeFi protocols."""
        operation_start = datetime.now()
        token_pair = data.get("token_pair", "USDC/WETH")
        amount = data.get("amount", 10000)
        min_profit = data.get("min_profit_percentage", 0.5)
        
        self.logger.info(f"💰 Starting DeFi arbitrage search for {token_pair}")
        self.logger.info(f"   Amount: ${amount:,}")
        self.logger.info(f"   Min profit: {min_profit}%")
        
        try:
            
            # Get pools from multiple protocols
            self.logger.info(f"   🔍 Fetching pools for arbitrage analysis...")
            pools_result = await self._get_liquidity_pools({
                "token_pair": token_pair,
                "protocols": ["uniswap_v3", "pancakeswap", "sushiswap"],
                "min_tvl": 100000
            })
            
            if not pools_result.get("success"):
                self.logger.error(f"   ❌ Failed to fetch pools for arbitrage")
                return {"success": False, "error": "Failed to fetch pools"}
            
            self.logger.info(f"   ✅ Pools fetched, analyzing prices...")
            
            opportunities = []
            pools = pools_result["pools"]
            
            # Compare prices across protocols
            protocol_prices = {}
            for protocol, pool_list in pools.items():
                if isinstance(pool_list, list) and pool_list:
                    # Use first pool's implied price
                    pool = pool_list[0]
                    if "error" not in pool:
                        # Simulate price calculation
                        simulated_price = 1.0 + (hash(protocol) % 100) / 10000
                        protocol_prices[protocol] = {
                            "price": simulated_price,
                            "pool": pool,
                            "liquidity": pool.get("liquidity", 0)
                        }
                        self.logger.debug(f"      📊 {protocol}: Price=${simulated_price:.6f}, Liquidity=${pool.get('liquidity', 0):,}")
                    else:
                        self.logger.warning(f"      ⚠️ {protocol}: Pool has error, skipping")
            
            # Find arbitrage opportunities
            if len(protocol_prices) >= 2:
                protocols = list(protocol_prices.keys())
                for i in range(len(protocols)):
                    for j in range(i + 1, len(protocols)):
                        protocol_a = protocols[i]
                        protocol_b = protocols[j]
                        
                        price_a = protocol_prices[protocol_a]["price"]
                        price_b = protocol_prices[protocol_b]["price"]
                        
                        if price_a < price_b:
                            profit_pct = ((price_b - price_a) / price_a) * 100
                            if profit_pct >= min_profit:
                                opportunities.append({
                                    "buy_protocol": protocol_a,
                                    "sell_protocol": protocol_b,
                                    "buy_price": price_a,
                                    "sell_price": price_b,
                                    "profit_percentage": profit_pct,
                                    "estimated_profit": amount * (profit_pct / 100),
                                    "liquidity_check": min(
                                        protocol_prices[protocol_a]["liquidity"],
                                        protocol_prices[protocol_b]["liquidity"]
                                    ) > amount,
                                    "gas_estimate": self._estimate_gas_costs(protocol_a, protocol_b),
                                    "token_pair": token_pair
                                })
            
            self.defi_operations += 1
            self.last_operation_time = datetime.now()
            
            return {
                "success": True,
                "opportunities": opportunities,
                "token_pair": token_pair,
                "amount": amount,
                "protocols_checked": len(protocol_prices),
                "total_opportunities": len(opportunities),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"DeFi arbitrage search failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _estimate_gas_costs(self, protocol_a: str, protocol_b: str) -> Dict[str, Any]:
        """Estimate gas costs for arbitrage transaction."""
        # Simplified gas estimation
        base_gas = {
            "uniswap_v3": 150000,
            "pancakeswap": 120000,
            "sushiswap": 130000,
            "curve": 200000,
            "balancer": 180000
        }
        
        total_gas = base_gas.get(protocol_a, 150000) + base_gas.get(protocol_b, 150000)
        
        # Estimate costs (assuming 20 gwei gas price for ETH, 5 gwei for BSC)
        eth_gas_price = 20e-9  # 20 gwei in ETH
        bsc_gas_price = 5e-9   # 5 gwei in BNB
        
        # Simplified - assume ETH mainnet
        gas_cost_eth = total_gas * eth_gas_price
        gas_cost_usd = gas_cost_eth * 2500  # Assume $2500 ETH price
        
        return {
            "total_gas": total_gas,
            "gas_cost_eth": gas_cost_eth,
            "gas_cost_usd": gas_cost_usd,
            "profitable_if_above": gas_cost_usd * 2  # Need 2x gas cost for profitability
        }
    
    async def _calculate_yield_opportunities(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate yield farming opportunities."""
        try:
            protocols = data.get("protocols", ["uniswap_v3", "curve", "pancakeswap"])
            min_apy = data.get("min_apy", 5.0)
            risk_tolerance = data.get("risk_tolerance", "medium")  # low, medium, high
            investment_amount = data.get("investment_amount", 50000)
            
            yield_opportunities = []
            
            for protocol in protocols:
                if protocol in self.yield_pools:
                    for pool in self.yield_pools[protocol]:
                        # Calculate estimated APY based on current conditions
                        base_apy = sum(pool["apy_range"]) / 2
                        
                        # Adjust APY based on risk tolerance
                        if risk_tolerance == "low":
                            estimated_apy = base_apy * 0.8  # Conservative estimate
                        elif risk_tolerance == "high":
                            estimated_apy = base_apy * 1.2  # Optimistic estimate
                        else:
                            estimated_apy = base_apy
                        
                        if estimated_apy >= min_apy:
                            annual_yield = investment_amount * (estimated_apy / 100)
                            monthly_yield = annual_yield / 12
                            
                            # Calculate impermanent loss risk
                            il_risk = self._calculate_il_risk(pool["pair"], risk_tolerance)
                            
                            yield_opportunities.append({
                                "protocol": protocol,
                                "pool": pool["pair"],
                                "estimated_apy": estimated_apy,
                                "fee_tier": pool["fee"],
                                "annual_yield_usd": annual_yield,
                                "monthly_yield_usd": monthly_yield,
                                "impermanent_loss_risk": il_risk,
                                "investment_amount": investment_amount,
                                "risk_score": self._calculate_risk_score(protocol, pool, estimated_apy),
                                "recommendation": self._get_yield_recommendation(estimated_apy, il_risk)
                            })
            
            # Sort by APY
            yield_opportunities.sort(key=lambda x: x["estimated_apy"], reverse=True)
            
            self.defi_operations += 1
            self.last_operation_time = datetime.now()
            
            return {
                "success": True,
                "yield_opportunities": yield_opportunities,
                "total_opportunities": len(yield_opportunities),
                "min_apy": min_apy,
                "risk_tolerance": risk_tolerance,
                "investment_amount": investment_amount,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Yield calculation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_il_risk(self, pair: str, risk_tolerance: str) -> str:
        """Calculate impermanent loss risk for a trading pair."""
        # Stable pairs have low IL risk
        stable_pairs = ["USDC/USDT", "USDC/DAI", "USDT/DAI", "3pool"]
        
        if any(stable in pair for stable in stable_pairs):
            return "very_low"
        
        # Correlated assets have medium IL risk
        correlated_pairs = ["WBTC/WETH", "stETH/WETH"]
        if any(corr in pair for corr in correlated_pairs):
            return "medium"
        
        # Uncorrelated assets have high IL risk
        return "high"
    
    def _calculate_risk_score(self, protocol: str, pool: Dict, apy: float) -> float:
        """Calculate overall risk score (1-10, 10 being highest risk)."""
        risk_score = 5.0  # Base risk
        
        # Protocol risk
        protocol_risk = {
            "curve": 2.0,      # Low risk - battle tested
            "uniswap_v3": 3.0, # Medium-low risk
            "sushiswap": 4.0,  # Medium risk
            "pancakeswap": 5.0, # Medium-high risk
            "balancer": 4.0    # Medium risk
        }
        
        risk_score += protocol_risk.get(protocol, 5.0) - 5.0
        
        # APY risk - very high APY usually means higher risk
        if apy > 50:
            risk_score += 3.0
        elif apy > 25:
            risk_score += 2.0
        elif apy > 15:
            risk_score += 1.0
        
        # Pool type risk
        if "stable" in pool.get("pair", "").lower():
            risk_score -= 1.0
        
        return max(1.0, min(10.0, risk_score))
    
    def _get_yield_recommendation(self, apy: float, il_risk: str) -> str:
        """Get yield farming recommendation."""
        if il_risk == "very_low" and apy >= 5:
            return "highly_recommended"
        elif il_risk == "low" and apy >= 8:
            return "recommended"
        elif il_risk == "medium" and apy >= 12:
            return "consider_with_caution"
        elif il_risk == "high":
            return "high_risk_high_reward"
        else:
            return "not_recommended"
    
    async def _get_token_price_defi(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get token price from DeFi protocols."""
        try:
            token_symbol = data.get("token", "WETH")
            vs_token = data.get("vs_token", "USDC")
            protocols = data.get("protocols", ["uniswap_v3", "sushiswap"])
            
            token_prices = {}
            
            for protocol in protocols:
                # Simulate price fetching
                if protocol in self.protocols:
                    # Mock price with some variation
                    base_price = 2500.0 if token_symbol == "WETH" else 1.0
                    variation = (hash(protocol + token_symbol) % 200 - 100) / 10000  # ±1%
                    price = base_price * (1 + variation)
                    
                    token_prices[protocol] = {
                        "price": price,
                        "liquidity": 10000000 + (hash(protocol) % 5000000),
                        "volume_24h": 5000000 + (hash(protocol) % 2000000),
                        "last_updated": datetime.now().isoformat()
                    }
            
            # Calculate average price
            prices = [data["price"] for data in token_prices.values()]
            avg_price = sum(prices) / len(prices) if prices else 0
            
            self.defi_operations += 1
            self.last_operation_time = datetime.now()
            
            return {
                "success": True,
                "token": token_symbol,
                "vs_token": vs_token,
                "prices": token_prices,
                "average_price": avg_price,
                "price_spread": max(prices) - min(prices) if len(prices) > 1 else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"DeFi token price lookup failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_trending_pools(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get trending DeFi pools by volume/APY."""
        try:
            sort_by = data.get("sort_by", "volume")  # volume, apy, tvl
            limit = data.get("limit", 10)
            min_tvl = data.get("min_tvl", 1000000)
            
            # Mock trending pools data
            trending_pools = [
                {
                    "protocol": "uniswap_v3",
                    "pair": "WETH/USDC",
                    "fee_tier": 0.3,
                    "tvl": 125000000,
                    "volume_24h": 89000000,
                    "apy": 12.5,
                    "trend": "up",
                    "change_24h": 15.3
                },
                {
                    "protocol": "curve",
                    "pair": "stETH/WETH",
                    "fee_tier": 0.04,
                    "tvl": 890000000,
                    "volume_24h": 45000000,
                    "apy": 8.7,
                    "trend": "up",
                    "change_24h": 8.2
                },
                {
                    "protocol": "pancakeswap",
                    "pair": "BNB/BUSD",
                    "fee_tier": 0.25,
                    "tvl": 56000000,
                    "volume_24h": 34000000,
                    "apy": 18.9,
                    "trend": "down",
                    "change_24h": -5.1
                }
            ]
            
            # Filter by minimum TVL
            filtered_pools = [pool for pool in trending_pools if pool["tvl"] >= min_tvl]
            
            # Sort pools
            if sort_by == "volume":
                filtered_pools.sort(key=lambda x: x["volume_24h"], reverse=True)
            elif sort_by == "apy":
                filtered_pools.sort(key=lambda x: x["apy"], reverse=True)
            elif sort_by == "tvl":
                filtered_pools.sort(key=lambda x: x["tvl"], reverse=True)
            
            # Limit results
            result_pools = filtered_pools[:limit]
            
            self.defi_operations += 1
            self.last_operation_time = datetime.now()
            
            return {
                "success": True,
                "trending_pools": result_pools,
                "sort_by": sort_by,
                "total_pools": len(result_pools),
                "min_tvl": min_tvl,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Trending pools lookup failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_protocol_stats(self) -> Dict[str, Any]:
        """Get DeFi protocol statistics."""
        try:
            protocol_stats = {}
            
            for protocol_id, protocol_info in self.protocols.items():
                if protocol_info["supported"]:
                    # Mock protocol statistics
                    protocol_stats[protocol_id] = {
                        "name": protocol_info["name"],
                        "chain": protocol_info["chain"],
                        "total_tvl": 1000000000 + (hash(protocol_id) % 5000000000),
                        "volume_24h": 500000000 + (hash(protocol_id) % 1000000000),
                        "fee_tiers": protocol_info["fee_tiers"],
                        "active_pools": 100 + (hash(protocol_id) % 500),
                        "supported_tokens": len(self.token_addresses.get(protocol_info["chain"], {})),
                        "last_updated": datetime.now().isoformat()
                    }
            
            return {
                "success": True,
                "protocol_stats": protocol_stats,
                "total_protocols": len(protocol_stats),
                "total_tvl": sum(stats["total_tvl"] for stats in protocol_stats.values()),
                "total_volume_24h": sum(stats["volume_24h"] for stats in protocol_stats.values())
            }
            
        except Exception as e:
            self.logger.error(f"Protocol stats lookup failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_defi_stats(self) -> Dict[str, Any]:
        """Get DeFi utility statistics."""
        return {
            "defi_operations": self.defi_operations,
            "last_operation_time": self.last_operation_time.isoformat() if self.last_operation_time else None,
            "supported_protocols": list(self.protocols.keys()),
            "supported_chains": list(set(p["chain"] for p in self.protocols.values())),
            "available_features": [
                "liquidity_pools",
                "arbitrage_detection",
                "yield_farming",
                "token_prices",
                "impermanent_loss_analysis",
                "trending_pools",
                "protocol_stats"
            ],
            "token_addresses_count": sum(len(tokens) for tokens in self.token_addresses.values()),
            "yield_pools_count": sum(len(pools) for pools in self.yield_pools.values()),
            "plugin_name": self.name,
            "enabled": self.config.enabled
        }