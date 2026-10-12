# 本地文件、数据与文档工作台 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Windows 本机提供一个可浏览文件、执行受控数据/文档任务、展示流式进度并生成实际文件的工作台。

**Architecture:** React 前端通过 HTTP/SSE 调用单个 FastAPI 服务。后端负责工作区、SQLite、任务队列、模型适配、工具执行和产物提交；文件处理采用 Python 库。先完成无需模型的基础流程和工具测试，再接模型循环、界面及本机启动交付。

**Tech Stack:** Python 3.13、FastAPI、HTTPX、Pydantic、sqlite3、Pandas、openpyxl、python-docx、pypdf、Matplotlib；React、TypeScript、Vite；pytest、Vitest、Playwright。

**Spec:** [首版设计](../specs/2026-10-12-local-workbench-design.md)

**Project root:** `D:\llm\agent\local-workbench`。下面新建文件的相对路径均以此目录为根。制定计划时只有设计文档；2026-10-12 用户授权先实施 Task 1、Git 推送和开发记录。实际完成证据与裁决见[开发总文档](../../development/master-plan.md)。其余 Tasks 2–10 待后续推进。

## Global Constraints

- Windows 本机、单用户、一次执行一个任务，后续任务排队；默认服务绑定 `127.0.0.1:8765`。
- 首次启动使用项目的自建 `samples` 目录，不自动读取其他个人目录；用户可显式更换工作区。
- 支持 CSV、XLSX、TXT、Markdown、DOCX 和文本型 PDF；扫描 PDF 明确提示无可用文本，不提供 OCR。
- 单文件上限 `50 * 1024 * 1024` 字节；单表上限 100,000 行、200 列；预览最多 100 行。
- 给模型的数据样本最多 20 行；每次文档片段最多 12,000 字符。
- 工具只接受本任务选中的 fileId 或本任务产生的 resultId；不接受任意系统路径。
- 支持筛选、排序、去重、选择列，以及 count/sum/mean/min/max 聚合；图表支持柱状图和折线图。
- 不执行模型生成的 Python、Shell、SQL 或 Pandas eval；原始输入文件不修改。
- 产物为 XLSX、DOCX、Markdown、PNG，保存在工作区 `outputs/<taskId>`，使用新文件名，不提供覆盖或删除工具。
- 模型工具循环最多 12 轮；单次模型请求超时 120 秒；结构化报告修正最多一次。
- 密钥仅保存于服务内存或来自 `WORKBENCH_API_KEY`；SQLite、日志、任务快照和普通设置响应都不包含密钥。
- 同步库调用返回后处理取消，不承诺强制终止任意 Pandas/文档解析函数；cancel_requested 生效后不能发布新产物。
- 状态更新与事件写入使用同一数据库事务；同一任务的取消和产物发布使用同一任务锁。
- 用户数据不进入 Git；后端使用项目 `.venv`，不修改全局 Python 环境。
- 产品代码、文件名、接口和提交信息使用英文；产品界面及错误说明使用中文。

## Review Focus

1. **Windows junction/链接越界及工作区切换**：不能读写工作区外的文件，也不能让旧任务误用新工作区；由 Task 3 的路径/快照测试和 Task 8 的作用域测试覆盖。
2. **编码、类型和 Excel 文本**：UTF-8 BOM/GB18030、混合列、NaN 和以 `=` 开头的文字应正确预览/导出，不生成非法 JSON 或意外公式；由 Tasks 3、5、6 覆盖。
3. **模型流分片和坏工具调用**：参数分片、多个 tool call、未知工具、重复 callId、超时和不支持 tool calling 的响应不能造成重复执行或虚假完成；由 Tasks 7、8 覆盖。
4. **取消与导出同时发生**：staging 可以清理，但已生效的取消之后不能发布文件或 completed；由 Task 6 的发布测试和 Task 8 的运行器测试覆盖。
5. **SSE 重连与服务重启**：游标恢复不丢失/重复应用事件；未完成任务变为 interrupted，历史产物仍可下载；由 Tasks 2、8、9、10 覆盖。

## 目录与职责

```text
local-workbench/
  backend/
    pyproject.toml                  Python 包及测试配置
    requirements.lock.txt          解析后的完整 Python 版本锁
    workbench/
      __init__.py
      __main__.py                   CLI 服务入口
      app.py                        服务组装、生命周期、静态前端
      config.py                     路径、端口和限额
      contracts.py                  Pydantic 公共模型/JSON 契约
      errors.py                     统一错误码/异常映射
      storage.py                    SQLite、事务、仓储
      workspace.py                  工作区、路径授权、文件登记/快照
      tables.py                     表格读取、概览、转换
      documents.py                  文本提取、来源定位
      artifacts.py                  staging、校验、发布和预览
      exporters.py                  XLSX/DOCX/Markdown/PNG 生成
      model.py                      设置/密钥、兼容模型流解析
      tools.py                      工具 schema、注册及作用域检查
      runner.py                     队列、Agent 循环、取消
      api.py                        HTTP 路由、SSE 和下载
    tests/                          单元、服务和集成测试
  frontend/
    src/
      api.ts / types.ts             类型化 API、SSE 客户端
      App.tsx / styles.css          页面装配、三栏布局
      components/                   设置、文件树、任务、预览
      task-state.ts                 事件归并和重连状态
    tests/                          组件测试、浏览器流程
  samples/                          自建示例数据与说明
  scripts/                          示例生成、依赖准备、启动
  start-workbench.ps1
  README.md
  docs/superpowers/
  .local-workbench/                 运行状态、SQLite；不提交
  .venv/                            Python 环境；不提交
```

