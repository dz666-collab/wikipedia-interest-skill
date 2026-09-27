import hashlib
import json
from pathlib import Path


CACHE_DIR = Path(".cache")


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def _cache_path(namespace: str, key: str) -> Path:
    _ensure_cache_dir()

    hashed_key = hashlib.sha256(
        key.encode("utf-8")
    ).hexdigest()

    return CACHE_DIR / f"{namespace}_{hashed_key}.json"


def load_cache(namespace: str, key: str):
    path = _cache_path(namespace, key)

    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(namespace: str, key: str, data) -> None:
    path = _cache_path(namespace, key)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )