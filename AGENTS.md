# Local Workbench 项目约定

- 回复用中文；产品代码、文件名、接口和提交信息使用英文。
- 项目主线：[开发总文档](docs/development/master-plan.md)；明细目录 `docs/development/tasks/`，新增任务使用 `docs/development/task-template.md`，编号递增。
- 业务边界和接口以 `docs/superpowers/specs/2026-10-12-local-workbench-design.md` 为准，执行步骤见对应 plans 文档；总文档记录实际进度，不将规划标为完成。
- Windows / Python 3.13 / FastAPI，本机服务默认 `127.0.0.1:8765`；使用项目 `.venv`，不要修改全局环境。
- 安装：`.\scripts\setup-backend.ps1`；启动：`.\scripts\start-backend.ps1`；全套测试：`.\.venv\Scripts\python.exe -m pytest backend\tests -q`；构建：`.\.venv\Scripts\python.exe -m build backend`。
- 公共 JSON 为 camelCase，内部 Python 为 snake_case；未知字段拒绝，标识符使用 UUID。
- 文件、模型、队列和数据库服务尚待后续实现。新增功能按所属任务完善同一 contracts.py；不预先创建空接口、插件框架或重名模型。
- 原始输入不可修改；工具只使用任务已授权 ID。运行状态、密钥和用户数据不进入 Git。
