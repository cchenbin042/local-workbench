from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    app_root: Path
    samples_root: Path | None = None
    state_path: Path | None = None
    host: str = "127.0.0.1"
    port: int = 8765
    max_file_bytes: int = field(default=50 * 1024 * 1024, init=False)
    max_table_rows: int = field(default=100_000, init=False)
    max_table_columns: int = field(default=200, init=False)
    preview_rows: int = field(default=100, init=False)
    model_sample_rows: int = field(default=20, init=False)
    document_characters: int = field(default=12_000, init=False)
    model_rounds: int = field(default=12, init=False)
    model_timeout_seconds: int = field(default=120, init=False)

    def __post_init__(self) -> None:
        if self.host != "127.0.0.1":
            raise ValueError("服务只能绑定 127.0.0.1")
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError("端口必须是 1–65535 的整数")
        root = Path(self.app_root).resolve()
        object.__setattr__(self, "app_root", root)
        object.__setattr__(self, "samples_root", Path(self.samples_root or root / "samples").resolve())
        object.__setattr__(self, "state_path", Path(self.state_path or root / ".local-workbench" / "state.sqlite3").resolve())
