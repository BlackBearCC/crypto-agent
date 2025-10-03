# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A cryptocurrency 24/7 monitoring and trading system with intelligent AI-powered analysis. The system uses multiple AI analyst agents (technical, market, fundamental, macro analysts) coordinated by an intelligent "master brain" to provide comprehensive market analysis and trading decisions. Features Telegram integration for user control and notifications.

## Coding Standards

**Strict Requirements**:
- **No Emojis**: Never use emoji in print statements or comments
- **Minimal Comments**: Code should be self-documenting; only add comments when absolutely necessary
- **No Mock Data**: Never use simulated, fake, or placeholder data
- **Direct Error Handling**: Raise errors directly, do not suppress or fallback silently
- **Clear Naming**: Variable and function names should be clear and concise; avoid encoding implementation details in names
- **Reuse First**: Always prefer using existing interfaces and architecture before creating new ones
- **Module Imports**: Use absolute imports (e.g., `from config import Settings`) not relative imports (e.g., `from .config import Settings`)

## Architecture

### Service-Oriented Modular Design

The system follows a clean separation of concerns with distinct layers:

**Core Controller** (`crypto_monitor_controller.py`)
- Main orchestrator coordinating all services
- Lightweight coordinator following single responsibility principle
- Manages lifecycle of all components and service interactions

**Service Layer** (`services/`)
- `AnalysisService`: Coordinates multiple analyst agents
- `DataService`: Handles all data collection and caching
- `MonitoringService`: System monitoring loop and heartbeat decisions
- `FormattingService`: Output formatting utilities

**Analysis Layer** (`analysis/`)
- Multiple specialized AI analyst agents (Technical, Market, Fundamental, Macro, Chief)
- Each analyst extends `BaseAnalyst` abstract class
- `PromptManager`: Centralized prompt templates for all analysts
- `TraderAnalyst`: Trading decision maker based on research

**Data Layer** (`data/`)
- `DataCollector`: Unified data collection coordinator
- `BinanceClient`: Binance API integration for trading data
- `CoingeckoClient`: CoinGecko API for market data
- `FinancialDataClient`: Additional financial data sources

**Core Calculation** (`core/`)
- `IndicatorCalculator`: Technical indicator calculations
- `MasterBrain`: LLM-powered intelligent decision making via function calling
- Individual indicator modules: RSI, MACD, Moving Averages

**Database** (`database/`)
- `DatabaseManager`: SQLite database operations
- `models.py`: Data models (MarketData, AnalysisResult, TriggerEvent)

**Configuration** (`config/`)
- `ConfigManager`: Loads from YAML and manages dynamic config
- `Settings`: Type-safe configuration dataclasses
- `crypto_monitor_config.yaml`: Main configuration file

**Integrations** (`integrations/`)
- `TelegramIntegration`: Bot interface for user control

**Trading** (`trading/`)
- `PortfolioManager`: Trading execution and portfolio management
- `TradingClient`: Binance trading API wrapper

### Master Brain Architecture

The `MasterBrain` (`core/master_brain.py`) is the intelligent coordinator:
- Uses LLM with function calling to intelligently invoke system capabilities
- Processes user requests from Telegram or heartbeat events
- Dynamically decides which analysts/services to call based on context
- Available functions include: technical_analysis, market_sentiment_analysis, comprehensive_analysis, trading_analysis, execute_trade, etc.
- System runs in "standby mode" - only acts on explicit user commands via Telegram

### Analyst Coordination Pattern

Multi-analyst collaboration flow:
1. User request → Master Brain
2. Master Brain → Calls specific analysts via function calling
3. Technical Analyst → K-line and indicator analysis
4. Market Analyst → Sentiment and trending analysis
5. Fundamental Analyst → Coin fundamentals
6. Macro Analyst → Economic environment (daily limit)
7. Research Director → Synthesizes all analyses
8. Trader Analyst → Makes trading decisions
9. Results → Formatted and sent to user via Telegram

## Key Commands

### Running the System

```bash
# Start the monitoring system (main entry point)
python main.py

# Alternative: Run controller directly (for testing)
python crypto_monitor_controller.py

# Test Binance API connection
python test_binance_direct.py

# Switch environment configurations
python switch_env.py
```

