from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .api import api_router
from .config import get_settings


class StaticCorsMiddleware:
    """Adds permissive CORS headers to the static reports mount.

    Reports are rendered in a sandboxed iframe without ``allow-same-origin``,
    so the browser treats the document as an opaque origin and its internal
    data fetches as cross-origin. The static files are publicly readable via
    GET anyway, so ``*`` does not widen the exposure.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_cors(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers: list[tuple[bytes, bytes]] = [
                    (key, value) for key, value in message.get("headers") or []
                ]
                headers.append((b"access-control-allow-origin", b"*"))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_cors)


class LocalStorageShimMiddleware:
    """Injects an in-memory ``localStorage``/``sessionStorage`` shim into report HTML.

    Allure bundles read ``window.localStorage`` during bootstrap, which throws
    a ``DOMException`` in a sandboxed iframe without ``allow-same-origin`` and
    leaves the report blank. The shim keeps the iframe sandboxed (no
    ``allow-same-origin``) while letting the SPA start; values only live in
    the page memory for the lifetime of the report view.
    """

    SHIM = (
        b"<script>(function(){function shim(){var s={};var o={getItem:function(k){"
        b"return Object.prototype.hasOwnProperty.call(s,k)?s[k]:null},setItem:function(k,v){"
        b"s[k]=String(v)},removeItem:function(k){delete s[k]},clear:function(){s={}},"
        b"key:function(i){return Object.keys(s)[i]||null}};"
        b"Object.defineProperty(o,'length',{get:function(){return Object.keys(s).length}});"
        b"return o}function install(n,o){try{Object.defineProperty(window,n,"
        b"{value:o,configurable:true,writable:true})}catch(e){try{window[n]=o}catch(e2){}}}"
        b"install('localStorage',shim());install('sessionStorage',shim())})();</script>"
    )

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start: Message | None = None
        body_chunks: list[bytes] = []
        buffering = False

        async def flush_shimmed() -> None:
            nonlocal start
            html = b"".join(body_chunks)
            head = html.lower().find(b"<head")
            if head != -1:
                insert_at = html.index(b">", head) + 1
                html = html[:insert_at] + self.SHIM + html[insert_at:]
            headers: list[tuple[bytes, bytes]] = [
                (key, value)
                for key, value in (start or {}).get("headers") or []
                if key != b"content-length"
            ]
            headers.append((b"content-length", str(len(html)).encode("latin-1")))
            await send({**(start or {}), "headers": headers})
            await send({"type": "http.response.body", "body": html, "more_body": False})

        async def send_with_shim(message: Message) -> None:
            nonlocal start, buffering
            if message["type"] == "http.response.start":
                headers = message.get("headers") or []
                is_html = any(key == b"content-type" and b"text/html" in value for key, value in headers)
                if is_html:
                    start = message
                    buffering = True
                    return
                await send(message)
                return
            if message["type"] == "http.response.body" and buffering:
                body_chunks.append(message.get("body") or b"")
                if not message.get("more_body"):
                    buffering = False
                    await flush_shimmed()
                return
            await send(message)

        await self.app(scope, receive, send_with_shim)


def create_app() -> FastAPI:
    settings = get_settings()
    settings.storage_root.mkdir(exist_ok=True)
    settings.reports_folder.mkdir(parents=True, exist_ok=True)

    tags_metadata = [
        {
            "name": "reports",
            "description": "Управление отчетами Allure: список, загрузка, удаление и скачивание.",
        },
        {
            "name": "history",
            "description": "Работа с `history.jsonl`: загрузка, скачивание и просмотр метаданных.",
        },
        {
            "name": "system",
            "description": "Служебные endpoint'ы для проверки состояния сервиса.",
        },
    ]

    application = FastAPI(
        title=settings.api_title,
        description=(
            "API для хранения и просмотра Allure-отчетов.\n\n"
            "- Swagger UI: `/docs`\n"
            "- ReDoc: `/redoc`\n"
            "- OpenAPI JSON: `/openapi.json`"
        ),
        version="1.0.0",
        contact={
            "name": "TestReport Storage",
        },
        openapi_tags=tags_metadata,
    )
    if settings.cors_origins:
        # Only enable CORS when explicit origins are configured. A wildcard with
        # credentials is rejected by browsers and unsafe, so we never use "*" here.
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    application.include_router(api_router)
    static_reports = LocalStorageShimMiddleware(
        StaticCorsMiddleware(StaticFiles(directory=settings.reports_folder, html=True))
    )
    application.mount("/reports-static", static_reports, name="reports-static")

    @application.get(
        "/health",
        tags=["system"],
        summary="Проверка состояния API",
        description="Возвращает статус работы backend-сервиса.",
    )
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
