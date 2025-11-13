# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TradingAgents-CN** is a Chinese-enhanced multi-agent LLM financial trading decision framework. It's built on FastAPI (backend) + Vue 3 (frontend) architecture with MongoDB/Redis for data persistence. The project supports A-share, Hong Kong, and US stock markets with comprehensive AI-powered analysis capabilities.

**Version:** 1.0.0-preview
**Base Project:** [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)
**Python Version:** 3.10+

## Architecture Overview

### Multi-Agent System
The core trading system uses a **five-team multi-agent workflow**:
1. **Analyst Team** - Market/Social/News/Fundamentals analysts gather data
2. **Research Team** - Bull/Bear researchers debate with Research Manager arbitration
3. **Trading Team** - Trader formulates investment plans
4. **Risk Management Team** - Risky/Neutral/Safe analysts evaluate risks
5. **Portfolio Management** - Portfolio Manager makes final decisions

### Technology Stack

**Backend (app/):**
- FastAPI + Uvicorn for RESTful API
- MongoDB (motor/pymongo) for document storage
- Redis for caching and real-time data
- APScheduler for scheduled tasks
- SSE + WebSocket for real-time notifications
- LangChain/LangGraph for AI agent orchestration

**Frontend (frontend/):**
- Vue 3 + Vite + Element Plus
- Modern SPA architecture

**Core AI Library (tradingagents/):**
- Multi-agent framework built on LangGraph
- Support for multiple LLM providers (Google, OpenAI, Anthropic, DashScope, DeepSeek, etc.)
- Financial data integration (AKShare, Tushare, BaoStock, yfinance)

**CLI (cli/):**
- Typer-based interactive CLI
- Rich terminal UI with live updates
- Full analysis workflow support

## Development Commands

### Backend Development

```bash
# Start FastAPI backend (development mode with auto-reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the app directly
python app/main.py

# Run with specific log level
python -m uvicorn app.main:app --log-level debug
```

### CLI Development

```bash
# Interactive stock analysis
python -m cli.main analyze
# Or simply:
python -m cli.main

# View configuration
python -m cli.main config

# List examples
python -m cli.main examples

# Check version
python -m cli.main version

# Data directory configuration
python -m cli.main data-config --show
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev        # Development server
npm run build      # Production build
npm run preview    # Preview production build
```

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python tests/test_chinese_output.py

# Run integration test
python tests/integration/test_dashscope_integration.py

# Quick API connectivity test
python tests/test_all_apis.py
```

### Docker Deployment

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Build multi-architecture images
./scripts/build-multiarch.sh

# Build for specific architecture
./scripts/build-amd64.sh     # x86_64
./scripts/build-arm64.sh     # ARM64/Apple Silicon
```

## Project Structure

```
TradingAgents-CN/
├── app/                    # FastAPI backend (proprietary)
│   ├── main.py            # Application entry point
│   ├── core/              # Core configuration and database
│   ├── routers/           # API route handlers
│   ├── services/          # Business logic services
│   ├── models/            # Pydantic data models
│   ├── middleware/        # Custom middleware
│   └── worker/            # Background workers for data sync
│
├── tradingagents/         # Core AI library (Apache 2.0)
│   ├── agents/            # Multi-agent implementations
│   ├── graph/             # LangGraph workflow definitions
│   ├── dataflows/         # Financial data acquisition
│   ├── llm_adapters/      # LLM provider adapters
│   ├── tools/             # Agent tools
│   └── utils/             # Shared utilities
│
├── cli/                   # Command-line interface
│   ├── main.py            # CLI entry point
│   ├── utils.py           # CLI utilities
│   └── models.py          # CLI data models
│
├── frontend/              # Vue 3 frontend (proprietary)
│   ├── src/
│   │   ├── views/         # Page components
│   │   ├── components/    # Reusable components
│   │   ├── api/           # API client
│   │   └── stores/        # Pinia state management
│   └── public/            # Static assets
│
├── tests/                 # Test suite
│   ├── integration/       # Integration tests
│   ├── test_*.py          # Unit/functional tests
│   └── debug_*.py         # Debugging utilities
│
├── scripts/               # Automation scripts
│   ├── build-*.sh         # Docker build scripts
│   └── *_sync_*.py        # Data synchronization scripts
│
├── config/                # Configuration files
├── docs/                  # Documentation
├── examples/              # Example programs
└── reports/               # Generated analysis reports
```

## Configuration

### Environment Variables

The project uses `.env` file for configuration. Key variables:

