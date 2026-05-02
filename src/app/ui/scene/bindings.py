from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.infrastructure.settings import get_project_root

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
HexColor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]

BindingKind = Literal["node", "sensor", "flow"]
AssetFormat = Literal["glb", "gltf"]
UpAxis = Literal["Y", "Z"]
ForwardAxis = Literal["X", "Z", "-Z", "-X"]
RotationAxis = Literal["X", "Y", "Z"]
PulseProperty = Literal["opacity", "emissive"]
StatusKey = Literal["normal", "warning", "alarm", "inactive"]


# ---------------------------------------------------------------------------
# SceneBinding — one mapping row (visual_id ↔ scene_node)
# ---------------------------------------------------------------------------

class SceneBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    visual_id: str = Field(min_length=1)
    kind: BindingKind
    signal_path: str = Field(min_length=1)
    svg_element_id: str = Field(min_length=1)
    scene_node: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_.]+$")


# ---------------------------------------------------------------------------
# SceneAsset — 3D model reference
# ---------------------------------------------------------------------------

class SceneAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_path: str = Field(min_length=1)
    format: AssetFormat = "glb"
    generator: str | None = None
    units: Literal["meters", "centimeters"] = "meters"
    up_axis: UpAxis = "Y"
    forward_axis: ForwardAxis = "X"


# ---------------------------------------------------------------------------
# CameraPreset — preset camera position / projection
# ---------------------------------------------------------------------------

class CameraPreset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position: list[float] = Field(min_length=3, max_length=3)
    target: list[float] = Field(min_length=3, max_length=3)
    fov: float = Field(ge=10, le=120, default=45)
    near: float = Field(gt=0, default=0.1)
    far: float = Field(gt=0, default=100)

    @model_validator(mode="after")
    def _near_less_than_far(self) -> CameraPreset:
        if self.near >= self.far:
            raise ValueError(
                f"near ({self.near}) must be less than far ({self.far})"
            )
        return self


# ---------------------------------------------------------------------------
# OrbitControlsConfig — three.js OrbitControls parameters
# ---------------------------------------------------------------------------

class OrbitControlsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_distance: float = Field(ge=0, default=3.0)
    max_distance: float = Field(gt=0, default=20.0)
    min_polar_angle: float = Field(ge=0, le=math.pi, default=0.1)
    max_polar_angle: float = Field(ge=0, le=math.pi, default=1.5)
    enable_damping: bool = True
    damping_factor: float = Field(ge=0, le=1, default=0.08)
    auto_rotate: bool = False

    @model_validator(mode="after")
    def _min_less_than_max(self) -> OrbitControlsConfig:
        if self.min_distance >= self.max_distance:
            raise ValueError(
                f"min_distance ({self.min_distance}) must be less than "
                f"max_distance ({self.max_distance})"
            )
        if self.min_polar_angle >= self.max_polar_angle:
            raise ValueError(
                f"min_polar_angle ({self.min_polar_angle}) must be less than "
                f"max_polar_angle ({self.max_polar_angle})"
            )
        return self


# ---------------------------------------------------------------------------
# PerformanceBudget — rendering quality / fallback thresholds
# ---------------------------------------------------------------------------

class PerformanceBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_pixel_ratio: float = Field(ge=1, le=4, default=2.0)
    max_canvas_width: int = Field(ge=320, default=1400)
    max_canvas_height: int = Field(ge=240, default=900)
    target_fps: int = Field(ge=10, le=120, default=30)
    antialias: bool = True
    fallback_to_2d_on_fps_below: int = Field(ge=1, le=30, default=10)

    @model_validator(mode="after")
    def _fallback_below_target(self) -> PerformanceBudget:
        if self.fallback_to_2d_on_fps_below >= self.target_fps:
            raise ValueError(
                f"fallback_to_2d_on_fps_below ({self.fallback_to_2d_on_fps_below}) "
                f"must be less than target_fps ({self.target_fps})"
            )
        return self


# ---------------------------------------------------------------------------
# Animation rules
# ---------------------------------------------------------------------------

class FanRotationRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_node: str = Field(min_length=1)
    axis: RotationAxis = "X"
    speed_signal: str = Field(min_length=1)
    max_rpm: float = Field(ge=0, default=2.0)


class FlowPulseRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_nodes: list[str] = Field(min_length=1)
    property: PulseProperty = "opacity"
    min_opacity: float = Field(ge=0, le=1, default=0.3)
    max_opacity: float = Field(ge=0, le=1, default=0.9)
    pulse_speed: float = Field(ge=0, default=1.5)

    @model_validator(mode="after")
    def _min_less_than_max_opacity(self) -> FlowPulseRule:
        if self.min_opacity >= self.max_opacity:
            raise ValueError(
                f"min_opacity ({self.min_opacity}) must be less than "
                f"max_opacity ({self.max_opacity})"
        )
        return self


class DamperPositionRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_nodes: list[str] = Field(min_length=1)
    axis: RotationAxis = "Z"
    closed_angle_deg: float = Field(ge=-180, le=180, default=-60.0)
    open_angle_deg: float = Field(ge=-180, le=180, default=8.0)
    driver_signal: str = Field(min_length=1)
    response: float = Field(ge=0.1, default=3.0)


class PlumePulseRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_nodes: list[str] = Field(min_length=1)
    axis: RotationAxis = "Y"
    min_scale: float = Field(gt=0, default=0.85)
    max_scale: float = Field(gt=0, default=1.2)
    min_opacity: float = Field(ge=0, le=1, default=0.14)
    max_opacity: float = Field(ge=0, le=1, default=0.52)
    pulse_speed: float = Field(ge=0, default=1.1)
    driver_signal: str | None = None

    @model_validator(mode="after")
    def _min_less_than_max(self) -> PlumePulseRule:
        if self.min_scale >= self.max_scale:
            raise ValueError(
                f"min_scale ({self.min_scale}) must be less than "
                f"max_scale ({self.max_scale})"
            )
        if self.min_opacity >= self.max_opacity:
            raise ValueError(
                f"min_opacity ({self.min_opacity}) must be less than "
                f"max_opacity ({self.max_opacity})"
            )
        return self


class SensorPulseRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_nodes: list[str] = Field(min_length=1)
    min_scale: float = Field(gt=0, default=0.94)
    max_scale: float = Field(gt=0, default=1.12)
    pulse_speed: float = Field(ge=0, default=1.8)
    emissive_strength: float = Field(ge=0, default=1.0)

    @model_validator(mode="after")
    def _min_less_than_max(self) -> SensorPulseRule:
        if self.min_scale >= self.max_scale:
            raise ValueError(
                f"min_scale ({self.min_scale}) must be less than "
                f"max_scale ({self.max_scale})"
            )
        return self


class AnimationRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fan_rotation: FanRotationRule | None = None
    flow_pulse: FlowPulseRule | None = None
    damper_position: DamperPositionRule | None = None
    plume_pulse: PlumePulseRule | None = None
    sensor_pulse: SensorPulseRule | None = None


# ---------------------------------------------------------------------------
# EmissiveHighlight — highlight colors (hex)
# ---------------------------------------------------------------------------

class EmissiveHighlight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hover: HexColor = "#334155"
    selected: HexColor = "#475569"
    alarm_flash_a: HexColor = "#ff2000"
    alarm_flash_b: HexColor = "#ff6600"


# ---------------------------------------------------------------------------
# ExportRules — conventions for DCC / model pipeline
# ---------------------------------------------------------------------------

class ExportRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dcc_tool: str | None = None
    units: Literal["meters", "centimeters"] = "meters"
    orientation: str = "Y-up, X-forward"
    allowed_texture_formats: list[str] = Field(
        default_factory=lambda: ["png", "jpeg"],
        min_length=1,
    )
    node_naming: str = "dot-separated hierarchy matching scene_node IDs"
    update_procedure: str | None = None


# ---------------------------------------------------------------------------
# SceneBindingRegistry — root model for scene3d.json
# ---------------------------------------------------------------------------

class SceneBindingRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1, le=99)
    asset: SceneAsset | None = None
    camera_presets: dict[str, CameraPreset] = Field(default_factory=dict)
    orbit_controls: OrbitControlsConfig = Field(default_factory=OrbitControlsConfig)
    performance_budget: PerformanceBudget = Field(default_factory=PerformanceBudget)
    interactive_targets: list[str] = Field(default_factory=list)
    auxiliary_nodes: list[str] = Field(default_factory=list)
    animation_rules: AnimationRules | None = None
    status_colors: dict[StatusKey, HexColor] = Field(default_factory=dict)
    emissive_highlight: EmissiveHighlight = Field(default_factory=EmissiveHighlight)
    export_rules: ExportRules | None = None
    bindings: list[SceneBinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def _cross_references(self) -> SceneBindingRegistry:
        """Validate that interactive_targets and animation targets reference
        scene_node IDs declared in *bindings*."""
        scene_nodes = {b.scene_node for b in self.bindings}
        auxiliary_nodes = set(self.auxiliary_nodes)

        if len(self.auxiliary_nodes) != len(auxiliary_nodes):
            raise ValueError("Duplicate auxiliary_nodes are not allowed")
        overlap = scene_nodes & auxiliary_nodes
        if overlap:
            raise ValueError(
                f"auxiliary_nodes duplicate binding scene_nodes: "
                f"{sorted(overlap)}"
            )

        known_nodes = scene_nodes | auxiliary_nodes
        if not scene_nodes:
            return self

        bad_interactive = set(self.interactive_targets) - scene_nodes
        if bad_interactive:
            raise ValueError(
                f"interactive_targets reference unknown scene_nodes: "
                f"{sorted(bad_interactive)}"
            )

        if self.animation_rules:
            rules = self.animation_rules
            if rules.fan_rotation:
                if rules.fan_rotation.target_node not in known_nodes:
                    raise ValueError(
                        f"fan_rotation.target_node "
                        f"'{rules.fan_rotation.target_node}' "
                        f"not found in bindings or auxiliary_nodes"
                    )
            if rules.flow_pulse:
                bad_pulse = set(rules.flow_pulse.target_nodes) - known_nodes
                if bad_pulse:
                    raise ValueError(
                        f"flow_pulse.target_nodes reference unknown "
                        f"scene_nodes: {sorted(bad_pulse)}"
                    )
            if rules.damper_position:
                bad_dampers = set(rules.damper_position.target_nodes) - known_nodes
                if bad_dampers:
                    raise ValueError(
                        f"damper_position.target_nodes reference unknown "
                        f"scene_nodes: {sorted(bad_dampers)}"
                    )
            if rules.plume_pulse:
                bad_plumes = set(rules.plume_pulse.target_nodes) - known_nodes
                if bad_plumes:
                    raise ValueError(
                        f"plume_pulse.target_nodes reference unknown "
                        f"scene_nodes: {sorted(bad_plumes)}"
                    )
            if rules.sensor_pulse:
                bad_sensors = set(rules.sensor_pulse.target_nodes) - known_nodes
                if bad_sensors:
                    raise ValueError(
                        f"sensor_pulse.target_nodes reference unknown "
                        f"scene_nodes: {sorted(bad_sensors)}"
                    )

        # Ensure no duplicate visual_ids
        visual_ids = [b.visual_id for b in self.bindings]
        if len(visual_ids) != len(set(visual_ids)):
            seen: set[str] = set()
            dupes: list[str] = []
            for vid in visual_ids:
                if vid in seen:
                    dupes.append(vid)
                seen.add(vid)
            raise ValueError(f"Duplicate visual_ids in bindings: {dupes}")

        return self


@lru_cache
def load_scene_bindings() -> SceneBindingRegistry:
    binding_path = get_project_root() / "data" / "visualization" / "scene3d.json"
    payload = json.loads(binding_path.read_text(encoding="utf-8"))
    registry = SceneBindingRegistry.model_validate(payload)
    if registry.asset:
        asset_path = get_project_root() / registry.asset.model_path
        if not asset_path.exists():
            raise FileNotFoundError(
                f"3D asset not found: {asset_path}. "
                f"Run build_blender_pvu.py or provide the model file."
            )
    return registry
