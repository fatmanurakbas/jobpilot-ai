from pathlib import Path
import hashlib


class FileHashService:

    def sha256(self, file_path: str) -> str:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {path}"
            )

        digest = hashlib.sha256()

        with path.open("rb") as file:
            while chunk := file.read(8192):
                digest.update(chunk)

        return digest.hexdigest()


file_hash_service = FileHashService()