按职责分文件，首版不新增插件框架、消息中间件、向量库、远程工作区或独立 Agent daemon。

## 固定契约与实现默认值

- Python 内部使用 snake_case；Pydantic 公共 JSON 使用 camelCase，禁止未定义字段。标识符为 UUID 字符串。
- `FileSelection(file_id: str, sheet: str | None)`；`TaskCreate(workspace_id: str, sources: list[FileSelection], prompt: str, mode: Literal['agent', 'profile'])`。
- `TaskRecord` 包含 id、workspace_id、workspace_root 快照、sources、prompt、mode、status、model_snapshot、created_at、updated_at；模型快照不含密钥。
- `TaskStatus`：queued、running、cancel_requested、completed、failed、cancelled、interrupted。`TaskEvent(task_id, sequence, type, created_at, payload)`，sequence 从 1 开始。
- `ToolContext(task, inputs, results, cancel_event, publish_lock)`：inputs/results 只属于该任务；`InputSnapshot` 保存实际读取字节及 SHA-256；`TableResult` 保存 DataFrame、source_ids、input_hashes 和操作参数。
- `InputSnapshot`、`TableData`、`TableResult`、`ToolContext` 是内部 dataclass，在 contracts.py 定义，不作为HTTP请求/响应序列化；其中DataFrame只使用类型注解。公共模型使用Pydantic。
- `ToolOutcome(ok, data, source_ids, artifact_ids, error)` 必须能序列化为严格 JSON；数值 NaN/Inf 转换为 null，日期转换为 ISO 字符串。
- `Report(title, summary, sections, tables, citations)`；每条 citation 指向该任务的 source_id，附页/段落/行定位。
- 工具逻辑名保持规格中的点号形式；模型 wire 名映射为 `file_inspect`、`table_profile`、`table_transform`、`table_export`、`chart_create`、`document_extract`、`report_export`，解决兼容接口函数名限制。
- `table.transform` 固定执行顺序：筛选 → 去重 → 分组聚合 → 排序 → 选择列；每一步验证当时可用列。筛选操作为 eq/ne/gt/gte/lt/lte/contains/in/is_null/not_null，contains 按文字处理，不使用正则表达式。
- 测试数据：month/category/sales_amount 四行，金额 10、20、30、40；2026-01 对应 30，2026-02 对应 70。另有 BOM、GB18030、缺失值、重复行和公式样文本 fixture。
- 数据库默认 `.local-workbench/state.sqlite3`；staging 为工作区 `outputs/.staging/<taskId>`，最终产物目录为 `outputs/<taskId>`。文件扫描排除 outputs，避免自动把产物重新作为输入。
- endpoint 输入为 base URL（例如带 `/v1` 的地址），适配器追加 `/chat/completions`；不重复追加 `/v1`。未配置模型时只允许 profile 模式和浏览/预览。
- 生产前端由 FastAPI 提供静态 `frontend/dist`，使用同源 API；开发前端 `127.0.0.1:5173` 代理 `/api` 到后端。Host/Origin 仅允许明确的 localhost/127.0.0.1 对应地址。

## 依赖基线与执行命令

基线是 2026-10-12 读取当前 Python 环境和 npm 包元数据所得，用于首次安装锁定，执行时检查安装成功再产生锁文件。

- Python：fastapi 0.135.2、uvicorn 0.42.0、httpx 0.28.1、pydantic 2.12.5、pandas 2.3.3、openpyxl 3.1.5、python-docx 1.2.0、pypdf 6.9.1、matplotlib 3.10.6。
- Python 测试：pytest 8.4.2、pytest-asyncio 0.26.0。
- 前端：react/react-dom 19.3.0、vite 8.3.4、typescript 7.0.2、@vitejs/plugin-react 6.1.2；测试 vitest 5.0.4、@testing-library/react 16.3.3、@testing-library/jest-dom 7.0.1、jsdom 30.1.2、@playwright/test 1.64.0。
- @types/react/@types/react-dom 19.3.0；其余传递依赖由实际安装产生 requirements.lock.txt/package-lock.json。plugin-react 的 Vite peer 范围为 ^8.0.0，Vitest 5 支持 Vite 8 与当前 Node 24。
- 本计划执行基线为 Python 3.13.9 和 Node 24.13.1；无需为了本项目升级全局运行时。

下面的后端测试命令均在项目根执行：`.\.venv\Scripts\python.exe -m pytest backend/tests/<file> -q`。前端命令使用 `npm --prefix frontend ...`，避免依赖 PowerShell 当前目录。

---

### Task 1：可启动服务、项目环境和公共契约

