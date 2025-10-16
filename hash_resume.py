# hash_resume.py
import hashlib
from pathlib import Path
from typing import Union

def compute_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute sha256 hex digest for file at file_path by reading in binary chunks.
    Returns 64-character hex string.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} does not exist")

    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
