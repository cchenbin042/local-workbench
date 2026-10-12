# T001：后端脚手架

## 任务信息

| 字段 | 内容 |
|---|---|
| 任务编号 | T001 |
| 类型 / 关联里程碑 | 开发 / M1，实施计划 Task 1 |
| 状态 | 已完成 |
| 创建日期 | 2026-10-12 |
| 开始日期 | 2026-10-12 |
| 最近更新 | 2026-10-12 |
| 完成日期 | 2026-10-12 |
| 最近回写 | 2026-10-12 |
| 总文档 | [开发总文档](../master-plan.md) |
| 依赖 | Python 3.13；项目目录已建立 |
| 设计 / 计划 | [首版设计](../../superpowers/specs/2026-10-12-local-workbench-design.md)、[实施计划 Task 1](../../superpowers/plans/2026-10-12-local-workbench.md) |

## 目标、范围与验收

服务无需模型即可绑定本机并返回健康状态；提供可安装包、配置、公共契约、错误格式、本地 Host/Origin 检查和可重复的安装启动流程。为后续持久化和文件服务提供基础。

| 功能点 | 验收条件 | 状态 |
|---|---|---|
| F01 项目环境与锁文件 | 独立 .venv、固定依赖、包可构建安装 | 已完成 |
| F02 配置与公共契约 | UUID、camelCase、未知字段、参数边界验证 | 已完成 |
| F03 HTTP 服务 | health、OpenAPI、统一错误、本地访问检查 | 已完成 |
| F04 CLI 与启动脚本 | 不依赖模型，真实进程启动并返回 health | 已完成 |

## 实施裁决

1. 本次只执行计划 Task 1；依据用户“先完成后端脚手架”的最新范围。其余九项留待接续，避免把计划当作完成成果。
2. 保留用户指定目录，在工作分支实施；不另建工作树。目录尚无产品代码，远端历史已接入；代价是后续并行开发需要再建立隔离工作树。
3. 只实现当前有行为的 FileSelection、TaskCreate、TaskStatus、TaskEvent，及 FastAPI/Pydantic/Uvicorn 依赖；ModelFactory、持久化、报告和处理库随相应任务加入。代价是后续需扩展契约和锁文件。
4. Windows 下用 PowerShell 和 Python 完成执行台账与审查包整理，替代技能的 Bash 辅助脚本；保留相同任务身份、基线、裁决和验证证据。代价是手工核验这些字段。

## 开发记录

### 2026-10-12 / 建档与基线

- 实际行为：建立任务记录；原有产品代码为空，当前处于工作分支。
- 文件：本明细、总文档及 `.gitignore` 新增 Python、运行数据、密钥和执行缓存忽略规则。
- 验证：`git status --short --branch`、`git log -1 --oneline`；基线为远端初始提交 e7384d4。
- 下一步：先编写行为测试并观察失败，然后实现服务。

### 2026-10-12 / F02、F03：契约与本机 HTTP 服务

- 实际行为：`GET /api/health` 返回 200 与 `{"status":"ok"}`，OpenAPI 可用；只接受精确的本机 Host/Origin，重复头和外部预检也拒绝。
- 契约：UUID 标识、camelCase JSON、禁未知字段、非空来源与要求、agent/profile 模式、严格正整数事件序号、带时区时间、无 NaN/Inf 的 JSON 载荷。
- 配置：绑定限制为 127.0.0.1，端口 1–65535；路径计算不创建数据库或扫描样例以外目录。规格数值已声明，读取/处理限额的实际执行留在后续任务。
- 错误：业务、HTTP、参数错误采用统一对象；校验错误不回显潜在密钥输入。
- 文件：新增 `config.py`、`contracts.py`、`errors.py`、`app.py` 及相应测试。
- 验证：项目根执行 `python -m pytest backend/tests -q`（使用 `.venv`）；实现前 21 failed / 19 errors，均来自缺少模块/CLI；实现后 40 passed。
- 已知提示：锁定的 Starlette 1.7.0 提示 TestClient 的 HTTPX 兼容路径未来弃用；本次测试仍通过，未抑制提示，真实 HTTP 测试也已通过。后续升级测试客户端时处理。
- 下一步：验证安装/启动脚本、包构建和 wheel 安装，完成 F01/F04。

### 2026-10-12 / F01：环境、锁文件和包交付

- 实际行为：项目独立 `.venv` 使用 Python 3.13.9；运行与开发依赖 24 项锁定，项目以 editable 安装。安装脚本可重复同步环境。
- 文件：`backend/pyproject.toml`、`backend/requirements.lock.txt`、`scripts/setup-backend.ps1`、包入口和 README。
- 验证：`scripts/setup-backend.ps1 -Python D:\software\tool\conda\python.exe` 成功；`uv pip check` 显示 25 包兼容（含本项目）；`python -m build backend` 成功生成 sdist/wheel。
- 在临时独立虚拟环境安装锁文件及 wheel 后，全套 40 项测试再次通过，排除 editable 导入掩盖打包缺失。
- 下一步：完成 Windows PowerShell 启动兼容验证。

