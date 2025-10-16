# tests/smoke_test_cache.py
from hash_resume import compute_sha256
from db_cache import init_db, get_cached_score, save_score
import tempfile, os

init_db()

# create a temp file
with tempfile.NamedTemporaryFile(delete=False) as tmp:
    tmp.write(b"dummy resume content")
    tmp.flush()
    path = tmp.name

h = compute_sha256(path)
assert get_cached_score(h) is None, "Expected no cached score"
save_score(h, 9.25, source_filename="dummy.pdf")
cached = get_cached_score(h)
assert abs(cached - 9.25) < 1e-6, "Cached score mismatch"

print("smoke test passed")
os.unlink(path)