**Files:** Create `.gitignore`、`backend/pyproject.toml`、`backend/workbench/__init__.py`、`backend/workbench/__main__.py`、`backend/workbench/config.py`、`backend/workbench/contracts.py`、`backend/workbench/errors.py`、`backend/workbench/app.py`；Test `backend/tests/conftest.py`、`backend/tests/test_app.py`、`backend/tests/test_contracts.py`。

**Interfaces:**
- Produces `AppConfig(app_root: Path, samples_root: Path, state_path: Path, port: int = 8765)` 和规格数值限额。
- Produces `create_app(config: AppConfig, *, model_factory: ModelFactory | None = None) -> FastAPI`；ModelFactory 签名为 `(ModelSettings, str | None) -> ModelClient`，后续Task 7实现。GET `/api/health` 返回 `{status: 'ok'}`。
- Produces contracts.py中的FileSelection/TaskCreate/TaskRecord/TaskEvent/TaskStatus、WorkspaceRecord/FileRecord/SourceRecord/ArtifactRecord、ModelSettings/ModelRequest/ModelEvent、Report/各Preview以及内部dataclass；后续任务完善对应类型字段，不另定义重名类型。Produces `WorkbenchError(code: str, message: str, status_code: int)`，HTTP 错误形式 `{error: {code, message}}`。

- [x] **Step 1：准备本项目环境。** 确认目录没有待保留产品代码后，在此目录初始化 Git；建立 `.venv`，声明并安装后端基线依赖及测试 extras；生成完整版本锁。忽略 .venv、.local-workbench、node_modules、dist、samples/outputs、缓存与 .env；不忽略示例输入和锁文件。
- [x] **Step 2：写失败测试。** `test_health_and_local_origin` 断言正常 health 为 200、恶意 Host/Origin 被拒绝；`test_contract_rejects_unknown_fields` 断言 TaskCreate 未知字段/非法模式失败；`test_limits_and_public_aliases` 断言限额精确值和 JSON 的 workspaceId/fileId。

  代表性断言（config和有效TaskCreate输入由conftest提供）：
  ```python
  client = TestClient(create_app(config), base_url="http://127.0.0.1:8765")
  assert client.get("/api/health").json() == {"status": "ok"}
  assert client.get("/api/health", headers={"Origin": "https://example.test"}).status_code == 403
  with pytest.raises(ValidationError):
      TaskCreate.model_validate({**valid_task_input, "executeShell": True})
  ```
- [x] **Step 3：确认失败。** Run `.\.venv\Scripts\python.exe -m pytest backend/tests/test_app.py backend/tests/test_contracts.py -q`；Expected 因导入/路由未实现失败，不应是环境依赖损坏。
- [x] **Step 4：实现并复测。** 实现上述入口、契约和异常/本机请求检查；CLI 支持 `python -m workbench --host 127.0.0.1 --port 8765`。运行同一测试，Expected PASS；启动检查 `/api/health`，无模型配置也能启动。
- [x] **Step 5：提交。** `git add .gitignore backend docs`；`git commit -m "chore: initialize local workbench service and contracts"`。

**2026-10-12 执行说明：** Task 1 已按用户本次范围验收并提交（e03589f）；无行为契约、ModelFactory 和文件处理依赖延后，Windows 原生台账替代 Bash 辅助脚本。完整裁决、实际命令与验证见 [T001](../../development/tasks/T001-2026-10-12-backend-scaffold.md)，Git 交付见 T002。

### Task 2：SQLite、事件事务和历史恢复

**Files:** Create `backend/workbench/storage.py`、`backend/tests/test_storage.py`；Modify `backend/workbench/app.py`、`backend/workbench/contracts.py`。

**Interfaces:**
- Consumes `AppConfig`、`TaskCreate`、`TaskRecord`、`TaskEvent`。
- Produces `Repository(state_path: Path)`：`create_task(request, workspace, model_snapshot) -> TaskRecord`；`append_event(task_id, event_type, payload, new_status=None) -> TaskEvent`；`events_after(task_id, sequence) -> list[TaskEvent]`；`get_task(task_id)`、`list_tasks(workspace_id)`。
- Produces `save_workspace(record: WorkspaceRecord)`、`save_file(record: FileRecord)`、`save_source(task_id: str, record: SourceRecord)`、`save_artifact(record: ArtifactRecord)`，均返回保存记录；`get_artifact(artifact_id: str) -> ArtifactRecord`；`save_settings(settings: ModelSettings) -> None`；`recover_interrupted_tasks() -> list[TaskRecord]`。记录类型在 contracts.py 定义，密钥不在普通 settings 中。

- [ ] **Step 1：写失败测试。** `test_event_and_status_are_one_transaction` 注入插入失败，断言状态与事件都不改变；`test_sequences_are_monotonic` 断言事件 1/2/3、after=1 返回 2/3；`test_restart_recovers_running_tasks` 断言 running/cancel_requested 变 interrupted，queued/completed 保持；`test_settings_never_persist_secret` 检查密钥不能进入设置/任务快照。

  已创建的queued task作为fixture；事件写入和状态必须一起生效：
  ```python
  event = repo.append_event(task.id, "task_started", {}, new_status="running")
  assert event.sequence == 1
  assert repo.get_task(task.id).status == "running"
  assert repo.events_after(task.id, 1) == []
  ```
