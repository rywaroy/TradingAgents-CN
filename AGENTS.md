# Repository Guidelines

## 项目结构与模块组织
- `app/` 为 FastAPI 后端与调度任务的主入口，`tradingagents/` 存放可复用的分析与多智能体逻辑；命令行工具集中在 `cli/`，示例脚本置于 `examples/` 与 `scripts/`。
- `frontend/` 采用 Vue 3 + Element Plus，`web/` 和 `assets/` 提供静态资源；`docs/`、`reports/`、`images/` 承载文档及导出材料。
- 测试与实验集中在 `tests/`（含 `integration/`、`system/`、`unit/` 子目录），数据样本位于 `data/` 与 `logs/`。Docker 与部署文件位于 `docker/`、`docker-compose*.yml`、`Dockerfile.*`。

## 构建、测试与开发命令
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt           # 安装后端依赖（若需锁定版本可用 uv pip sync uv.lock）
python -m uvicorn app.main:app --reload   # 启动本地 API
python main.py --help                     # 查看 CLI 分析入口
npm install && npm run dev --prefix frontend   # 启动前端调试
npm run build --prefix frontend                # 打包前端
pytest                                        # 默认跳过 integration 标记
pytest -m integration tests/system            # 运行端到端测试
docker compose up -d                          # 需要完整栈或演示环境时使用
```

## 编码风格与命名约定
- Python 端遵循 PEP 8 与 typing 约束，4 空格缩进，模块/函数使用 `snake_case`，类使用 `PascalCase`，配置键保持 `UPPER_SNAKE_CASE`；新增逻辑需补充中文 docstring。
- 前端使用 TypeScript + `<script setup>`；组件文件 `PascalCase.vue`，Pinia store 采用 `useXxxStore`；保持 ESLint + Prettier（`npm run lint` / `npm run format`）干净通过。
- 配置、数据与报告的命名统一以功能前缀开头，例如 `config/env/quotes_*.yaml`、`reports/{market}_{date}.md`，避免中文空格与大写扩展名。

## 测试指南
- Pytest 配置位于 `tests/pytest.ini`，默认排除 `integration`，如需覆盖率请使用 `pytest --maxfail=1 --disable-warnings -q` 并记录运行耗时，确保单轮 <60s。
- 单元测试命名 `test_<Feature>_<Scenario>`；如依赖外部行情，请利用 `tests/dataflows/` 中的缓存或 `tests/config/fixtures/` 提供的 mock。
- 前端变更需运行 `npm run lint --prefix frontend` 与必要的组件快照；涉及 CLI 或调度的改动应提供最小可复现脚本（置于 `examples/` 或新建 `scripts/dev/`）。

## 提交与 Pull Request 规范
- Git 历史多采用 `docs:`、`chore:`、`fix:` 等前缀并辅以简短中文说明，推荐遵循 `<type>: <摘要>`（type 取 `feat|fix|docs|chore|refactor|test`），必要时补充受影响模块。
- PR 描述需包含：目的、关键变更列表、测试命令输出摘要、相关 Issue/工单链接；UI/报表相关修改请附截图或示例报告路径。
- 在 PR 中列出配置或密钥改动，并指明 `.env` 示例更新位置；涉及商业授权目录（`app/`、`frontend/`）的修改需在描述中强调。

## 安全与配置提示
- 所有敏感凭据放入 `.env` 或 `config/secrets/`，切勿写入 Git；若需要分享模板，请更新 `config/.env.example`。
- 修改 Docker、Nginx、数据库等高风险文件前请先在 Issue 或讨论中确认影响面，并在 PR 中附带 rollback 步骤。
