from uuid import uuid4

import pytest


@pytest.fixture
def config(tmp_path):
    from workbench.config import AppConfig

    return AppConfig(app_root=tmp_path)


@pytest.fixture
def valid_task_input():
    return {
        "workspaceId": str(uuid4()),
        "sources": [{"fileId": str(uuid4())}],
        "prompt": "Summarize selected file",
        "mode": "profile",
    }