### Environment Setup

1. Copy `.env.example` to `.env`
2. Configure API keys:
   - `BINANCE_API_KEY` and `BINANCE_API_SECRET` for trading
   - `DOUBAO_API_KEY` for AI analysis (primary)
   - `CLAUDE_API_KEY` for AI analysis (optional)
   - `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` for notifications

### Configuration

Main config: `config/crypto_monitor_config.yaml`

Key settings:
- `监控币种.主要币种`: Primary symbols to monitor (e.g., ETHUSDT, DOGEUSDT)
- `触发条件.常规分析间隔`: Heartbeat interval in seconds (default 1800 = 30 min)
- `API配置.分析师模型`: Configure which LLM model each analyst uses
- `风险管理.币种杠杆`: Per-symbol leverage settings
- `K线数据配置.获取间隔`: Data fetch interval (default 300 = 5 min)

Dynamic configuration changes are saved to preserve user adjustments made via Telegram.

## LLM Client Architecture

**Multi-Provider Support** (`llm_client.py`):
- Unified interface for Claude, Doubao (ByteDance), DeepSeek
- Model name → Endpoint ID mapping for Doubao platform
- Support for system prompt + user message separation
- Stream and non-stream response handling
- Automatic error handling and retry logic

**Model Configuration**:
Each analyst has dedicated model config in YAML:
```yaml
API配置:
  分析师模型:
    技术分析师:
      提供商: "doubao"
      模型: "doubao-1.6"
      温度: 0.3
```

## Important Patterns

### Import Handling
The codebase supports both direct execution and module imports with try-except blocks:
```python
try:
    from .module import Class  # Relative import
except ImportError:
    from crypto_monitor_project.module import Class  # Absolute import
```

### Service Initialization Order
1. Core components (config, database, indicators)
2. LLM clients
3. Service layer (data → analysis → formatting → monitoring)
4. Master brain (needs controller reference)
5. Integrations (Telegram)

### Error Handling Philosophy
- All service methods return results, never crash
- Failed API calls fall back to backup models (see 兜底模型 config)
- Comprehensive logging with try-except at service boundaries
- Telegram provides user-friendly error messages

### Data Flow
1. `DataService` fetches K-line data from Binance (cached)
2. `IndicatorCalculator` computes technical indicators
3. `MonitoringService` checks trigger conditions (RSI extremes, MACD crossovers, heartbeat intervals)
4. `MasterBrain` makes intelligent decisions via LLM function calling
5. Analysts perform specialized analysis when triggered
6. Results saved to database and sent via Telegram

## Database Schema

SQLite database with three main tables:
- `market_data`: Price, RSI, MACD, volume, moving averages (30 day retention)
- `analysis_results`: Analyst outputs, recommendations, confidence scores
- `trigger_events`: Special conditions that triggered analysis (RSI extremes, crossovers, stop loss/profit)

## Testing & Debugging

- Test Binance connection: `python test_binance_direct.py`
- Enable DEBUG logging: Set `日志级别: "DEBUG"` in YAML
- Check database: `database/crypto_monitor.db` (SQLite)
- Monitor Telegram responses for real-time system status
- Use `/status` command in Telegram to check system health

## Telegram Bot Commands

The system is controlled entirely via Telegram:
- `/start` - Initialize bot
- `/status` - System status
- `/analyze <SYMBOL>` - Manual analysis trigger
- `/portfolio` - View positions
- `/help` - Available commands

Master Brain understands natural language requests via LLM.

## Risk Management

**Multi-Level Controls**:
- Per-symbol leverage limits (configured in YAML 风险管理.币种杠杆)
- Maximum positions limit (default: 6)
- Single position size limit (default: 20% of capital)
- Stop loss/take profit triggers (5%/10% defaults)
- Trader work status detection (prevents overtrading)

## Important Notes

- System runs in **standby mode** by default - only responds to Telegram commands
- Heartbeat monitoring collects data but doesn't auto-trade
- Macro analysis limited to once daily (expensive operation)
- All trading requires user confirmation via Telegram
- API rate limits handled with caching and request throttling
- Supports both testnet and production Binance trading
