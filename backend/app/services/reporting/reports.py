import logging
import uuid
import zipfile
from pathlib import Path

from fastapi import HTTPException, UploadFile

from .common import safe_extract_zip
from .context import StorageContext
from .models import ReportEntry
from .repositories import ReportsRepository

logger = logging.getLogger(__name__)

_UPLOAD_CHUNK_SIZE = 1024 * 1024


class ReportStorageService:
    def __init__(self, context: StorageContext):
        self.context = context
        self.context.ensure_directories()
        self.repository = ReportsRepository(context)

    def list_reports(self) -> list[dict]:
        return [entry.to_dict() for entry in self.repository.list_report_entries()]

    def upload_report(self, file: UploadFile) -> dict:
        filename = (file.filename or "").lower()
        if not filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")

        report_id = str(uuid.uuid4())
        report_path = self.repository.create_report_directory(report_id)
        zip_path = report_path / ".upload.zip"

        try:
            copied = 0
            with zip_path.open("wb") as buffer:
                while True:
                    chunk = file.file.read(_UPLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    copied += len(chunk)
                    if copied > self.context.max_upload_size_bytes:
                        raise HTTPException(status_code=413, detail="Upload file is too large")
                    buffer.write(chunk)

            with zipfile.ZipFile(zip_path, "r") as archive:
                safe_extract_zip(archive, report_path)

            zip_path.unlink(missing_ok=True)
            meta = self.repository.build_report_meta(report_path)
            self.repository.write_report_meta(report_path, meta)
            evicted = self.repository.apply_retention()
            if evicted:
                logger.info("Retention evicted %s report(s): %s", len(evicted), ", ".join(evicted))
            logger.info("Report uploaded: id=%s size=%s", report_id, copied)
            entry = ReportEntry(
                id=report_id,
                name=meta["name"] or report_id,
                created_at=meta["created_at"],
                size=meta["size"],
                entry_path=meta["entry_path"],
                stats=meta["stats"],
                status=meta["status"],
                duration=meta["duration"],
            )
            return {
                "id": report_id,
                "message": "Report uploaded and extracted successfully",
                "report": entry.to_dict(),
            }
        except zipfile.BadZipFile as exc:
            self.repository.remove_path(report_path)
            logger.warning("Report upload rejected: invalid ZIP file")
            raise HTTPException(status_code=400, detail="Invalid ZIP file") from exc
        except HTTPException:
            self.repository.remove_path(report_path)
            raise
        except Exception:
            self.repository.remove_path(report_path)
            logger.exception("Report upload failed: id=%s", report_id)
            raise HTTPException(status_code=500, detail="Upload failed") from None
        finally:
            try:
                file.file.close()
            except Exception:
                pass

    def delete_report(self, report_id: str) -> dict:
        if not self.repository.report_exists(report_id):
            raise HTTPException(status_code=404, detail="Report not found")

        try:
            self.repository.delete_report(report_id)
            logger.info("Report deleted: id=%s", report_id)
            return {"message": "Report deleted successfully"}
        except Exception:
            logger.exception("Report delete failed: id=%s", report_id)
            raise HTTPException(status_code=500, detail="Delete failed") from None

    def create_report_archive(self, report_id: str) -> tuple[Path, str]:
        if not self.repository.report_exists(report_id):
            raise HTTPException(status_code=404, detail="Report not found")
        return self.repository.create_archive(report_id)