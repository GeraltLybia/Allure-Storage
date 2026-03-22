# TestReport Storage

Веб-приложение для хранения и просмотра тестовых отчетов Allure.

Проект предназначен для работы с [allure-framework/allure3](https://github.com/allure-framework/allure3).
Это независимый продукт, не аффилированный с upstream-проектом и не одобренный им.
Упоминание upstream-проекта добавлено в документацию, чтобы сохранить требуемую атрибуцию по лицензии Apache-2.0.

## Структура проекта
- `frontend` - приложение на Vue 3 (интерфейс управления и просмотр отчетов)
- `backend` - сервис на FastAPI (загрузка/скачивание/список/удаление отчетов, работа с history)
- `storage` - runtime-директория для отчетов и `history.jsonl`, находится в `.gitignore`
- `docker-compose.yml` - orchestration контейнеров для production-like запуска

## Backend-структура
Внутренний backend-код для домена отчетов и history теперь лежит в пакете `app/services/reporting`.

Логика разделена по слоям:
- `app/services/reporting/reports.py` - сервис работы с отчетами
- `app/services/reporting/history.py` - сервис работы с `history.jsonl`
- `app/services/reporting/history_index.py` - построение и обновление `history_index.json`
- `app/services/reporting/analytics.py` - агрегаты для dashboard
- `app/services/reporting/repositories/` - файловые repository-слои
- `app/services/reporting/models.py` - внутренние typed-модели

Это сделано специально, чтобы не путать кодовый пакет с runtime-папкой `storage/`.

## Документация API (Swagger/OpenAPI)
Когда backend запущен:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

В Docker-развертывании (через прокси frontend):
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`
- OpenAPI JSON: `http://localhost:8080/openapi.json`

## Запуск через Docker (Рекомендуется)
```bash
cd /Users/zaharpirozenko/Documents/allure3_folder
docker compose up --build
```

Адреса:
- UI приложения: `http://localhost:8080`
- Backend (внутри docker-сети): `backend:8000`

Остановка:
```bash
docker compose down
```

## Локальный запуск для разработки
### Backend
```bash
cd /Users/zaharpirozenko/Documents/allure3_folder/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd /Users/zaharpirozenko/Documents/allure3_folder/frontend
npm ci
npm run dev
```

Frontend dev server: `http://localhost:5173`

## Основные возможности
- Отдельная страница Dashboard для QA-аналитики по истории прогонов
- Загрузка архивов отчетов Allure (`.zip`)
- Просмотр списка загруженных отчетов
- Встроенный просмотр отчетов в iframe
- Скачивание и удаление отчетов
- Загрузка/скачивание `history.jsonl`
- History-based метрики из `history.jsonl`: pass rate, unstable/flaky tests, failure signatures, tag health, trends
- Фильтры на Dashboard по `tag`, `suite`, `environment` и `failure signature`
- Deep-link фильтров через query-параметры URL на странице Dashboard
- Автоматическая ротация отчетов по лимиту (по умолчанию храним 10 последних)
- Healthcheck endpoint: `GET /health`

## History API
- `GET /api/history` - скачать текущий `history.jsonl`
- `POST /api/history` - загрузить новый `history.jsonl`
- `GET /api/history/info` - получить метаданные `history.jsonl`
- `GET /api/history/dashboard` - получить агрегаты dashboard без скачивания всего файла
- `GET /api/history/dashboard/tests/{test_key}` - получить детали выбранного теста для dashboard
- `POST /api/history/rebuild-index` - принудительно полностью перечитать `history.jsonl` и пересобрать `history_index.json`

## Dashboard
Dashboard доступен по адресу `http://localhost:8080/dashboard` в Docker-развертывании
или `http://localhost:5173/dashboard` в dev-режиме frontend.

Что показывает Dashboard:
- KPI по истории прогонов: runs, unique tests, pass rate, p95 duration
- Stability-блок: flaky tests, always failed, always passed, incidents
- Тренд последних прогонов по статусам `passed / failed / broken`
- Самые нестабильные тесты
- Топ failure signatures
- Health по тегам
- Быстрые переходы в последние и проблемные отчеты

Как используются данные:
- Summary по отчетам берется из распакованных Allure-отчетов
- QA-метрики и тренды строятся по агрегированному индексу `storage/history_index.json`
- `history_index.json` создается лениво при первой обработке `history.jsonl` и не требуется для старта сервиса
- При загрузке нового `history.jsonl`, если файл дописан в конец, backend обычно дочитывает только новый хвост и обновляет индекс инкрементально
- Если индекс отсутствует, поврежден или есть сомнение в консистентности, можно вызвать `POST /api/history/rebuild-index` для полного rebuild из текущего `history.jsonl`
- Если `history.jsonl` не загружен, dashboard показывает только пустое состояние для history-based виджетов

Интерактивность:
- Клик по карточкам в Stability открывает список конкретных тестов
- Из попапа Stability можно выбрать тест и открыть блок `Test Details`
- Клик по tag health и failure signatures включает соответствующий фильтр

## Конфигурация
Переменные окружения backend:
- `APP_STORAGE_ROOT` - путь к директории хранения (по умолчанию: `storage`)
- `APP_MAX_REPORTS` - максимальное количество хранимых отчетов (по умолчанию: `10`)

Поведение ротации:
- После загрузки нового отчета, если общее количество превышает `APP_MAX_REPORTS`,
  автоматически удаляются самые старые директории отчетов.
