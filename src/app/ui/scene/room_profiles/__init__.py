"""Профили помещений — по одному модулю на помещение.

Каждое помещение описывается отдельным файлом `room_profiles/<room_id>.py`
(`META` + `MODEL_OVERRIDES`). Здесь они собираются в реестры `ROOM_META` и
`ROOM_MODEL_OVERRIDES`, которыми пользуется `room_catalog.build_room_catalog`.

Порядок модулей задаёт порядок помещений в каталоге: первое — помещение по
умолчанию (`default_room_id`).
"""

from __future__ import annotations

from app.ui.scene.room_profiles import (
    classroom_wing,
    lab_cluster,
    office_suite,
)

__all__ = ["ROOM_META", "ROOM_MODEL_OVERRIDES"]


# Ключ — историческое имя GLB помещения (используется как идентификатор записи и
# для отката пути модели). Порядок важен: первое помещение — по умолчанию.
ROOM_META: dict[str, dict[str, object]] = {
    "office_suite.glb": office_suite.META,
    "classroom_wing.glb": classroom_wing.META,
    "lab_cluster.glb": lab_cluster.META,
}

ROOM_MODEL_OVERRIDES: dict[str, tuple[str, ...]] = {
    "office_suite.glb": office_suite.MODEL_OVERRIDES,
    "classroom_wing.glb": classroom_wing.MODEL_OVERRIDES,
    "lab_cluster.glb": lab_cluster.MODEL_OVERRIDES,
}
