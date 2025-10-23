# hash_resume.py
import hashlib
from pathlib import Path
from typing import Union

def compute_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Stream file and compute SHA-256 hex digest (64 chars).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")

    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
