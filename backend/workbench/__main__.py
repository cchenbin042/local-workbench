import argparse
from pathlib import Path

import uvicorn

from workbench.app import create_app
from workbench.config import AppConfig


def port_number(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("端口必须是整数") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("端口范围为 1–65535")
    return port


def main() -> None:
    parser = argparse.ArgumentParser(description="启动本地工作台后端")
    parser.add_argument("--host", choices=["127.0.0.1"], default="127.0.0.1")
    parser.add_argument("--port", type=port_number, default=8765)
    parser.add_argument("--app-root", type=Path, default=Path.cwd())
    parser.add_argument("--log-level", choices=["critical", "error", "warning", "info", "debug"], default="info")
    args = parser.parse_args()
    config = AppConfig(app_root=args.app_root, host=args.host, port=args.port)
    uvicorn.run(create_app(config), host=config.host, port=config.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