- [ ] **Step 2：确认失败。** Run 后端 `test_storage.py`；Expected repository 未实现导致 FAIL。
- [ ] **Step 3：实现仓储。** 建立 workspaces/files/tasks/task_events/sources/artifacts/settings，启用 foreign_keys 和 WAL；单连接使用check_same_thread=False，仓储方法由RLock保护；事件与状态事务化，任务队列顺序使用创建时间/id。应用 lifespan 打开、恢复并关闭 Repository，不自动执行重启前任务。
- [ ] **Step 4：复测。** Run `test_storage.py` 和 `test_app.py`；Expected PASS，重新打开相同数据库仍可读取任务及事件。
- [ ] **Step 5：提交。** `git add backend`；`git commit -m "feat: persist workspaces tasks events and artifacts"`。

### Task 3：工作区、CSV/XLSX 读取和文件预览

**Files:** Create `backend/workbench/workspace.py`、`backend/workbench/tables.py`、`backend/workbench/api.py`、`backend/tests/test_workspace.py`、`backend/tests/test_table_readers.py`、`backend/tests/test_files_api.py`、`samples/sales.csv`；Modify app.py/contracts.py。

**Interfaces:**
- Produces `WorkspaceService(repo)`：`set_root(root: Path) -> WorkspaceRecord`、`list_files(workspace_id) -> list[FileRecord]`、`read_snapshot(workspace_id, file_id) -> InputSnapshot`。
- Produces `TableService.read(snapshot: InputSnapshot, sheet: str | None) -> TableData` 和 `preview_table(table: TableData) -> TablePreview`，TableData 包含 frame、sheet、source hash；所有公共 rows 是严格 JSON。
- Produces POST `/api/workspaces`、GET `/api/workspaces/current`、GET `/api/workspaces/{id}/files?query=`、POST `/api/files/{id}/preview`（body 包含 sheet）。WorkspaceRecord的root不可原位修改；更换目录创建/激活对应记录，持久化active workspace。首次启动默认注册samples，后续启动恢复已选工作区。

- [ ] **Step 1：写失败测试。** `test_resolved_path_stays_inside_root` 检查 ..、symlink 和 Windows junction；`test_scan_excludes_outputs`；`test_workspace_snapshot_is_not_changed_by_switch`；`test_csv_encodings` 覆盖 UTF-8/BOM/GB18030；`test_sheet_limits_and_preview` 断言错误 sheet、50 MiB+1 字节、100001 行、201 列被拒绝，预览最多100行；`test_json_has_no_nan_or_infinity`。

  预览和读取限制使用实际表格fixture：
  ```python
  preview = preview_table(table_with_101_rows)
  assert len(preview.rows) == 100
  assert preview.row_count == 101
  with pytest.raises(WorkbenchError) as error:
      tables.read(snapshot_with_100001_rows, sheet=None)
  assert error.value.code == "TABLE_ROW_LIMIT"
  ```
- [ ] **Step 2：确认失败。** Run test_workspace.py/test_table_readers.py/test_files_api.py；Expected 服务未实现 FAIL。junction 用临时 NTFS 目录建立真实 fixture；若系统阻止创建，明确记录未验证，不能用跳过冒充覆盖。
- [ ] **Step 3：实现读取与 API。** 路径 resolve 后校验相对 containment，再读字节并记录实际 SHA-256；工具只能用登记 ID。CSV UTF-8-sig 覆盖 BOM/普通 UTF-8，失败后用 GB18030；XLSX 显式 worksheet，读取上限+1 行检测超限。文件扫描只登记 metadata，预览才读内容；不加载整个目录正文。
- [ ] **Step 4：复测。** 同一测试 Expected PASS；真实 health/files/preview API 能读取自建 sales.csv，原文件 hash 不变。
- [ ] **Step 5：提交。** `git add backend samples`；`git commit -m "feat: browse workspaces and preview tabular files"`。

### Task 4：文档提取、来源定位和文本预览

**Files:** Create `backend/workbench/documents.py`、`backend/tests/test_documents.py`、`backend/tests/fixture_builders.py`、`scripts/create_samples.py`、`samples/README.md`；Modify contracts.py/api.py。

**Interfaces:**
- Consumes `InputSnapshot`、Repository.save_source。
- Produces `DocumentService.extract(snapshot, selection: DocumentSelection, max_characters: int = 12000) -> DocumentExtract`；selection 支持页范围/段落范围。
- `DocumentExtract` 包含 source_id、文本、file_id、input_hash、页/段落/字符定位及 truncated；TXT/MD 为文本位置，DOCX 为段落位置，PDF 为页位置。
- Produces文档 `FilePreview`，扫描 PDF 返回 `PDF_NO_EXTRACTABLE_TEXT`。

