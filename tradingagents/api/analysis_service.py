#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于FastAPI的股票分析HTTP服务
提供无鉴权的REST接口，封装现有run_stock_analysis能力
"""

from __future__ import annotations

import os
import random
import time
import uuid
from datetime import date
from typing import Any, Dict, List, Literal, Optional

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.utils.logging_manager import get_logger
from web.utils.analysis_runner import (
    collect_required_api_key_status,
    run_stock_analysis,
    validate_analysis_params,
    format_analysis_results,
)

project_root = Path(__file__).resolve().parents[2]
load_dotenv(project_root / ".env", override=True)

logger = get_logger("analysis_service")

try:
    from web.utils.report_exporter import ReportExporter

    REPORT_EXPORTER: Optional[ReportExporter] = ReportExporter()
    logger.info("✅ Markdown 报告导出器已初始化")
except Exception as exc:  # pylint: disable=broad-except
    REPORT_EXPORTER = None
    logger.warning("⚠️ Markdown 报告导出器初始化失败: %s", exc)

MarketType = Literal["A股", "港股", "美股"]
AnalystType = Literal["market", "social", "news", "fundamentals"]

DEFAULT_ANALYSTS: List[AnalystType] = ["market", "fundamentals"]


def _mask_api_key(api_key: str) -> str:
    """对敏感密钥做简单掩码，避免日志泄露"""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}***{api_key[-4:]}"


def _select_random_siliconflow_api_key() -> Optional[str]:
    """从逗号分隔（兼容分号）的SiliconFlow密钥列表中随机挑选一个"""
    raw_value = os.getenv("SILICONFLOW_API_KEY", "")
    if not raw_value:
        return None

    normalized = raw_value.replace(";", ",")
    candidates = [item.strip() for item in normalized.split(",") if item.strip()]
    if not candidates:
        return None

    chosen = random.choice(candidates)
    masked = _mask_api_key(chosen)
    if len(candidates) > 1:
        logger.info(
            "🎲 [SiliconFlow] 已在 %d 个密钥中随机选中: %s",
            len(candidates),
            masked,
        )
    else:
        logger.info("🌐 [SiliconFlow] 使用单一密钥: %s", masked)

    return chosen


class AnalysisRequest(BaseModel):
    """外部HTTP请求的参数定义"""

    stock_symbol: str = Field(..., description="待分析的股票代码")
    market_type: MarketType = Field("A股", description="市场类型")
    analysis_date: date = Field(default_factory=date.today, description="分析基准日期")
    analysts: Optional[List[AnalystType]] = Field(
        default=None, description="参与分析的分析师列表，默认使用市场+基本面组合"
    )
    research_depth: int = Field(
        3, ge=1, le=5, description="研究深度等级，1-5之间的整数，越大越深入"
    )
    llm_provider: Optional[str] = Field(
        default=None, description="可选，大模型提供商，如 dashscope/deepseek/google 等"
    )
    llm_model: Optional[str] = Field(
        default=None, description="可选，大模型名称，不填则使用默认配置"
    )


class AnalysisPayload(BaseModel):
    """返回给调用方的分析结果摘要"""

    stock_symbol: str
    market_type: MarketType
    analysis_date: str
    analysts: List[str]
    research_depth: int
    llm_provider: str
    llm_model: str
    decision: Dict[str, Any]
    state: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    success: bool
    error: Optional[str] = None
    session_id: Optional[str] = None
    is_demo: bool = False
    demo_reason: Optional[str] = None
    markdown_report: Optional[str] = None


class AnalysisResponse(BaseModel):
    """HTTP响应结构"""

    request_id: str
    duration_ms: int
    analysis: AnalysisPayload


app = FastAPI(
    title="TradingAgents-CN Analysis Service",
    description="封装股票分析能力的REST服务（无鉴权版本）",
    version="0.1.0",
)


def _ensure_environment_ready(
    llm_provider: str, override_siliconflow_api_key: Optional[str] = None
) -> None:
    """确保必要的环境变量存在，否则返回503"""
    status_snapshot = collect_required_api_key_status(
        llm_provider, override_siliconflow_api_key
    )
    for label, available in status_snapshot["statuses"].items():
        logger.info("环境变量检查: %s => %s", label, "已设置" if available else "未设置")
    if status_snapshot["missing"]:
        detail = f"运行环境缺少必要配置: {', '.join(status_snapshot['missing'])}"
        logger.error("环境校验失败: %s", detail)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail
        )


def _resolve_llm_settings(
    preferred_provider: Optional[str], preferred_model: Optional[str]
) -> Dict[str, str]:
    """合并请求参数与默认配置，确定LLM提供商与模型"""
    provider = preferred_provider or os.getenv(
        "TRADINGAGENTS_API_LLMPROVIDER", DEFAULT_CONFIG.get("llm_provider", "dashscope")
    )

    # DEFAULT_CONFIG中常见使用 deep_think_llm 作为主模型
    default_model = (
        os.getenv("TRADINGAGENTS_API_LLMMODEL")
        or DEFAULT_CONFIG.get("llm_model")
        or DEFAULT_CONFIG.get("deep_think_llm")
    )
    model = preferred_model or default_model

    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法确定大模型名称，请在请求中指定 llm_model 或配置默认值",
        )

    return {"provider": provider, "model": model}


@app.get("/health", summary="健康检查")
async def health_check() -> Dict[str, str]:
    """健康检查接口"""
    return {"status": "ok"}


@app.post(
    "/api/v1/analysis",
    response_model=AnalysisResponse,
    summary="执行股票分析",
    description="同步执行股票分析并返回结构化结果",
)
async def create_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """外部调用入口"""
    analysts = request.analysts or DEFAULT_ANALYSTS
    analysis_date_str = request.analysis_date.isoformat()

    # 基础参数校验（沿用原有逻辑）
    is_valid, errors = validate_analysis_params(
        stock_symbol=request.stock_symbol,
        analysis_date=analysis_date_str,
        analysts=analysts,
        research_depth=request.research_depth,
        market_type=request.market_type,
    )
    if not is_valid:
        logger.warning("参数校验失败: %s", errors)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors)

    llm_settings = _resolve_llm_settings(request.llm_provider, request.llm_model)
    override_siliconflow_api_key: Optional[str] = None
    if llm_settings["provider"] == "siliconflow":
        override_siliconflow_api_key = _select_random_siliconflow_api_key()
        if not override_siliconflow_api_key:
            detail = "SiliconFlow 未配置有效的 API 密钥"
            logger.error(detail)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=detail,
            )

    _ensure_environment_ready(
        llm_settings["provider"], override_siliconflow_api_key
    )

    request_id = uuid.uuid4().hex
    logger.info(
        "收到分析请求 request_id=%s symbol=%s market=%s depth=%s provider=%s model=%s",
        request_id,
        request.stock_symbol,
        request.market_type,
        request.research_depth,
        llm_settings["provider"],
        llm_settings["model"],
    )

    started_at = time.perf_counter()

    try:
        analysis_result = await run_in_threadpool(
            run_stock_analysis,
            request.stock_symbol,
            analysis_date_str,
            analysts,
            request.research_depth,
            llm_settings["provider"],
            llm_settings["model"],
            request.market_type,
            override_siliconflow_api_key=override_siliconflow_api_key,
        )
    except HTTPException:
        # 透传上层主动抛出的错误
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("执行股票分析时出现异常 request_id=%s", request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析执行失败: {exc}",
        ) from exc

    duration_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info(
        "分析完成 request_id=%s duration_ms=%s demo=%s",
        request_id,
        duration_ms,
        analysis_result.get("is_demo", False),
    )

    formatted_result = format_analysis_results(analysis_result)

    markdown_report: Optional[str] = None
    if formatted_result.get("success") and REPORT_EXPORTER:
        try:
            markdown_report = REPORT_EXPORTER.generate_markdown_report(formatted_result)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("⚠️ 生成Markdown报告失败 request_id=%s error=%s", request_id, exc)

    payload = AnalysisPayload(
        stock_symbol=formatted_result.get("stock_symbol", request.stock_symbol),
        market_type=request.market_type,
        analysis_date=formatted_result.get("analysis_date", analysis_date_str),
        analysts=formatted_result.get("analysts", analysts),
        research_depth=formatted_result.get("research_depth", request.research_depth),
        llm_provider=formatted_result.get("llm_provider", llm_settings["provider"]),
        llm_model=formatted_result.get("llm_model", llm_settings["model"]),
        decision=formatted_result.get("decision") or {},
        state=formatted_result.get("state") or {},
        metadata=formatted_result.get("metadata"),
        success=formatted_result.get("success", False),
        error=formatted_result.get("error"),
        session_id=analysis_result.get("session_id"),
        is_demo=analysis_result.get("is_demo", False),
        demo_reason=analysis_result.get("demo_reason"),
        markdown_report=markdown_report,
    )

    return AnalysisResponse(
        request_id=request_id,
        duration_ms=duration_ms,
        analysis=payload,
    )


__all__ = ["app", "AnalysisRequest", "AnalysisResponse"]
