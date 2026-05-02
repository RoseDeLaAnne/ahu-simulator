from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.settings import get_project_root
from app.ui.scene.model_profiles import build_scene_profile


class SceneModelDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)
    model_path: str = Field(min_length=1)
    model_url: str = Field(min_length=1)
    preview_path: str | None = None
    preview_url: str | None = None
    accent: str = Field(default="#14b8a6", pattern=r"^#[0-9a-fA-F]{6}$")
    tone: str = Field(default="industrial", min_length=1)
    featured: bool = False
    profile: dict[str, object] = Field(default_factory=dict)


class SceneModelCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_model_id: str | None = None
    models: list[SceneModelDescriptor] = Field(default_factory=list)


_MODEL_META: dict[str, dict[str, str | bool]] = {
    "ahu/master/modular_ahu_pbr.glb": {
        "id": "modular_ahu",
        "label": "Флагманская ПВУ (детализированная)",
        "description": (
            "Детализированная флагманская модель ПВУ для основной демонстрации "
            "сцены установки вместо процедурного прототипа."
        ),
        "preview_path": "images-of-models/0476a6.jpg",
        "accent": "#38bdf8",
        "tone": "precision",
        "featured": True,
    },
    "ahu/master/modular_ahu_shaded.glb": {
        "id": "modular_ahu",
        "label": "Флагманская ПВУ (детализированная)",
        "description": (
            "Детализированная флагманская модель ПВУ для основной демонстрации "
            "сцены установки вместо процедурного прототипа."
        ),
        "preview_path": "images-of-models/0476a6.jpg",
        "accent": "#38bdf8",
        "tone": "precision",
        "featured": True,
    },
    "ahu/variants/base_variant_c_pbr.glb": {
        "id": "base_variant_c",
        "label": "Базовый вариант C",
        "description": (
            "Новый вариант базового корпуса для замены отсутствовавшего GLB "
            "в третьем семействе базовых моделей."
        ),
        "preview_path": "images-of-models/XXL_height.webp",
        "accent": "#06b6d4",
        "tone": "clean",
        "featured": False,
    },
    "ahu/variants/base_variant_c_shaded.glb": {
        "id": "base_variant_c",
        "label": "Базовый вариант C",
        "description": (
            "Новый вариант базового корпуса для замены отсутствовавшего GLB "
            "в третьем семействе базовых моделей."
        ),
        "preview_path": "images-of-models/XXL_height.webp",
        "accent": "#06b6d4",
        "tone": "clean",
        "featured": False,
    },
    "ahu/variants/industrial_hvac_unit.glb": {
        "id": "industrial_hvac_unit",
        "label": "Промышленная ПВУ",
        "description": (
            "Компактная индустриальная ПВУ для акцентной студийной сцены и "
            "быстрой проверки режимов."
        ),
        "preview_path": "images-of-models/XXL_height.webp",
        "accent": "#14b8a6",
        "tone": "studio",
        "featured": False,
    },
    "ahu/variants/industrial_machinery_unit.glb": {
        "id": "industrial_machinery_unit",
        "label": "Промышленный агрегат",
        "description": (
            "Вытянутый агрегат с компактным сечением, подходящий для режима "
            "рентген-визуализации потока."
        ),
        "preview_path": "images-of-models/obaw9u5kjxb6wc04l05iuz032skbt5sb.webp",
        "accent": "#f97316",
        "tone": "xray",
        "featured": False,
    },
    "ahu/variants/base_classic.glb": {
        "id": "base_classic",
        "label": "Базовый классический",
        "description": (
            "Базовый удлинённый корпус установки для чистой визуализации "
            "приточного тракта."
        ),
        "preview_path": "images-of-models/XXL_height.webp",
        "accent": "#22c55e",
        "tone": "clean",
        "featured": False,
    },
    "ahu/variants/base_variant_b.glb": {
        "id": "base_variant_b",
        "label": "Базовый вариант Б",
        "description": (
            "Высокий вариант установки для альтернативного ракурса и "
            "демонстрации узлов по вертикали."
        ),
        "preview_path": "images-of-models/obaw9u5kjxb6wc04l05iuz032skbt5sb.webp",
        "accent": "#eab308",
        "tone": "clean",
        "featured": False,
    },
}

_PREFERRED_SCENE_MODEL_PATH_GROUPS: tuple[tuple[str, ...], ...] = (
    ("ahu/master/modular_ahu_pbr.glb", "ahu/master/modular_ahu_shaded.glb"),
    (
        "ahu/variants/base_variant_c_pbr.glb",
        "ahu/variants/base_variant_c_shaded.glb",
    ),
)


