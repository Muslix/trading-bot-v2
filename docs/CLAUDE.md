# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a crypto trading bot project implementing three advanced Python concepts for high-performance trading:
- **Multiprocessing**: Parallel calculation of Sharpe ratios, volatility, correlations for 50-100 cryptocurrencies
- **Async/IO**: Simultaneous price fetching from multiple exchanges (Binance, Coinbase, Kraken)
- **Decorators**: Clean logging, performance tracking, and error handling

## Core Architecture

```
crypto_trading_bot.py
├── Module 1: Portfolio Analyzer (Multiprocessing)
├── Module 2: Price Monitor (Async/IO) 
├── Module 3: Signal Generator (Decorators)
└── Main Loop: Integration of all modules
```

## Technical Implementation Details

### 1. Multiprocessing for Portfolio Analysis
- Use `multiprocessing.Pool` to distribute calculations across all CPU cores
- Functions should follow pattern: `calculate_sharp_ratio(ticker)` returning `(ticker, ratio)`
- Expected performance: Reduce analysis time from 10 minutes to 2 minutes for 100+ assets
- Sequential vs parallel comparison shows ~30-40% speed improvement

### 2. Async/IO for Price Monitoring
- Use `asyncio.gather()` to fetch prices from multiple exchanges simultaneously
- Functions must be declared as `async def` and use `await` for API calls
- CCXT library for exchange connections: `exchange.fetch_ticker(symbol)`
- Expected performance: 140% faster than sequential API calls
- Pattern: Create coroutines list, then `await asyncio.gather(*tasks)`

### 3. Decorators for Logging and Performance
- `@log_performance` decorator for automatic timing and error handling
- Clean, consistent logging without cluttering function logic
- Track execution time, success/failure status, and handle exceptions
- Apply to all API calls and calculation functions

## Development Phases

**SCHRITT 1: Crypto Screener**
- Multi-exchange price comparison (Async/IO)
- Parallel technical analysis for multiple coins (Multiprocessing)
- Clean logging of all actions (Decorators)

**SCHRITT 2: Arbitrage Bot**
- Automatic price monitoring
- Profit calculations
- Alert system for price differences > 1%

**SCHRITT 3: Backtesting Engine**
- Historical data processing in parallel
- Multiple strategy testing simultaneously
- Performance tracking

## Key Libraries and Tools

- **Core**: `yfinance`, `pandas`, `numpy`, `ccxt`
- **Concurrency**: `multiprocessing.Pool`, `asyncio`, `time`
- **Expected exchanges**: Binance, Coinbase, Kraken
- **Performance focus**: Time measurement and comparison between sequential vs parallel approaches

## Performance Benchmarks
- Portfolio analysis: 10 minutes → 2 minutes (80% reduction)
- Multi-exchange price fetching: 140% faster with async/IO
- Clean code with decorators vs manual logging