**Database:**
- `MONGODB_HOST`, `MONGODB_PORT`, `MONGODB_DATABASE`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`

**LLM Providers:**
- `GOOGLE_API_KEY` - Google AI (Gemini)
- `OPENAI_API_KEY` - OpenAI
- `ANTHROPIC_API_KEY` - Anthropic (Claude)
- `DASHSCOPE_API_KEY` - Alibaba DashScope (阿里百炼)
- `DEEPSEEK_API_KEY` - DeepSeek

**Data Sources:**
- `TUSHARE_TOKEN` - Tushare financial data
- `FINNHUB_API_KEY` - Finnhub market data
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` - Reddit social sentiment

**Proxy (if needed):**
- `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`

**Application:**
- `HOST`, `PORT` - Server binding
- `DEBUG` - Enable debug mode
- `TIMEZONE` - Timezone for scheduling (default: Asia/Shanghai)

### Dynamic Configuration

The system supports runtime configuration through:
1. **Web UI Configuration** - `/api/config/*` endpoints for LLM and data source management
2. **Database Configuration** - Settings stored in MongoDB with priority over env vars
3. **Config Bridge** - `app/core/config_bridge.py` syncs database config to environment

## Core Workflows

### Stock Analysis Flow

1. **Data Validation** - Validates stock code and pre-fetches data
2. **Data Collection** - Gathers historical prices, fundamentals, news, sentiment
3. **Analyst Team** - Multiple analysts analyze different aspects in parallel
4. **Research Team** - Bull/Bear debate with manager arbitration (configurable debate rounds)
5. **Trading Team** - Formulates concrete investment plan
6. **Risk Assessment** - Three risk analysts evaluate from different perspectives
7. **Final Decision** - Portfolio manager makes final trading decision
8. **Report Generation** - Comprehensive markdown/PDF/Word reports

### Data Synchronization

Background workers handle scheduled data synchronization:
- **Stock Basics** - Daily sync at 06:30 (configurable via CRON)
- **Real-time Quotes** - Every N seconds during trading hours
- **Historical Data** - Incremental daily updates
- **Financial Data** - Quarterly sync
- **News Data** - Multiple sources aggregated

Configure via `.env`:
```bash
SYNC_STOCK_BASICS_ENABLED=true
SYNC_STOCK_BASICS_CRON="0 6 * * *"
QUOTES_INGEST_ENABLED=true
QUOTES_INGEST_INTERVAL_SECONDS=10
```

## Important Implementation Details

### LLM Provider Integration

When adding or modifying LLM providers:

1. **Adapter Location:** `tradingagents/llm_adapters/`
2. **Factory Pattern:** Use `create_llm_by_provider()` in `tradingagents/graph/trading_graph.py`
3. **API Key Priority:** Database config > Environment variables
4. **Base URL Support:** Allow custom endpoints for OpenAI-compatible APIs

Example pattern:
```python
if provider.lower() == "new_provider":
    api_key = api_key or os.getenv('NEW_PROVIDER_API_KEY')
    return ChatNewProvider(
        model=model,
        api_key=api_key,
        base_url=backend_url if backend_url else None,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )
```

### Data Source Management

The system supports **multi-source data with automatic fallback**:
- Priority order: Tushare > AKShare > BaoStock (configurable)
- Automatic source switching on failure
- Unified data format across sources

Key files:
- `app/services/multi_source_basics_sync_service.py` - Multi-source orchestration
- `tradingagents/dataflows/data_source_manager.py` - Data source abstraction
- `app/worker/*_sync_service.py` - Individual source implementations

### Agent State Management

The system uses **typed state classes** for agent communication:
- `AgentState` - Main state shared across all agents
- `InvestDebateState` - Research team debate state
- `RiskDebateState` - Risk management debate state

Located in: `tradingagents/agents/utils/agent_states.py`

### Logging System

**Unified logging** via `tradingagents/utils/logging_manager.py`:
- Separate loggers for different modules (agents, dataflows, cli, webapi, worker)
- File rotation and compression
- CLI mode disables console output to keep UI clean

When adding logging:
```python
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('module_name')  # Use appropriate module name
```

## Testing Strategy

### Test Categories

1. **Integration Tests** (`tests/integration/`) - End-to-end workflows
2. **API Tests** (`tests/test_*_apis.py`) - External API connectivity
3. **Performance Tests** (`tests/test_redis_performance.py`) - System benchmarks
4. **Debug Tools** (`tests/debug_*.py`, `tests/diagnose_*.py`) - Troubleshooting

### Running Single Test