- [ ] **Step 1：写失败测试。** `test_docx_and_pdf_citations_point_to_real_text` 用已知正文 fixture 验证位置/文本/hash；`test_fragment_is_capped_at_12000`；`test_blank_pdf_reports_no_text`；`test_corrupt_or_unknown_document_is_not_success`；`test_text_preview_does_not_execute_html`。

  用含已知正文的文档快照，而不是mock提取结果：
  ```python
  result = documents.extract(known_docx, DocumentSelection(), max_characters=12000)
  assert "Sample revenue is 100" in result.text
  assert result.input_hash == known_docx.sha256
  assert result.location.paragraph_start == 1
  assert len(result.text) <= 12000
  ```
- [ ] **Step 2：确认失败。** Run test_documents.py，Expected FAIL；fixture builder 用 python-docx/pypdf 和一个本地最小有效文本 PDF，不联网、不读取个人文件。
- [ ] **Step 3：实现提取。** 使用 python-docx/pypdf，保留真实位置，不由模型编造来源；TXT/MD 作为文字。提取器生成SourceRecord，preview不绑定任务；Task 8工具执行时以save_source(task_id, record)绑定任务，报告引用只接受该任务记录。样本生成脚本仅生成项目 samples 下的输入文件，存在时不覆盖；为 XLSX、DOCX、文本 PDF 写使用说明。
- [ ] **Step 4：复测。** Expected PASS；对自建 samples 文档调用 preview API，显示原文和定位；无文本 PDF 得到具体错误。
- [ ] **Step 5：提交。** `git add backend scripts samples`；`git commit -m "feat: extract documents with verifiable source locations"`。

### Task 5：数据概览、转换和任务内结果

**Files:** Modify `backend/workbench/tables.py`、contracts.py；Create `backend/tests/test_table_transforms.py`。

**Interfaces:**
- Produces `TableService.profile(table: TableData) -> TableProfile`，含行列统计、missing counts、20行模型样本和100行UI样本。
- Produces `TableService.transform(table: TableData, request: TransformRequest) -> TableResult`。
- `TransformRequest` 明确定义 FilterSpec、SortSpec、AggregateSpec、deduplicate_by、select_columns；AggregateSpec 包含 column、function、output_column。
- `ResultStore` 为任务内字典：`put(result) -> result_id`、`get(result_id) -> TableResult`；不能读其他任务的 ID，工具循环终止后释放 DataFrame。

- [ ] **Step 1：写失败测试。** `test_month_totals_are_30_and_70` 精确比较分组值；`test_filter_sort_deduplicate_select_order`；`test_count_mean_min_max`；`test_unknown_column_and_mixed_type_fail_clearly`；`test_contains_is_literal_and_no_eval`；`test_result_ids_are_task_scoped`；确认输入 DataFrame/文件不被修改。

  按固定输入计算真实聚合：
  ```python
  request = TransformRequest(group_by=["month"], aggregates=[AggregateSpec(
      column="sales_amount", function="sum", output_column="total")])
  result = tables.transform(sales_table, request)
  assert result.frame["total"].tolist() == [30, 70]
  assert len(sales_table.frame) == 4
  ```
- [ ] **Step 2：确认失败。** Run test_table_transforms.py，Expected FAIL。
- [ ] **Step 3：实现转换。** 按固定顺序调用明确的 Pandas API，不使用 eval/query 拼接；每阶段检查列与类型，禁止非有限 filter 数值。结果记录 source_ids/input_hashes/操作参数；输出摘要 JSON 不含 DataFrame 或无限制全表。
- [ ] **Step 4：复测。** reader/transform 测试 Expected PASS；用固定 CSV 验证概览、去重、聚合等实际结果。
- [ ] **Step 5：提交。** `git add backend`；`git commit -m "feat: add controlled table profiling and transformations"`。

### Task 6：真实导出、产物发布和预览

**Files:** Create `backend/workbench/exporters.py`、`backend/workbench/artifacts.py`、`backend/tests/test_exporters.py`、`backend/tests/test_artifact_publish.py`；Modify contracts.py/api.py。

**Interfaces:**
- Produces `write_xlsx(result: TableResult, destination: Path)`、`write_chart(result, request: ChartRequest, destination)`、`write_report(report: Report, format: Literal['docx','markdown'], destination)`。
- Produces `async ArtifactService.publish(ctx: ToolContext, staged_path: Path, artifact_type, sources) -> ArtifactRecord`、`preview(artifact_id) -> ArtifactPreview`、`download_path(artifact_id) -> Path`。写入/校验在同步工具线程中完成；publish在事件循环中持asyncio.Lock执行短暂rename/登记。
- Publishes只在持有 ctx.publish_lock、状态仍 running 且未取消时；原子 rename 后才登记 artifact_ready。
- Produces GET `/api/tasks/{id}/artifacts`、GET `/api/artifacts/{id}/preview`、GET `/api/artifacts/{id}/download`。

