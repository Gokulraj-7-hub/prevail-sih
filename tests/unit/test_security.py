"""Threat-model.md spot checks (Phase 25/29): upload size cap, no path
traversal via client-controlled filenames, CORS never defaults to '*'."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from prevail.api.dataset_store import MAX_UPLOAD_BYTES, DatasetStore, IngestionError


def test_oversized_upload_rejected():
    store = DatasetStore()
    oversized = b"x" * (MAX_UPLOAD_BYTES + 1)
    with pytest.raises(IngestionError, match="exceeds max size"):
        store.ingest_bytes(oversized)


def test_unparseable_upload_raises_typed_error_not_crash():
    store = DatasetStore()
    with pytest.raises(IngestionError):
        store.ingest_bytes(b"this is not a valid csv at all \x00\x01\x02")


def test_stored_upload_path_is_server_generated_not_client_controlled():
    """Client never supplies the storage path/filename -- ingest_bytes takes
    only raw bytes, so a filename like '../../etc/passwd' cannot reach the
    filesystem layer at all (there is no filename parameter to inject into)."""
    import inspect
    from prevail.api.dataset_store import DatasetStore

    sig = inspect.signature(DatasetStore.ingest_bytes)
    assert "filename" not in sig.parameters
    assert "path" not in sig.parameters


def test_cors_default_never_wildcard():
    import re
    main_py = (Path(__file__).resolve().parents[2] / "src" / "prevail" / "api" / "main.py").read_text()
    match = re.search(r"_default_origins\s*=\s*(\[[^\]]*\])", main_py)
    assert match is not None
    assert '"*"' not in match.group(1)
