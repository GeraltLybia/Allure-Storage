__all__ = ["HistoryService", "ReportStorageService", "StorageContext"]


def __getattr__(name: str):
    if name in {"HistoryService", "ReportStorageService", "StorageContext"}:
        from . import reporting

        return getattr(reporting, name)
    raise AttributeError(name)