- [ ] **Step 1：写失败测试。** `test_xlsx_reopens_with_values_and_source_sheet`；`test_formula_like_text_remains_text` 断言 `=1+1` 的 cell.value 不变且 data_type 为 s；`test_docx_contains_sections_and_sources` 重新打开 DOCX；`test_chart_png_has_dimensions_and_pixels`；`test_unknown_citation_is_rejected`；`test_cancel_before_publish_creates_no_artifact`；`test_output_junction_and_existing_file_are_rejected`；失败导出不登记成功。

  用真实openpyxl重读，不能只断言文件存在：
  ```python
  write_xlsx(result_with_formula_like_text, destination)
  workbook = openpyxl.load_workbook(destination)
  assert workbook["Data"]["A2"].value == "=1+1"
  assert workbook["Data"]["A2"].data_type == "s"
  assert "Sources" in workbook.sheetnames
  ```
- [ ] **Step 2：确认失败。** Run test_exporters.py/test_artifact_publish.py，Expected FAIL。
- [ ] **Step 3：实现导出与发布。** XLSX 保存数据和来源 sheet，文字显式作为文字，不执行公式；DOCX 使用中文字体、章节和来源附录；Markdown 明确引用；Matplotlib 使用 Agg，图表正确映射已知列。生成 staging 文件后用真实库重读/图片头校验，再持锁发布。不存在合法引用的报告不得发布。
- [ ] **Step 4：复测。** Expected PASS；从 API 下载并重读 XLSX/DOCX/PNG；预览返回结构化表/报告/图片 URL，无任意路径下载入口。
- [ ] **Step 5：提交。** `git add backend`；`git commit -m "feat: export and publish validated workbook report and chart artifacts"`。

### Task 7：模型设置、密钥生命周期和兼容流

**Files:** Create `backend/workbench/model.py`、`backend/tests/test_model.py`；Modify contracts.py/api.py/app.py。

**Interfaces:**
- Consumes contracts.py的 `ModelSettings(base_url: str, model: str)`；Produces `SecretStore.set_key(key: str | None)`、`SecretStore.get_key() -> str | None`；普通设置返回 configured 布尔值，不返回密钥。
- Produces `ModelClient(settings: ModelSettings, api_key: str | None, *, transport: httpx.AsyncBaseTransport | None = None)`；`stream(request: ModelRequest, cancel_event: asyncio.Event) -> AsyncIterator[ModelEvent]`。ModelEvent.kind 为 text_delta/tool_call/turn_end，tool_call 有 call_id、wire_name、完整 arguments。
- ModelRequest 包含 messages、tools、model 和120秒超时；默认工厂产生 HTTPX 客户端，测试注入 MockTransport，无产品级假模型开关。
- Produces GET/PUT `/api/settings/model`、POST `/api/settings/model/check`；check 是用户明确触发的连接检查。

- [ ] **Step 1：写失败测试。** `test_fragmented_multiple_tool_calls_are_assembled` 分片同时覆盖 UTF-8 文本与两个call；`test_base_url_path_is_preserved`；`test_missing_tool_support_is_explicit`；`test_timeout_and_cancel_stop_stream`；`test_auth_errors_are_redacted`；`test_key_is_absent_from_database_and_responses`。

  fixture流把JSON参数分成多个data frame；收到的调用必须完整且唯一：
  ```python
  events = [event async for event in client.stream(request, cancel_event)]
  calls = [event for event in events if event.kind == "tool_call"]
  assert len(calls) == 2
  assert calls[0].wire_name == "table_profile"
  assert calls[0].arguments == {"fileId": selected_file_id}
  ```
- [ ] **Step 2：确认失败。** Run test_model.py，Expected FAIL；用 HTTPX MockTransport 提供真实格式 SSE frame、401、429、损坏 JSON 和延迟流。
- [ ] **Step 3：实现适配。** 发送 Chat Completions 请求，按 index/id 合并工具参数分片，完成后严格 JSON 解码；校验 URL/模型配置，追加路径一次；超时/取消关闭 response/client。初始化可以从 WORKBENCH_API_KEY 读取；API GET/日志/TaskRecord 均不能序列化 secret。
- [ ] **Step 4：复测。** Expected PASS；检查 OpenAPI 和设置响应；未配置模型时仍可 health/files/preview，不产生远端请求。
- [ ] **Step 5：提交。** `git add backend`；`git commit -m "feat: configure compatible models and parse cancellable streams"`。

### Task 8：工具注册、Agent 循环、队列、取消与 SSE

**Files:** Create `backend/workbench/tools.py`、`backend/workbench/runner.py`、`backend/tests/test_tools.py`、`backend/tests/test_runner.py`、`backend/tests/test_events_api.py`；Modify contracts.py/api.py/app.py。

**Interfaces:**
- Consumes Repository、WorkspaceService、TableService、DocumentService、ArtifactService、ModelClient、ToolContext。
- Produces `ToolRegistry.schemas() -> list[dict]`；`async execute(ctx, call_id: str, wire_name: str, arguments: dict) -> ToolOutcome`，七个 wire 名映射固定逻辑名。
- Produces `TaskRunner.enqueue(request: TaskCreate) -> TaskRecord`、`async cancel(task_id: str) -> TaskRecord`、`async start() -> None`、`async run_task(task_id: str) -> None`、`async close() -> None`。start由应用lifespan调用；独立单元测试可直接run_task。
- Produces `AgentLoop.run(ctx, client, emit: Callable[[str, dict], Awaitable[None]]) -> TaskStatus`。
- Produces POST/GET `/api/tasks`、GET `/api/tasks/{id}`、POST `/api/tasks/{id}/cancel`、GET `/api/tasks/{id}/events?after=`。SSE id 为 sequence，接受 Last-Event-ID，断线重放持久化事件。