```bash
# Direct execution
python tests/test_chinese_output.py

# Using pytest
pytest tests/test_chinese_output.py -v
```

### Test Requirements

- Set required API keys in `.env`
- MongoDB and Redis must be running for integration tests
- Use `load_dotenv()` in test files for env var loading

## Common Tasks

### Adding a New Agent

1. Create agent class in `tradingagents/agents/`
2. Define agent node function
3. Add to graph in `tradingagents/graph/trading_graph.py`
4. Update `AgentState` if new state fields needed
5. Add agent status tracking in CLI (`cli/main.py` if applicable)

### Adding a New Data Source

1. Implement in `tradingagents/dataflows/`
2. Follow the interface pattern from existing sources
3. Add sync service in `app/worker/` for scheduled updates
4. Register in `MultiSourceBasicsSyncService`
5. Add configuration options in `app/core/config.py`

### Adding a New API Endpoint

1. Create router in `app/routers/`
2. Implement service logic in `app/services/`
3. Define Pydantic models in `app/models/`
4. Register router in `app/main.py`
5. Add frontend API client in `frontend/src/api/`

### Modifying Agent Workflow

The main workflow is defined in `tradingagents/graph/trading_graph.py`:
- `GraphSetup.create()` - Builds the LangGraph state graph
- `ConditionalLogic` - Handles workflow branching
- `Propagator.propagate()` - Executes the workflow

Debate rounds are configurable:
- `max_debate_rounds` - Research team debate iterations
- `max_risk_discuss_rounds` - Risk team discussion iterations

## Data and Results

### Directory Structure

```bash
# Default locations (configurable)
~/Documents/TradingAgents/data/          # Stock data cache
<project_root>/reports/                  # Analysis reports
<project_root>/logs/                     # Application logs
```

### Report Formats

Analysis reports can be exported in:
- **Markdown** (.md) - Default, human-readable
- **Word** (.docx) - MS Word document
- **PDF** (.pdf) - Requires wkhtmltopdf installation

### Managing Data Directories

```bash
# View current configuration
python -m cli.main data-config --show

# Set custom data directory
python -m cli.main data-config --set /path/to/data

# Reset to defaults
python -m cli.main data-config --reset
```

## Troubleshooting

### Common Issues

**MongoDB Connection Failures:**
- Check `MONGODB_HOST` and `MONGODB_PORT` in `.env`
- Ensure MongoDB service is running
- Verify network connectivity

**LLM API Errors:**
- Verify API keys are set correctly
- Check `backend_url` for custom endpoints
- Review rate limits and quotas
- Enable debug logging: `DEBUG=true` in `.env`

**Data Sync Issues:**
- Check data source API credentials
- Review scheduler logs in `logs/worker.log`
- Verify CRON expressions in configuration
- Use `python scripts/akshare_force_sync_all.py` for manual sync

**CLI Display Issues:**
- Ensure terminal supports Rich library rendering
- Check terminal size (minimum 80x24 recommended)
- Disable problematic plugins if using terminal multiplexers

### Debug Mode

Enable comprehensive logging:
```bash
DEBUG=true python app/main.py
```

View specific log modules:
```bash
tail -f logs/agents.log      # AI agent operations
tail -f logs/dataflows.log   # Data acquisition
tail -f logs/webapi.log      # API requests
tail -f logs/worker.log      # Background tasks
```

## Market-Specific Notes

### A-Share (中国A股)
- Use 6-digit stock codes (e.g., "600036", "000001")
- Primary data sources: Tushare, AKShare, BaoStock
- Trading hours: 09:30-11:30, 13:00-15:00 (UTC+8)

### Hong Kong Stock (港股)
- Format: "####.HK" (e.g., "0700.HK", "09988.HK")
- Data source: Yahoo Finance (yfinance)
- On-demand fetching with caching

### US Stock (美股)
- Use standard ticker symbols (e.g., "AAPL", "NVDA", "SPY")
- Data source: Yahoo Finance, Finnhub
- On-demand fetching with caching

## License

**Hybrid License Model:**
- Core AI library (`tradingagents/`) - **Apache 2.0**
- Backend (`app/`) and Frontend (`frontend/`) - **Proprietary** (commercial license required)

For commercial use of proprietary components, contact: hsliup@163.com

## Additional Resources

- **Documentation:** `docs/` directory
- **Examples:** `examples/` directory
- **Changelog:** `docs/releases/CHANGELOG.md`
- **WeChat Public Account:** TradingAgents-CN (中文支持)
- **Original Project:** [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)
