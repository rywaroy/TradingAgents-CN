# 股票分析 HTTP 服务集成文档

> 面向脚本 / 后端服务调用方，帮助你快速集成 TradingAgents-CN 股票分析能力。

---

## 1. 总览

- **服务说明**：基于 FastAPI 的 REST 接口，同步执行股票分析流程，最终返回结构化结果与 Markdown 报告。
- **默认端口**：`8080`
- **健康检查**：`GET /health`
- **核心接口**：`POST /api/v1/analysis`
- **输出格式**：JSON（包含完整 Markdown 文本）

---

## 2. 环境准备

### 2.1 必需依赖

- Python 3.10+ 或 Docker
- TradingAgents-CN 源码
- LLM / 数据源密钥：
  - `DASHSCOPE_API_KEY`
  - `FINNHUB_API_KEY`
  - `DEEPSEEK_API_KEY` 等按需配置

### 2.2 环境变量总览

| 变量 | 作用 | 备注 |
|------|------|------|
| `DASHSCOPE_API_KEY` | 阿里百炼密钥 | 分析流程必需 |
| `FINNHUB_API_KEY` | Finnhub 金融数据 | 分析流程必需 |
| `DEEPSEEK_API_KEY` 等 | 其他模型密钥 | 按需配置 |
| `TRADINGAGENTS_API_HOST` | 服务监听地址 | 默认 `0.0.0.0` |
| `TRADINGAGENTS_API_PORT` | 服务端口 | 默认 `8080` |
| `TRADINGAGENTS_API_RELOAD` | 开发热重载 | `true`/`false` |
| `TRADINGAGENTS_API_LLMPROVIDER` | 默认 LLM 提供商 | 请求体可覆盖 |
| `TRADINGAGENTS_API_LLMMODEL` | 默认 LLM 模型 | 请求体可覆盖 |

所有变量可写入 `.env` 文件；脚本和服务模块启动时会自动加载。

---

## 3. 部署方式

### 3.1 本地启动（开发/调试）

```bash
pip install -r requirements-lock.txt
cp .env.example .env
vi .env                  # 填写密钥
python scripts/start_analysis_service.py
```

默认监听 `0.0.0.0:8080`。若需自定义端口或日志级别，在 `.env` 或命令前导出相应变量。

### 3.2 Docker Compose（一键部署）

```bash
docker compose up -d analysis-api
```

- `analysis-api` 服务会自动读取 `.env` 并暴露 `8080` 端口。
- 若需修改端口：在 `.env` 中设置 `TRADINGAGENTS_API_PORT=9000`，并把 docker-compose 中的端口映射同步改成 `9000:9000`。
- 日志查看：`docker logs -f tradingagents-analysis-api`
- 状态检查：`docker ps` 或健康检查接口（见下文）

### 3.3 健康检查

```bash
curl http://localhost:8080/health
```

返回示例：

```json
{"status":"ok"}
```

---

## 4. 接口契约

### 4.1 Endpoint 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 服务健康检查 |
| `POST` | `/api/v1/analysis` | 执行股票分析，返回完整结果 |

### 4.2 请求字段详解（POST /api/v1/analysis）

| 字段 | 类型 | 是否必填 | 默认值 | 说明 |
|------|------|----------|--------|------|
| `stock_symbol` | string | ✅ | - | 股票代码（A股 6 位数字 / 港股 4-5 位数字或带 `.HK` / 美股 1-5 位字母） |
| `market_type` | string | ❌ | `A股` | 市场类型：`A股` / `港股` / `美股` |
| `analysis_date` | string | ❌ | 今日 | 分析日期 `YYYY-MM-DD` |
| `analysts` | string[] | ❌ | `["market","fundamentals"]` | 参与分析的 AI 团队：`market`、`fundamentals`、`news`、`social` |
| `research_depth` | int | ❌ | 3 | 分析深度 1-5（越大越耗时） |
| `llm_provider` | string | ❌ | 来自默认配置 | LLM 提供商（如 `dashscope`、`deepseek`、`google` 等） |
| `llm_model` | string | ❌ | 来自默认配置 | 具体模型名称（如 `qwen-plus`、`deepseek-chat` 等） |

**默认值优先级**：请求体 > 环境变量（`TRADINGAGENTS_API_*`）> `default_config.py`

### 4.3 请求示例

#### 4.3.1 使用 DashScope（默认配置）

```bash
curl -X POST http://localhost:8080/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{
        "stock_symbol": "600519",
        "market_type": "A股",
        "research_depth": 3
      }'
```

#### 4.3.2 使用 DeepSeek（指定模型）

```bash
curl -X POST http://localhost:8080/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{
        "stock_symbol": "AAPL",
        "market_type": "美股",
        "analysis_date": "2025-08-01",
        "research_depth": 3,
        "analysts": ["market", "fundamentals"],
        "llm_provider": "deepseek",
        "llm_model": "deepseek-chat"
      }'
```