- [ ] **Step 1：写失败测试。** `test_tool_call_result_next_turn` 验证模型收到上轮 tool result；`test_unknown_tool_extra_fields_and_foreign_file_are_rejected`；`test_duplicate_call_id_executes_once`（同ID不同参数拒绝）；`test_turn_limit_is_12_and_report_repair_is_once`；`test_one_active_task_and_queue_order`；`test_cancel_cannot_publish_or_complete`；`test_profile_needs_no_model`；`test_sse_reconnect_replays_after_cursor`；`test_restart_preserves_artifacts_and_interrupts_running`。

  runner fixture不启动后台worker，直接运行一个profile任务检查无模型闭环：
  ```python
  task = runner.enqueue(profile_request)
  await runner.run_task(task.id)
  assert repo.get_task(task.id).status == "completed"
  assert fake_model.requests == []
  assert any(event.type == "tool_finished" for event in repo.events_after(task.id, 0))
  ```
- [ ] **Step 2：确认失败。** Run test_tools.py/test_runner.py/test_events_api.py，Expected FAIL。
- [ ] **Step 3：实现执行链。** 单一后台 worker 消费SQLite任务；选中文件和工作区根快照绑定到 ctx，per-task锁供cancel/publish共用。同步工具通过 asyncio.to_thread 运行，返回后检查取消；HTTP模型流可取消。每次工具调用发开始/结束事件；处理未知/坏参数为可修正 ToolOutcome，不执行字符串代码。重复call复用相同结果；严重错误/轮数上限标 failed。profile 仅允许一个选中表格，直接计算概览并持久化摘要事件；多选或文档返回 PROFILE_REQUIRES_SINGLE_TABLE。
- [ ] **Step 4：复测。** Expected PASS；端点使用真实 Repository＋测试 ModelClient 完成聚合→导出，20行模型样本/12000字符上限、20个以上上下文行不自动发送均有断言。SSE 从持久化事件分页追赶，终态客户端可关闭订阅。
- [ ] **Step 5：提交。** `git add backend`；`git commit -m "feat: run scoped agent tasks with queue cancellation and replayable events"`。

### Task 9：三栏工作台、历史、设置和预览

**Files:** Create frontend/package.json/package-lock.json/tsconfig.json/vite.config.ts/index.html；frontend/src/main.tsx/api.ts/types.ts/task-state.ts/App.tsx/styles.css；components/WorkspacePanel.tsx、TaskPanel.tsx、PreviewPanel.tsx、SettingsDialog.tsx；tests/task-state.test.ts、tests/workbench.test.tsx、tests/setup.ts。

**Interfaces:**
- Consumes现有 HTTP contract；`api.ts` 导出 setWorkspace/listFiles/previewFile/createTask/listTasks/getTask/cancelTask/listArtifacts/previewArtifact/updateModel/checkModel。
- Produces `subscribeTaskEvents(taskId: string, after: number, onEvent: (event: TaskEvent) => void): () => void`。
- Produces `applyTaskEvent(state: TaskViewState, event: TaskEvent) -> TaskViewState`，拒绝旧/重复 sequence；检测序号缺口后请求补齐，不直接跳过。
- Produces `createTaskView(task: TaskRecord) -> TaskViewState`；公共TaskEvent/TaskRecord等JSON类型与后端camelCase契约一致。

- [ ] **Step 1：准备前端环境。** 按依赖基线配置 npm scripts dev/typecheck/test/build/e2e；安装产生 package-lock。Vite 监听 127.0.0.1:5173，代理 /api；实现阶段先应用适合新工作台界面的前端设计技能，沿用此规格范围。
- [ ] **Step 2：写失败测试。** `duplicate_or_stale_events_are_not_applied`；`gap_triggers_replay`；`file_selection_and_sheet_are_sent_in_task`；`profile_works_when_model_is_unconfigured`；`task_errors_keep_partial_artifacts`；`settings_clears_key_after_submit`；`document_text_is_escaped`；`cancel_requested_is_distinct_from_cancelled`。

  用类型化task/event fixture验证重连后的重复事件不会再次应用：
  ```typescript
  const state = createTaskView(task);
  const once = applyTaskEvent(state, firstEvent);
  const twice = applyTaskEvent(once, firstEvent);
  expect(twice.lastSequence).toBe(1);
  expect(twice.events).toHaveLength(1);
  ```
- [ ] **Step 3：确认失败。** Run `npm --prefix frontend run test -- --run`；Expected 组件/状态方法缺失导致 FAIL，不是浏览器环境配置错误。
- [ ] **Step 4：实现并验证。** 中文三栏界面和明确的空/加载/错误/取消状态；文件选择、worksheet、任务输入和历史；表格、文档引用和PNG产物预览/下载；设置不回显已保存key。Run test/typecheck/build，Expected全部PASS；无模型只禁用Agent提交，不禁用文件功能。
- [ ] **Step 5：提交。** `git add frontend`；`git commit -m "feat: add file task and artifact workbench interface"`。

