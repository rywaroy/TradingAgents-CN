#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动TradingAgents-CN股票分析HTTP服务
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import uvicorn


def main() -> None:
    """启动FastAPI服务"""
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env", override=True)

    host = os.getenv("TRADINGAGENTS_API_HOST", "0.0.0.0")
    port = int(os.getenv("TRADINGAGENTS_API_PORT", "8080"))
    reload_enabled = os.getenv("TRADINGAGENTS_API_RELOAD", "false").lower() == "true"

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload_enabled,
        log_level=os.getenv("TRADINGAGENTS_API_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from tradingagents.api.analysis_service import app  # noqa: E402
    main()
