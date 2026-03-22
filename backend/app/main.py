from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import api_router
from .config import get_settings


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
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)
    application.mount(
        "/reports-static",
        StaticFiles(directory=settings.reports_folder, html=True),
        name="reports-static",
    )

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