### Task 10：端到端、本机启动和交付文档

**Files:** Create backend/tests/test_integration.py、backend/tests/test_restart.py；frontend/tests/workbench.e2e.ts、frontend/playwright.config.ts；scripts/setup-workbench.ps1、start-workbench.ps1、README.md；Modify app.py/__main__.py、samples/README.md、.gitignore。

**Interfaces:**
- FastAPI 在生产模式提供已构建 frontend/dist，并保持 /api 优先和有效SPA fallback。
- `start-workbench.ps1` 使用项目 .venv，检查依赖/前端构建，启动 127.0.0.1:8765；不自动占用其他端口，不关闭不属于本应用的进程。
- setup-workbench.ps1 仅安装本项目依赖并生成样本；运行/日志路径可在README复现。

- [ ] **Step 1：写失败测试。** `test_sales_task_exports_30_and_70` 重读真实XLSX并检查PNG；`test_cited_document_exports_valid_docx`；`test_cancel_and_failure_leave_no_new_artifact`；`test_restart_has_history_and_downloads`。浏览器流程通过测试应用工厂注入模型，覆盖选目录→预览→任务→工具状态→产物→重连→历史；生产无测试模型选项。

  集成fixture执行实际任务并由产物登记取得导出路径：
  ```python
  assert finished_task.status == "completed"
  workbook = openpyxl.load_workbook(exported_xlsx, data_only=True)
  assert [workbook["Data"][f"B{row}"].value for row in (2, 3)] == [30, 70]
  assert input_path.read_bytes() == original_input_bytes
  ```
- [ ] **Step 2：确认失败。** Run后端integration/restart以及 `npm --prefix frontend run e2e`；Expected 尚未串联的环节失败，记录实际原因。
- [ ] **Step 3：完成组装与启动。** 实现同源静态服务、优雅停机和重启恢复；setup脚本使用项目锁文件；启动脚本检查端口并提供具体冲突提示。若需后台辅助进程，PowerShell Start-Process 使用 WindowStyle Hidden；退出只处理记录的本项目PID。README说明目录选择、模型配置、无模型概览、格式/限额、输出目录、取消语义和重启恢复。
- [ ] **Step 4：最终验证。** Run `.\.venv\Scripts\python.exe -m pytest backend/tests -q`、`npm --prefix frontend run test -- --run`、`npm --prefix frontend run typecheck`、`npm --prefix frontend run build`、`npm --prefix frontend run e2e`。Expected PASS；启动实际构建版，在真实浏览器检查三栏、长路径/长文件名、中文显示和窄窗口；重读示例产物，核对输入hash未变。真实模型仅在用户已配置服务时验证，未配置则明确保留此验证项。
- [ ] **Step 5：提交并记录。** `git add backend frontend scripts samples start-workbench.ps1 README.md .gitignore docs`；`git commit -m "feat: ship validated local file and document workbench"`。记录命令结果、测试跳过项和模型验证范围，不以计划中的Expected代替实测结果。

## 里程碑与执行建议

| 里程碑 | 完成任务 | 可验收交付 |
|---|---|---|
| M1 | 1–4 | 可启动API、持久化、工作区、表格及文档预览 |
| M2 | 5–6 | 实际计算结果、有效XLSX/DOCX/PNG及产物API |
| M3 | 7–8 | 模型适配、完整Agent循环、队列、取消及SSE |
| M4 | 9–10 | 中文三栏工作台、一键启动、测试和使用说明 |

执行必须按 1→10 推进；后续任务消费前面 Interfaces，不能另建重复接口。每个任务完成专属验证后提交；新故障或修改再补对应验证，避免没有理由地反复跑全量检查。

推荐 **Native：在当前会话顺序实现**。十个任务依赖同一套 Python/HTTP/前端契约，单一实现上下文便于保持接口一致；完成后再进行一次独立整体评审。另一个选择是 subagent-driven：逐任务使用独立实现者和评审者，审查更密集，但上下文/协调开销更高。

本文件是实施计划，当前未执行依赖安装、Git初始化、产品代码或任务测试。用户评审计划并选择执行方式后，按对应执行技能开始实施。

## 计划自检

- 规格第3节文件/数据/文档/任务：Tasks 3–9；第4节界面和流程：Tasks 8–10。
- 第5–7节组件、工具与契约：Tasks 1–2、5–9；第8节错误/取消/一致性：Tasks 3、6–8。
- 第9节验收与交付：Tasks 4、6、8–10；第10节实施阶段对应M1–M4。
- 五项Review Focus均有明确测试归属；未加入规格范围外的桌面壳、OCR、网页采集、任意代码执行或插件平台。
- 文件名、类型、接口、JSON命名、状态、事件与取消语义前后一致；所有依赖版本是准备时读取的基线，锁文件由实际安装生成。
