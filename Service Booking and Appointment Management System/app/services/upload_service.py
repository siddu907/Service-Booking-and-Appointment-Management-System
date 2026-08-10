from pathlib import Path
from fastapi import UploadFile

from app.config import settings


class UploadService:
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, file: UploadFile, folder: str) -> str:
        dest_dir = self.upload_dir / folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        extension = Path(file.filename).suffix
        safe_name = f"{Path(file.filename).stem}_{abs(hash(file.filename))}{extension}"
        dest_path = dest_dir / safe_name
        with dest_path.open("wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                buffer.write(chunk)
        return f"/uploads/{folder}/{safe_name}"