### 4.4 响应结构

```json5
{
  "request_id": "f43c8c8e9d5f4d4d899dbe053fa9b5ac",
  "duration_ms": 18250,
  "analysis": {
    "stock_symbol": "AAPL",
    "market_type": "美股",
    "analysis_date": "2025-08-01",
    "analysts": ["market", "fundamentals"],
    "research_depth": 3,
    "llm_provider": "deepseek",
    "llm_model": "deepseek-chat",
    "decision": {...},         // 投资决策摘要
    "state": {...},            // 各模块详细输出
    "metadata": {...},         // 额外元数据
    "success": true,
    "error": null,
    "session_id": "analysis_abcd1234",
    "is_demo": false,
    "demo_reason": null,
    "markdown_report": "# AAPL 股票分析报告\n\n..."  // 完整 Markdown
  }
}
```

常见错误：

| 状态码 | 场景 | 响应示例 |
|--------|------|----------|
| 422 | 参数校验失败 | `{"detail": ["股票代码不能为空"]}` |
| 503 | 缺少关键环境变量 | `{"detail": "运行环境缺少必要配置: DASHSCOPE_API_KEY"}` |
| 500 | LLM/数据源异常 | `{"detail": "分析执行失败: ...错误信息..."}` |

---

## 5. 实战示例

### 5.1 Python 调用（保存 Markdown）

```python
import requests, pathlib

payload = {
    "stock_symbol": "TSLA",
    "market_type": "美股",
    "research_depth": 3,
    "analysts": ["market", "fundamentals"],
    "llm_provider": "deepseek",
    "llm_model": "deepseek-chat"
}

resp = requests.post(
    "http://localhost:8080/api/v1/analysis",
    json=payload,
    timeout=180
)
resp.raise_for_status()

data = resp.json()
markdown = data["analysis"]["markdown_report"]
pathlib.Path("report_TSLA.md").write_text(markdown, encoding="utf-8")
```

### 5.2 Shell 调用

```bash
curl -s -X POST http://localhost:8080/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{"stock_symbol":"0700","market_type":"港股"}' \
  | jq -r '.analysis.markdown_report' > report_0700.md
```

### 5.3 Postman/Insomnia

- 将 Method 设置为 `POST`，URL 为 `http://localhost:8080/api/v1/analysis`。
- Body 选择 `raw` JSON，填入参数。
- 若分析耗时较长，请在 Settings 中将超时改为更大的数值（建议 ≥ 120000 ms）。

---

## 6. 性能与并发建议

1. **分析耗时**：单次请求 10~60 秒不等，取决于 LLM 响应时间与数据源延迟。
2. **客户端超时**：务必将请求超时设为至少 120 秒；默认为 0（无限等待）的可保持不变。
3. **并发控制**：建议单批 3-5 个并发请求，观察稳定性后再逐步调高。过高并发可能触发 LLM 限流或 API 超时。
4. **批量任务策略**：
   - 将股票列表切片分批提交（如 5 个一批）。
   - 监控 HTTP 429/5xx 或内部 `demo_reason` 字段，及时重试或减小并发。
   - 若要更高吞吐，可在后续版本引入任务队列（Redis + worker）实现异步执行。

---

## 7. 排障指南

| 现象 | 可能原因 | 处理建议 |
|------|----------|----------|
| `503` 缺少配置 | `.env` 未配置或未加载 | 确保 `.env` 含必需密钥，并在启动前 `source .env` 或配置 `env_file` |
| `401/403` | LLM API 权限不足 | 检查密钥权限、额度或绑定 IP |
| `500` 且日志提示超时 | 外部 LLM/数据源超时 | 降低并发 / 切换更快模型 / 重试 |
| Docker 中 `ModuleNotFoundError` | 镜像旧缓存 | `docker compose build analysis-api` 后重启 |
| Markdown 为空 | 分析失败或缓存命中 demo 数据 | 检查 `success` 字段及 `demo_reason`，确认密钥是否有效 |

查看日志（本地/容器）：

```bash
# 本地
tail -f logs/tradingagents.log

# Docker
docker logs -f tradingagents-analysis-api
```

---

## 8. 安全集成建议

- 当前接口 **不启用鉴权**，务必通过网关、内网或防火墙限制访问范围。
- 可在上游增加 API Key 或 JWT 校验；亦可在应用层增加请求签名。
- 记录 `request_id` 与调用方标识，方便审计与故障定位。

---

## 9. 常见扩展方向

- **异步队列**：POST 返回 `task_id`，后台 worker 执行，调用方轮询 `GET /analysis/{task_id}`。
- **多格式导出**：在 Markdown 基础上扩展 PDF / HTML 下载接口。
- **成本监控**：结合 `session_id` 与日志，统计 Token 和调用费用。
- **模型切换策略**：按市场或任务类型自动选择不同 LLM。

---

如需进一步功能或遇到问题，欢迎反馈。祝集成顺利！ 🎯
