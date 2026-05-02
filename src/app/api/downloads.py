from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from app.infrastructure.runtime_paths import RuntimePathResolver


def resolve_download_file(
    path_resolver: RuntimePathResolver,
    display_path: str,
    *,
    allowed_prefixes: tuple[str, ...],
) -> Path:
    normalized_path = display_path.replace("\\", "/").strip()
    if not normalized_path:
        raise HTTPException(
            status_code=400,
            detail="Параметр path не должен быть пустым.",
        )

    if not any(
        normalized_path == prefix or normalized_path.startswith(f"{prefix}/")
        for prefix in allowed_prefixes
    ):
        raise HTTPException(
            status_code=400,
            detail="Указанный путь нельзя скачать через этот endpoint.",
        )

    resolved_path = path_resolver.resolve_display_path(normalized_path).resolve()
    allowed_roots = [
        path_resolver.resolve_display_path(prefix).resolve()
        for prefix in allowed_prefixes
    ]
    if not any(_is_within_root(resolved_path, root) for root in allowed_roots):
        raise HTTPException(
            status_code=400,
            detail="Путь выходит за пределы разрешённого каталога.",
        )

    if not resolved_path.exists() or not resolved_path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден.")

    return resolved_path


def build_download_filename(display_path: str, fallback: str) -> str:
    filename = Path(display_path.replace("\\", "/")).name
    return filename or fallback


def _is_within_root(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False