def build_scene_model_catalog(project_root: Path | None = None) -> SceneModelCatalog:
    root = project_root or get_project_root()
    models_dir = root / "models"
    if not models_dir.exists():
        return SceneModelCatalog()

    duplicate_glb_names = _discover_duplicate_glbs(models_dir)
    scene_model_paths = _collect_scene_model_paths(models_dir, duplicate_glb_names)
    descriptors: list[SceneModelDescriptor] = []
    for model_path in scene_model_paths:
        relative_model_path = model_path.relative_to(models_dir).as_posix()
        meta = _MODEL_META.get(relative_model_path) or _MODEL_META.get(model_path.name, {})
        descriptor = SceneModelDescriptor(
            id=str(meta.get("id") or _slugify(model_path.stem)),
            label=str(meta.get("label") or _humanize_name(model_path.stem)),
            description=str(
                meta.get("description")
                or "Пользовательская 3D-модель для интерактивной сцены ПВУ."
            ),
            model_path=model_path.relative_to(root).as_posix(),
            model_url=f"/models/{quote(relative_model_path)}",
            preview_path=_relative_preview_path(root, meta.get("preview_path")),
            preview_url=_preview_url(root, meta.get("preview_path")),
            accent=str(meta.get("accent") or "#14b8a6"),
            tone=str(meta.get("tone") or "industrial"),
            featured=bool(meta.get("featured", False)),
            profile=build_scene_profile(
                str(meta.get("id") or _slugify(model_path.stem))
            ),
        )
        descriptors.append(descriptor)

    descriptors.sort(key=lambda item: (not item.featured, item.label.lower()))
    default_model_id = descriptors[0].id if descriptors else None
    return SceneModelCatalog(default_model_id=default_model_id, models=descriptors)


def _collect_scene_model_paths(
    models_dir: Path,
    duplicate_glb_names: set[str],
) -> list[Path]:
    collected_paths: list[Path] = []
    seen_paths: set[str] = set()
    preferred_paths = {
        relative_path
        for group in _PREFERRED_SCENE_MODEL_PATH_GROUPS
        for relative_path in group
    }

    def _add_unique(candidate_path: Path) -> None:
        normalized = candidate_path.as_posix()
        if normalized in seen_paths:
            return
        seen_paths.add(normalized)
        collected_paths.append(candidate_path)

    for group in _PREFERRED_SCENE_MODEL_PATH_GROUPS:
        for relative_path in group:
            candidate_path = models_dir / relative_path
            if candidate_path.exists():
                _add_unique(candidate_path)
                break

    ahu_dir = models_dir / "ahu"
    if ahu_dir.exists():
        for model_path in sorted(ahu_dir.rglob("*.glb")):
            relative_model_path = model_path.relative_to(models_dir).as_posix()
            if relative_model_path in preferred_paths:
                continue
            if model_path.name in duplicate_glb_names:
                continue
            _add_unique(model_path)

    return collected_paths


def _relative_preview_path(project_root: Path, preview_path: str | bool | None) -> str | None:
    if not isinstance(preview_path, str):
        return None
    candidate = project_root / preview_path
    if not candidate.exists():
        return None
    return candidate.relative_to(project_root).as_posix()


def _preview_url(project_root: Path, preview_path: str | bool | None) -> str | None:
    relative_path = _relative_preview_path(project_root, preview_path)
    if not relative_path:
        return None
    return "/" + quote(relative_path)


def _humanize_name(value: str) -> str:
    cleaned = re.sub(r"[_-]+", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.title() or "Модель сцены"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "scene_model"


@lru_cache(maxsize=8)
def _discover_duplicate_glbs(models_dir: Path) -> set[str]:
    duplicate_glb_names: set[str] = set()

    glb_hash_groups: dict[str, list[Path]] = defaultdict(list)
    for glb_path in models_dir.glob("*.glb"):
        glb_hash_groups[_sha256_file(glb_path)].append(glb_path)
    for group in glb_hash_groups.values():
        if len(group) < 2:
            continue
        preferred = _preferred_original(group)
        duplicate_glb_names.update(path.name for path in group if path != preferred)

    obj_hash_groups: dict[str, list[Path]] = defaultdict(list)
    for obj_path in models_dir.glob("*.obj"):
        obj_hash_groups[_sha256_file(obj_path)].append(obj_path)
    for group in obj_hash_groups.values():
        if len(group) < 2:
            continue
        preferred_obj = _preferred_original(group)
        preferred_glb = models_dir / f"{preferred_obj.stem}.glb"
        if not preferred_glb.exists():
            continue
        for obj_path in group:
            if obj_path == preferred_obj:
                continue
            candidate_glb = models_dir / f"{obj_path.stem}.glb"
            if candidate_glb.exists():
                duplicate_glb_names.add(candidate_glb.name)

    return duplicate_glb_names


def _preferred_original(paths: list[Path]) -> Path:
    return min(
        paths,
        key=lambda path: (
            1 if re.search(r"\(\d+\)$", path.stem) else 0,
            len(path.stem),
            path.stem.lower(),
        ),
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
