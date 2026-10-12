# Local Workbench

Windows 本地文件、数据与文档工作台。当前版本交付 **FastAPI 后端脚手架**：本机服务、健康检查、配置、公共请求/事件契约、统一错误及 Host/Origin 校验。

工作区扫描、SQLite、数据/文档处理、模型任务、SSE 和 React 界面按照实施计划后续完成。目前不能执行文件处理任务。

## 环境准备

需要 Windows、Python **3.13**、[uv](https://docs.astral.sh/uv/) 和 Git。当前已验证 Python 3.13.9；此阶段无需 Node、数据库服务或模型密钥。

```powershell
git clone https://github.com/cchenbin042/local-workbench.git
cd local-workbench
.\scripts\setup-backend.ps1
# Python 不在 PATH 时：
# .\scripts\setup-backend.ps1 -Python 'D:\software\tool\conda\python.exe'
```

脚本从任何当前目录调用都以项目目录为根，创建 `.venv`，安装 `backend/requirements.lock.txt` 中的运行与测试依赖，再安装本地包。隔离构建工具由 `backend/pyproject.toml` 固定版本。已有 `.venv` 会同步到该项目锁文件。

## 启动与检查

```powershell
.\scripts\start-backend.ps1
# 指定其他端口：.\scripts\start-backend.ps1 -Port 9123
```

服务前台运行，按 Ctrl+C 停止。默认访问 [健康接口](http://127.0.0.1:8765/api/health)、[Swagger 文档](http://127.0.0.1:8765/docs) 和 [OpenAPI](http://127.0.0.1:8765/openapi.json)。健康响应为 `{"status":"ok"}`。

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/health
.\.venv\Scripts\python.exe -m pytest backend\tests -q
.\.venv\Scripts\python.exe -m build backend
```

也可从项目根直接执行 `.\.venv\Scripts\python.exe -m workbench --host 127.0.0.1 --port 8765 --app-root .`。CLI 的 `--app-root` 默认当前目录；启动脚本自动传入项目根。服务只允许绑定 `127.0.0.1`，接受该端口的 `localhost`/`127.0.0.1` Host，以及同源或端口 5173 的本机开发 Origin。CLI 无 Origin 的请求可用。

## 接口与目录

- 当前业务路由只有 `GET /api/health`；TaskCreate/TaskEvent 是后续 API 的类型基础，不代表任务端点已实现。
- 公共 JSON 使用 camelCase、UUID；拒绝未知字段、空任务来源、空白要求和非法模式。任务事件序号是正整数，载荷必须为有限数值组成的合法 JSON。
- 已知 HTTP/参数/业务错误采用 `{"error":{"code":"...","message":"..."}}`；参数错误不回显输入。
- `backend/workbench/`：服务、配置、CLI、契约与错误；`backend/tests/`：单元、HTTP 与真实子进程启动测试；`scripts/`：安装和启动。
- 默认样例路径为项目的 `samples/`，状态路径为 `.local-workbench/state.sqlite3`；脚手架只计算路径，尚不创建数据库、扫描目录或读取用户文件。
- 配置保留规格规定的 50 MiB、100,000 行、200 列等限额；读取和执行阶段的限额检查在后续任务实现。
- `.venv`、运行状态、缓存、构建输出及 `.env` 不提交。未来样例产物放在 `samples/outputs/`，同样忽略。

## 开发记录

- [开发总文档](docs/development/master-plan.md)
- [T001 后端脚手架](docs/development/tasks/T001-2026-10-12-backend-scaffold.md)
- [T002 Git 初始化与推送](docs/development/tasks/T002-2026-10-12-git-bootstrap.md)
- [T003 开发台账](docs/development/tasks/T003-2026-10-12-development-ledger.md)
- [任务模板](docs/development/task-template.md)
- [首版设计](docs/superpowers/specs/2026-10-12-local-workbench-design.md) / [实施计划](docs/superpowers/plans/2026-10-12-local-workbench.md)

代码由本项目独立实现；WorkBuddy 静态分析仅作为架构参考，仓库不包含其程序包、凭证或代码。
