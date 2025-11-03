# Repository Guidelines

## 项目纵览
- 框架基于 LangGraph 构建多智能体协作，核心模块在 `tradingagents/` 内按 `agents/`、`graph/`、`llm/`、`tools/` 子目录拆分；任何改动需同步评估 `default_config.py` 与图节点依赖。
- 前端采用 FastAPI + Vue3 架构（见 `web/`），同时保留命令行与脚本入口（`main.py`、`cli/`、`start_web.py`、`docker-compose.yml`）。
- 文档体系详见 `docs/STRUCTURE.md`，涵盖架构、配置、安全、开发流等专题，更新核心功能时务必同步对应文档。

## 项目结构与资产
- `tradingagents/`：载入 `graph/trading_graph.py`、多角色分析师、LLM 适配器和工具链；新增智能体需参考 `docs/architecture/v0.1.13/agent-architecture.md` 定义输入输出与信号流。
- `web/`：`web/app.py` 为调试入口，前端资源位于 `web/src/`，与后端配置共享 `config/` 与 `default_config.py`。
- `tests/`：`tests/README.md` 列出 API、数据源、性能、LLM、Web 五大类用例，集成测试集中于 `tests/integration/`，调试脚本沿用 `debug_*.py` 约定。
- `scripts/`：按 `setup/`、`validation/`、`maintenance/`、`development/` 等子目录区分用途（参见 `scripts/README.md`），所有脚本从仓库根目录执行且不得生成脏文件。
- `docs/`：使用 Markdown+Mermaid 描述架构；新增能力需在对应分区补充使用说明与示例。

## 构建、运行与验证
- 首选锁定依赖：`pip install -r requirements-lock.txt`，随后 `pip install -e . --no-deps` 启用可编辑模式；本地调试可通过 `python start_web.py` 或 `python web/app.py`，容器环境使用 `docker-compose up -d --build`。
- 快速体验：执行 `python main.py --profile quick` 或 `python cli/main.py` 运行命令行流程；部署前确认 `.env` 来源于 `.env.example` 并补全 API、数据源、数据库参数。
- 自动化检查：`python scripts/validation/verify_gitignore.py`、`python scripts/syntax_checker.py`、`python scripts/development/prepare_upstream_contribution.py` 用于提交前验证。
- 全量测试：`python -m pytest tests/ -v`；重点路径附带覆盖率命令 `python -m pytest tests/ --cov=tradingagents --cov-report=term-missing`，单次运行建议控制在 60 秒以内。
- 定向调试：利用 `pytest -k "<pattern>"` 或独立执行 `tests/debug_*.py` 快速定位 LLM、数据源问题。

## 代码风格与命名
- 遵循 PEP 8 + 类型注解，四空格缩进，核心函数编写中文 docstring；类名 `PascalCase`，函数/变量 `snake_case`，常量全大写。
- 提交前运行 `black .`、`flake8`，必要时参考 `docs/overview/installation.md` 配置 `isort`、`mypy`；保持中文注释覆盖复杂业务与关键数据流。
- Web 端 Vue 组件命名遵循 `PascalCase.vue`，共享逻辑沉淀在 `web/src/utils/`，避免在组件中硬编码 API。

## 测试策略
- pytest 为唯一测试框架，测试文件命名 `test_<feature>.py`，辅助脚本命名 `debug_*.py` 或 `check_*.py`；新增用例需更新 `tests/README.md` 分类。
- 数据源、LLM、性能、Web、工具链测试均有现成模板，可复用 `tests/test_cli_version.py`、`tests/test_redis_performance.py`、`tests/integration/test_dashscope_integration.py`。
- 扩展 LLM 适配器时使用 `docs/llm/LLM_TESTING_VALIDATION_GUIDE.md` 给出的分层测试（连接、工具调用、端到端、性能）并保留日志。

## 自动化与分支治理
- 主干保护：遵循 `docs/DEVELOPMENT_WORKFLOW.md` 的“main 禁止直接推送”与 Git hook 约束，分支命名 `feature/*`、`fix/*`、`hotfix/*`。
- GitHub Actions `upstream-sync-check.yml` 每周检测上游更新并创建 Issue，必要时参阅 `docs/maintenance/upstream-sync.md` 运行同步脚本。
- 脚本目录提供 `scripts/git/upstream_git_workflow.sh`、`scripts/development/prepare_upstream_contribution.py` 等自动化工具，执行前确认不会改写敏感配置或生成大文件。

## 提交与 PR 规范
- Commit 采用约定式前缀（`feat`、`fix`、`docs`、`chore` 等），一次提交聚焦单一改动并附简洁中文说明；推送前确保测试与检查脚本全部通过。
- Pull Request 使用 `.github/pull_request_template.md`，填写变更摘要、测试指令与结果，涉及 LLM 适配器需完成专属检查清单并附响应时间或成功率等指标。
- 合并前确认：测试通过、文档同步、风险与回滚方案记录于 PR 讨论区；主干合并需维护者确认，遵循“用户测试先于合并”的流程。

## 安全与配置检查
- `.env`、`.env.*` 必须在 `.gitignore` 中，密钥仅通过环境变量读取（参照 `docs/security/api_keys_security.md`），建议设置 `chmod 600 .env` 并定期轮换。
- 新增配置需在 `config/` 提供示例或模板，并在 `docs/configuration/`、`docs/installation-mirror.md` 等文档说明加载顺序与依赖。
- 清理 `data/`、`reports/`、`logs/` 临时文件后再提交，确保不含敏感信息；提交到公共仓库前重新检查 Git 历史是否泄露密钥。
