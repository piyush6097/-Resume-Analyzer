
# hash_resume.py
import hashlib
from pathlib import Path
from typing import Union

def compute_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute SHA-256 hash for the given file.
    Reads in binary mode to support any file type.
    Returns a 64-character hex string.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")

    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()
