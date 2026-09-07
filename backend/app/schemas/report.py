from pydantic import BaseModel


class ReportStats(BaseModel):
    total: int = 0
    passed: int = 0
    failed: int = 0
    flaky: int = 0
    broken: int = 0


class ReportItem(BaseModel):
    id: str
    name: str
    created_at: str
    size: int
    entry_path: str | None = None
    stats: ReportStats | None = None
    status: str | None = None
    duration: int | None = None


class UploadResponse(BaseModel):
    id: str
    message: str
    report: ReportItem
    report: ReportItem


class MessageResponse(BaseModel):
    message: str