### 2026-10-12 / F04：CLI 与 Windows 启动兼容

- CLI：支持 host、port、app-root、log-level；只绑定本机。真实子进程测试验证无模型启动、health/OpenAPI 与外部 Origin 拒绝，且不创建状态目录。
- 启动脚本使用自身位置定位项目根，前台运行；已增加自定义端口及不同当前目录的 Windows PowerShell 回归测试。
- 调试证据：无 BOM 的 UTF-8 脚本在 PowerShell 7 可运行，但 Windows PowerShell 5.1 按本机 ANSI 解码，导致中文字符串解析失败；显式 UTF-8 读取后解析成功。
- 修复：两个 PowerShell 脚本统一保存为带 BOM 的 UTF-8，兼容 Windows PowerShell 5.1 与 PowerShell 7。回归测试经过移除 BOM 重现 ParserError、恢复 BOM 通过的 RED→GREEN；完整测试为 41 passed / 0 skipped。
- 测试探测在启动尚未完成时可出现 ConnectTimeout，已将它与 ConnectError 一并纳入有总截止时间的重试，并保留超时日志；服务就绪后状态与响应仍严格断言。
- Windows PowerShell 5.1 实际执行安装脚本成功；启动脚本回归确认不同当前目录、自定义端口及真实 HTTP 健康响应。

## 实际文件改动

| 文件 | 改动 | 用途 |
|---|---|---|
| `backend/pyproject.toml`、`backend/requirements.lock.txt` | 新增 | 包、版本锁、构建与测试依赖 |
| `backend/workbench/__init__.py`、`__main__.py` | 新增 | 包与 CLI |
| `backend/workbench/config.py`、`contracts.py` | 新增 | 配置与公共类型 |
| `backend/workbench/app.py`、`errors.py` | 新增 | HTTP 组装、访问守卫与错误 |
| `backend/tests/conftest.py`、`test_app.py`、`test_contracts.py`、`test_cli.py` | 新增 | 41 项行为、边界和真实启动测试 |
| `scripts/setup-backend.ps1`、`scripts/start-backend.ps1` | 新增 | 独立安装与 Windows 启动 |
| `.gitignore`、`README.md` | 修改 | 忽略规则、当前能力与使用说明 |
| `AGENTS.md` | 新增 | 项目约定与开发记录入口 |
| `docs/superpowers/` 中设计和计划 | 新增到仓库、更新状态 | 前置规划和实际范围链接 |

已有设计、计划在本次代码实施前建立；没有将完整设计功能计为已实现。执行缓存、环境和构建产物仅在本机保留且忽略。

## 验证结果

所有命令执行目录为项目根 `D:\llm\agent\local-workbench`。

| 检查 | 结果 | 覆盖与限制 |
|---|---|---|
| `.venv\Scripts\python.exe -m pytest backend/tests -q` | 41 passed，0 skipped，1 upstream deprecation warning | 契约、配置、访问守卫、错误、CLI、实际服务与 Windows 脚本 |
| `uv pip check --python .venv/Scripts/python.exe` | 25 包兼容 | 已安装环境 |
| `.venv\Scripts\python.exe -m build backend` | sdist/wheel 成功 | 六个模块及 CLI 入口齐全 |
| 独立虚拟环境安装 wheel 后执行当时的完整测试 | 40 passed | 无 editable 导入；新增 Windows 编码回归随后在主环境通过 |
| Windows PowerShell 5.1 安装脚本 | 成功 | 固定依赖同步及包安装 |
| Windows 启动编码 RED→GREEN | 无 BOM 复现 ParserError；有 BOM 通过 | 未改变系统执行策略；Bypass 仅用于测试进程 |
| Markdown 链接、任务状态、同日记录检查 | 通过 | T001–T003 所有明细，结束时再次核对 |

尚未验证文件解析、SQLite、模型、SSE、任务执行或前端，这些不是本次交付功能。

## 遗留与接续

范围内 F01–F04 已验收；Git 交付和独立审查见 T002。Starlette 的 HTTPX TestClient 弃用提示属于后续测试依赖维护，未隐藏，也未影响真实 HTTP 验证。

下一次新增 T004 实现 SQLite、事件事务和历史恢复，先读总文档、计划 Task 2、config.py/contracts.py/app.py；在 contracts.py 增加持久化记录，按任务建立失败测试。

## 回写摘要

- 回写日期：2026-10-12。
- 状态：已完成，完成日期 2026-10-12。
- 完成项：F01–F04，41 项测试、构建、独立安装和真实启动验证。
- 里程碑：只完成 M1 的脚手架子项；M1 整体仍进行中。
- 下一步：T002 审查与推送；随后新增 T004 推进 SQLite。
