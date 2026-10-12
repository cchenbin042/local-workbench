from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from workbench.config import AppConfig
from workbench.errors import WorkbenchError, error_body


class LocalAccessMiddleware:
    """Exact Host/Origin checks before routes and CORS preflight handling."""

    def __init__(self, app: ASGIApp, hosts: set[str], origins: set[str]) -> None:
        self.app = app
        self.hosts = hosts
        self.origins = origins

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            hosts = [value.decode("latin-1") for name, value in scope["headers"] if name.lower() == b"host"]
            origins = [value.decode("latin-1") for name, value in scope["headers"] if name.lower() == b"origin"]
            if len(hosts) != 1 or hosts[0] not in self.hosts or len(origins) > 1 or (origins and origins[0] not in self.origins):
                response = JSONResponse(error_body("LOCAL_ACCESS_DENIED", "仅允许明确的本机 Host 和 Origin"), status_code=403)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


def create_app(config: AppConfig) -> FastAPI:
    app = FastAPI(title="Local Workbench", version="0.1.0")
    app.state.config = config
    hosts = {f"{host}:{config.port}" for host in ("127.0.0.1", "localhost")}
    if config.port == 80:
        hosts.update({"127.0.0.1", "localhost"})
    origins = {f"http://{host}" for host in hosts}
    origins.update({"http://127.0.0.1:5173", "http://localhost:5173"})
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(origins),
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Last-Event-ID"],
    )
    # Last added is outermost, including OPTIONS requests.
    app.add_middleware(LocalAccessMiddleware, hosts=hosts, origins=origins)

    @app.exception_handler(WorkbenchError)
    async def workbench_error_handler(request: Request, exc: WorkbenchError) -> JSONResponse:
        return JSONResponse(error_body(exc.code, exc.message), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Validation input may contain future model credentials; never echo it.
        return JSONResponse(error_body("INVALID_REQUEST", "请求参数不符合接口约定"), status_code=422)

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(error_body("HTTP_ERROR", f"请求未成功（HTTP {exc.status_code}）"), status_code=exc.status_code, headers=exc.headers)

    @app.get("/api/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
