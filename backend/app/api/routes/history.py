from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from ...dependencies import get_history_service
from ...schemas.history import HistoryDashboardSummary, HistoryInfo, HistorySelectedTestDetails
from ...schemas.report import MessageResponse
from ...services.reporting import HistoryService

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get(
    "",
    summary="Скачать history.jsonl",
    description="Возвращает текущий файл `history.jsonl` из хранилища.",
    responses={404: {"description": "Файл history не найден"}},
)
async def download_history(service: HistoryService = Depends(get_history_service)):
    history_path = service.get_history_path()
    return FileResponse(
        path=history_path,
        filename="history.jsonl",
        media_type="application/x-jsonlines",
    )


@router.post(
    "",
    response_model=MessageResponse,
    summary="Загрузить history.jsonl",
    description="Принимает и валидирует JSONL-файл истории, затем сохраняет его в хранилище.",
    responses={
        400: {"description": "Некорректный формат файла history"},
        500: {"description": "Внутренняя ошибка при сохранении history"},
    },
)
async def upload_history(
    file: UploadFile = File(...),
    service: HistoryService = Depends(get_history_service),
):
    return await service.upload_history(file)


@router.post(
    "/rebuild-index",
    response_model=MessageResponse,
    summary="Полностью перестроить history index",
    description="Принудительно перечитывает весь `history.jsonl` и заново собирает `history_index.json`.",
    responses={
        404: {"description": "Файл history не найден"},
        500: {"description": "Внутренняя ошибка при перестроении index"},
    },
)
async def rebuild_history_index(service: HistoryService = Depends(get_history_service)):
    return service.rebuild_history_index()


@router.get(
    "/info",
    response_model=HistoryInfo,
    summary="Получить метаданные history",
    description="Возвращает количество записей, время обновления и размер `history.jsonl`.",
)
async def get_history_info(service: HistoryService = Depends(get_history_service)):
    return service.history_info()


@router.get(
    "/dashboard",
    response_model=HistoryDashboardSummary,
    summary="Получить агрегаты dashboard",
    description="Возвращает агрегированные метрики dashboard из history index без скачивания всего JSONL.",
)
async def get_history_dashboard(
    tags: str | None = None,
    suite: str | None = None,
    environment: str | None = None,
    signature: str | None = None,
    stopFrom: int | None = None,
    stopTo: int | None = None,
    service: HistoryService = Depends(get_history_service),
):
    parsed_tags = [item.strip() for item in (tags or "").split(",") if item.strip()]
    return service.get_history_dashboard(
        tags=parsed_tags,
        suite=suite,
        environment=environment,
        signature=signature,
        stop_from=stopFrom,
        stop_to=stopTo,
    )


@router.get(
    "/dashboard/tests/{test_key:path}",
    response_model=HistorySelectedTestDetails,
    summary="Получить детали теста для dashboard",
    description="Возвращает историю выбранного теста из индекса с учётом фильтров dashboard.",
    responses={404: {"description": "Тест не найден для текущего набора фильтров"}},
)
async def get_history_test_details(
    test_key: str,
    tags: str | None = None,
    suite: str | None = None,
    environment: str | None = None,
    signature: str | None = None,
    stopFrom: int | None = None,
    stopTo: int | None = None,
    service: HistoryService = Depends(get_history_service),
):
    parsed_tags = [item.strip() for item in (tags or "").split(",") if item.strip()]
    details = service.get_history_test_details(
        test_key=test_key,
        tags=parsed_tags,
        suite=suite,
        environment=environment,
        signature=signature,
        stop_from=stopFrom,
        stop_to=stopTo,
    )
    if details is None:
        raise HTTPException(status_code=404, detail="Test not found")
    return details
