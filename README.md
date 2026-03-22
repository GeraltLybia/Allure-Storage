# TestReport Storage

- English: see [README.en.md](./README.en.md)
- Русский: см. [README.ru.md](./README.ru.md)

This repository contains a production-ready split architecture:
- `frontend` (Vue 3 + Vite + Nginx)
- `backend` (FastAPI)
- `storage` (runtime data: reports and history files, ignored by git)

This project is designed to work with [allure-framework/allure3](https://github.com/allure-framework/allure3).
It is an independent product and is not affiliated with or endorsed by the upstream project.
The upstream reference is kept in this documentation to preserve attribution required by the Apache-2.0 license.

Backend service code uses the internal package `app/services/reporting` for report/history domain logic.

For API docs (Swagger/OpenAPI), run the backend and open:
- `/docs` (Swagger UI)
- `/redoc` (ReDoc)
- `/openapi.json` (OpenAPI spec)
