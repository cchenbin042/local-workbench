from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError


def test_limits_and_public_aliases(config, valid_task_input):
    from workbench.contracts import TaskCreate

    assert (config.max_file_bytes, config.max_table_rows, config.max_table_columns) == (50 * 1024 * 1024, 100_000, 200)
    assert (config.preview_rows, config.model_sample_rows, config.document_characters, config.model_rounds, config.model_timeout_seconds) == (100, 20, 12_000, 12, 120)
    task = TaskCreate.model_validate(valid_task_input)
    public = task.model_dump(mode="json", by_alias=True)
    assert public["workspaceId"] == valid_task_input["workspaceId"]
    assert public["sources"][0]["fileId"] == valid_task_input["sources"][0]["fileId"]


@pytest.mark.parametrize("patch", [{"executeShell": True}, {"mode": "shell"}, {"sources": []}, {"prompt": "  "}, {"workspaceId": "not-a-uuid"}, {"sources": [{"fileId": "bad"}]}, {"sources": [{"fileId": str(uuid4()), "path": "C:/secret"}]}])
def test_contract_rejects_unknown_fields(valid_task_input, patch):
    from workbench.contracts import TaskCreate

    with pytest.raises(ValidationError):
        TaskCreate.model_validate({**valid_task_input, **patch})


def test_prompt_is_trimmed_and_internal_names_work(valid_task_input):
    from workbench.contracts import FileSelection, TaskCreate

    task = TaskCreate(workspace_id=valid_task_input["workspaceId"], sources=[FileSelection(file_id=valid_task_input["sources"][0]["fileId"])], prompt="  summarize  ", mode="agent")
    assert task.prompt == "summarize"


@pytest.mark.parametrize("sequence", [0, -1, True, "1", 1.5])
def test_event_sequence_is_a_positive_integer(sequence):
    from workbench.contracts import TaskEvent

    with pytest.raises(ValidationError):
        TaskEvent(task_id=uuid4(), sequence=sequence, type="task_started", created_at=datetime.now(timezone.utc), payload={})


def test_event_rejects_unknown_type_naive_time_and_non_json_payload():
    from workbench.contracts import TaskEvent

    base = dict(task_id=uuid4(), sequence=1, type="task_started", created_at=datetime.now(timezone.utc), payload={})
    event = TaskEvent(**base).model_dump(mode="json", by_alias=True)
    assert event["sequence"] == 1 and "taskId" in event and "createdAt" in event
    for patch in [{"type": "execute_shell"}, {"created_at": datetime.now()}, {"payload": {"value": float("nan")}}, {"payload": {"value": float("inf")}}, {"payload": {"object": object()}}]:
        with pytest.raises(ValidationError):
            TaskEvent(**{**base, **patch})


@pytest.mark.parametrize("patch", [{"host": "0.0.0.0"}, {"port": 0}, {"port": 65536}, {"port": True}])
def test_invalid_bind_configuration(tmp_path, patch):
    from workbench.config import AppConfig

    with pytest.raises(ValueError):
        AppConfig(app_root=tmp_path, **patch)
