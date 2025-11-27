# TradingAgents 多智能体分析流水线

本文概述单股分析从「股票代码输入、取数」到「多角色分析与决策」的完整链路与关键代码位置。

## 1. 入口与取数准备
- 路由入口：`app/routers/analysis.py` 的 `/analysis/single` 调用 `SimpleAnalysisService._run_analysis_sync`，随后进入 `TradingAgentsGraph.propagate`。
- 代码校验与基础信息：`tradingagents.utils.stock_validator.prepare_stock_data_async` 校验股票代码、市场类型、分析日期，失败直接返回错误。
- 市场识别：`tradingagents.utils.stock_utils.StockUtils.get_market_info` 区分 A 股/港股/美股并提供币种信息。
- 统一工具注入：`TradingAgentsGraph.__init__` 构造 `tool_nodes`，绑定统一数据接口（行情、新闻、社交情绪、基本面）。工具定义在 `tradingagents/agents/utils/agent_utils.py` 的 `Toolkit` 中。
- 模型与配置：`app/services/simple_analysis_service.py:create_analysis_config` 根据研究深度和前端指定模型选出 quick/deep 模型、辩论轮次、风险轮次，并传递给 `TradingAgentsGraph`。

## 2. 多智能体编排（LangGraph 拓扑）
- 拓扑定义：`tradingagents/graph/setup.py:GraphSetup.setup_graph`。
- 默认节点顺序（由 `selected_analysts` 决定起点和顺序）：
  1. 市场分析师 → `tools_market` → `Msg Clear Market`
  2. 新闻分析师 → `tools_news` → `Msg Clear News`
  3. 社交分析师 → `tools_social` → `Msg Clear Social`
  4. 基本面分析师 → `tools_fundamentals` → `Msg Clear Fundamentals`
- 研究辩论：`Bull Researcher` ↔ `Bear Researcher`（条件循环，见 `conditional_logic.should_continue_debate`），进入 `Research Manager` 汇总。
- 交易决策：`Trader` 将结论转换为交易方案。
- 风险辩论：`Risky Analyst` → `Safe Analyst` → `Neutral Analyst`（条件循环，见 `should_continue_risk_analysis`），最终 `Risk Judge` 输出风险裁决并结束。
- 执行驱动：`tradingagents/graph/trading_graph.py:TradingAgentsGraph.propagate` 通过 `graph.stream` 依次驱动节点，并将节点名称映射为中文进度提示（`_send_progress_update`）。

## 3. 角色职责与产出
- 市场分析师（`tradingagents/agents/analysts/market_analyst.py`）：调用 `get_stock_market_data_unified`，输出 `state.market_report`。
- 新闻分析师（`tradingagents/agents/analysts/news_analyst.py`）：调用 `get_stock_news_unified`（必要时谷歌/Finhub 兜底），输出 `state.news_report`。
- 社交/情绪分析师（`tradingagents/agents/analysts/social_media_analyst.py`）：调用 `get_stock_social_sentiment_unified` 等，输出 `state.sentiment_report`/`state.social_report`。
- 基本面分析师（`tradingagents/agents/analysts/fundamentals_analyst.py`）：调用 `get_stock_fundamentals_unified`（SimFin/Finhub 兜底），输出 `state.fundamentals_report`。
- 多空研究员（`tradingagents/agents/researchers/bull_researcher.py`, `bear_researcher.py`）：生成多空论据，写入 `investment_debate_state.bull_history` / `bear_history`。
- 研究经理（`tradingagents/agents/managers/research_manager.py`）：汇总多空观点，形成 `state.investment_plan` 或 `state.research_team_decision`。
- 交易员（`tradingagents/agents/trader/trader.py`）：将研究结论转成交易行动与执行要点，写入 `state.trader_investment_plan`、`state.final_trade_decision`。
- 风险辩论三人组（`risk_mgmt/aggresive_debator.py`, `neutral_debator.py`, `conservative_debator.py`）：对交易方案进行激进/中性/保守评估，记录在 `risk_debate_state.*_history`。
- 风险经理（`risk_mgmt/managers/risk_manager.py`）：汇总风险评估，输出 `risk_management_decision`，推动流程结束。
- 决策结构化：`TradingAgentsGraph.process_signal` 将 `final_trade_decision` 转为结构化 `decision`（action、target_price、confidence、reasoning，并附 `model_info`）。

## 4. 状态与结果
- `final_state` 中的主要产出字段：`market_report`、`news_report`、`sentiment_report`、`fundamentals_report`、`investment_plan`、`trader_investment_plan`、`final_trade_decision`、`investment_debate_state`、`risk_debate_state`、`performance_metrics`。
- `decision`：结构化交易建议，供上层服务写入 Mongo/文件及返回给前端（见 `app/services/simple_analysis_service.py` 的结果保存逻辑）。
