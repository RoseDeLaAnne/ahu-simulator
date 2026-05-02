"""Tests for hardened Pydantic models in app.ui.scene.bindings.

Covers: Literal type enforcement, cross-field validators, hex color validation,
cross-reference checks (interactive_targets, animation targets vs scene_nodes),
and edge cases.
"""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from app.ui.scene.bindings import (
    AnimationRules,
    CameraPreset,
    DamperPositionRule,
    EmissiveHighlight,
    ExportRules,
    FanRotationRule,
    FlowPulseRule,
    OrbitControlsConfig,
    PerformanceBudget,
    PlumePulseRule,
    SceneAsset,
    SceneBinding,
    SceneBindingRegistry,
    SensorPulseRule,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_binding(**overrides) -> dict:
    base = {
        "visual_id": "outdoor_air",
        "kind": "node",
        "signal_path": "nodes.outdoor_air",
        "svg_element_id": "outdoor_air",
        "scene_node": "pvu.intake.outdoor_air",
    }
    base.update(overrides)
    return base


def _minimal_registry(**overrides) -> dict:
    base = {
        "version": 2,
        "bindings": [_minimal_binding()],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# SceneBinding
# ---------------------------------------------------------------------------

class TestSceneBinding:
    def test_valid_node_binding(self) -> None:
        b = SceneBinding.model_validate(_minimal_binding())
        assert b.kind == "node"
        assert b.scene_node == "pvu.intake.outdoor_air"

    def test_valid_sensor_binding(self) -> None:
        b = SceneBinding.model_validate(
            _minimal_binding(kind="sensor", visual_id="sensor_temp")
        )
        assert b.kind == "sensor"

    def test_valid_flow_binding(self) -> None:
        b = SceneBinding.model_validate(
            _minimal_binding(kind="flow", visual_id="flow_a")
        )
        assert b.kind == "flow"

    def test_rejects_invalid_kind(self) -> None:
        with pytest.raises(ValidationError, match="kind"):
            SceneBinding.model_validate(_minimal_binding(kind="unknown"))

    def test_rejects_empty_visual_id(self) -> None:
        with pytest.raises(ValidationError, match="visual_id"):
            SceneBinding.model_validate(_minimal_binding(visual_id=""))

    def test_rejects_invalid_scene_node_pattern(self) -> None:
        with pytest.raises(ValidationError, match="scene_node"):
            SceneBinding.model_validate(
                _minimal_binding(scene_node="Invalid Node!")
            )

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError, match="extra_forbidden"):
            SceneBinding.model_validate(
                _minimal_binding(unknown_field="oops")
            )


# ---------------------------------------------------------------------------
# SceneAsset
# ---------------------------------------------------------------------------

class TestSceneAsset:
    def test_valid_glb(self) -> None:
        a = SceneAsset.model_validate({
            "model_path": "data/model.glb",
            "format": "glb",
        })
        assert a.format == "glb"
        assert a.up_axis == "Y"

    def test_valid_gltf(self) -> None:
        a = SceneAsset.model_validate({
            "model_path": "data/model.gltf",
            "format": "gltf",
        })
        assert a.format == "gltf"

    def test_rejects_invalid_format(self) -> None:
        with pytest.raises(ValidationError, match="format"):
            SceneAsset.model_validate({
                "model_path": "data/model.obj",
                "format": "obj",
            })

    def test_rejects_invalid_up_axis(self) -> None:
        with pytest.raises(ValidationError, match="up_axis"):
            SceneAsset.model_validate({
                "model_path": "x.glb",
                "up_axis": "X",
            })

    def test_rejects_invalid_forward_axis(self) -> None:
        with pytest.raises(ValidationError, match="forward_axis"):
            SceneAsset.model_validate({
                "model_path": "x.glb",
                "forward_axis": "Y",
            })


# ---------------------------------------------------------------------------
# CameraPreset
# ---------------------------------------------------------------------------

class TestCameraPreset:
    def test_valid_preset(self) -> None:
        p = CameraPreset.model_validate({
            "position": [2.0, 4.0, 8.0],
            "target": [0.5, 0.5, 0.0],
        })
        assert p.fov == 45
        assert p.near < p.far

    def test_rejects_near_ge_far(self) -> None:
        with pytest.raises(ValidationError, match="near.*less than.*far"):
            CameraPreset.model_validate({
                "position": [0, 0, 0],
                "target": [0, 0, 0],
                "near": 100,
                "far": 1,
            })

    def test_rejects_near_equal_far(self) -> None:
        with pytest.raises(ValidationError, match="near.*less than.*far"):
            CameraPreset.model_validate({
                "position": [0, 0, 0],
                "target": [0, 0, 0],
                "near": 10,
                "far": 10,
            })

    def test_rejects_position_wrong_length(self) -> None:
        with pytest.raises(ValidationError):
            CameraPreset.model_validate({
                "position": [0, 0],
                "target": [0, 0, 0],
            })


# ---------------------------------------------------------------------------
# OrbitControlsConfig
# ---------------------------------------------------------------------------

class TestOrbitControlsConfig:
    def test_defaults_valid(self) -> None:
        c = OrbitControlsConfig()
        assert c.min_distance < c.max_distance
        assert c.min_polar_angle < c.max_polar_angle

    def test_rejects_min_distance_ge_max(self) -> None:
        with pytest.raises(ValidationError, match="min_distance.*less than"):
            OrbitControlsConfig.model_validate({
                "min_distance": 20,
                "max_distance": 5,
            })

    def test_rejects_min_polar_ge_max_polar(self) -> None:
        with pytest.raises(ValidationError, match="min_polar_angle.*less than"):
            OrbitControlsConfig.model_validate({
                "min_polar_angle": 1.5,
                "max_polar_angle": 0.1,
            })

    def test_polar_angle_bounded_by_pi(self) -> None:
        with pytest.raises(ValidationError):
            OrbitControlsConfig.model_validate({
                "max_polar_angle": math.pi + 0.1,
            })


# ---------------------------------------------------------------------------
# PerformanceBudget
# ---------------------------------------------------------------------------

class TestPerformanceBudget:
    def test_defaults_valid(self) -> None:
        b = PerformanceBudget()
        assert b.fallback_to_2d_on_fps_below < b.target_fps

    def test_rejects_fallback_ge_target(self) -> None:
        with pytest.raises(ValidationError, match="fallback.*less than.*target_fps"):
            PerformanceBudget.model_validate({
                "target_fps": 30,
                "fallback_to_2d_on_fps_below": 30,
            })


# ---------------------------------------------------------------------------
# Animation rules
# ---------------------------------------------------------------------------

class TestFanRotationRule:
    def test_valid(self) -> None:
        r = FanRotationRule.model_validate({
            "target_node": "pvu.fan.supply",
            "axis": "X",
            "speed_signal": "flows.flow_fan_to_room.intensity",
        })
        assert r.axis == "X"

    def test_rejects_invalid_axis(self) -> None:
        with pytest.raises(ValidationError, match="axis"):
            FanRotationRule.model_validate({
                "target_node": "n",
                "axis": "W",
                "speed_signal": "s",
            })


class TestFlowPulseRule:
    def test_valid(self) -> None:
        r = FlowPulseRule.model_validate({
            "target_nodes": ["pvu.flow.a"],
            "property": "opacity",
        })
        assert r.property == "opacity"

    def test_rejects_invalid_property(self) -> None:
        with pytest.raises(ValidationError, match="property"):
            FlowPulseRule.model_validate({
                "target_nodes": ["n"],
                "property": "color",
            })

    def test_rejects_min_ge_max_opacity(self) -> None:
        with pytest.raises(ValidationError, match="min_opacity.*less than"):
            FlowPulseRule.model_validate({
                "target_nodes": ["n"],
                "min_opacity": 0.9,
                "max_opacity": 0.3,
            })

    def test_rejects_empty_target_nodes(self) -> None:
        with pytest.raises(ValidationError):
            FlowPulseRule.model_validate({
                "target_nodes": [],
            })


class TestDamperPositionRule:
    def test_valid(self) -> None:
        r = DamperPositionRule.model_validate({
            "target_nodes": ["pvu.damper.intake"],
            "axis": "Z",
            "driver_signal": "flows.flow_fan_to_room.intensity",
        })
        assert r.axis == "Z"

    def test_rejects_invalid_axis(self) -> None:
        with pytest.raises(ValidationError, match="axis"):
            DamperPositionRule.model_validate({
                "target_nodes": ["pvu.damper.intake"],
                "axis": "Q",
                "driver_signal": "flows.flow_fan_to_room.intensity",
            })


class TestPlumePulseRule:
    def test_valid(self) -> None:
        r = PlumePulseRule.model_validate({
            "target_nodes": ["pvu.flow.room_plumes"],
        })
        assert r.axis == "Y"

    def test_rejects_invalid_ranges(self) -> None:
        with pytest.raises(ValidationError, match="min_scale.*less than"):
            PlumePulseRule.model_validate({
                "target_nodes": ["pvu.flow.room_plumes"],
                "min_scale": 1.2,
                "max_scale": 0.8,
            })

    def test_rejects_invalid_opacity_range(self) -> None:
        with pytest.raises(ValidationError, match="min_opacity.*less than"):
            PlumePulseRule.model_validate({
                "target_nodes": ["pvu.flow.room_plumes"],
                "min_opacity": 0.6,
                "max_opacity": 0.3,
            })


class TestSensorPulseRule:
    def test_valid(self) -> None:
        r = SensorPulseRule.model_validate({
            "target_nodes": ["pvu.sensors.airflow"],
            "pulse_speed": 2.2,
        })
        assert r.pulse_speed == 2.2

    def test_rejects_invalid_scale_range(self) -> None:
        with pytest.raises(ValidationError, match="min_scale.*less than"):
            SensorPulseRule.model_validate({
                "target_nodes": ["pvu.sensors.airflow"],
                "min_scale": 1.2,
                "max_scale": 1.1,
            })


# ---------------------------------------------------------------------------
# EmissiveHighlight
# ---------------------------------------------------------------------------

class TestEmissiveHighlight:
    def test_defaults_are_valid_hex(self) -> None:
        h = EmissiveHighlight()
        assert h.hover.startswith("#")
        assert len(h.hover) == 7

    def test_rejects_invalid_hex(self) -> None:
        with pytest.raises(ValidationError, match="hover"):
            EmissiveHighlight.model_validate({"hover": "red"})

    def test_rejects_short_hex(self) -> None:
        with pytest.raises(ValidationError):
            EmissiveHighlight.model_validate({"hover": "#abc"})

    def test_accepts_uppercase_hex(self) -> None:
        h = EmissiveHighlight.model_validate({"hover": "#AABBCC"})
        assert h.hover == "#AABBCC"


# ---------------------------------------------------------------------------
# SceneBindingRegistry — cross-referencing
# ---------------------------------------------------------------------------

class TestSceneBindingRegistryCrossRef:
    def test_valid_registry_passes(self) -> None:
        r = SceneBindingRegistry.model_validate(_minimal_registry(
            interactive_targets=["pvu.intake.outdoor_air"],
        ))
        assert r.version == 2
        assert len(r.bindings) == 1

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError, match="extra_forbidden"):
            SceneBindingRegistry.model_validate(
                _minimal_registry(bogus_field="oops")
            )

    def test_rejects_interactive_target_not_in_bindings(self) -> None:
        with pytest.raises(ValidationError, match="interactive_targets.*unknown"):
            SceneBindingRegistry.model_validate(_minimal_registry(
                interactive_targets=["nonexistent.node"],
            ))

    def test_rejects_fan_rotation_target_not_in_bindings(self) -> None:
        with pytest.raises(ValidationError, match="fan_rotation.target_node"):
            SceneBindingRegistry.model_validate(_minimal_registry(
                animation_rules={
                    "fan_rotation": {
                        "target_node": "nonexistent.fan",
                        "speed_signal": "s",
                    }
                },
            ))

    def test_rejects_flow_pulse_targets_not_in_bindings(self) -> None:
        with pytest.raises(ValidationError, match="flow_pulse.target_nodes.*unknown"):
            SceneBindingRegistry.model_validate(_minimal_registry(
                animation_rules={
                    "flow_pulse": {
                        "target_nodes": ["nonexistent.flow"],
                    }
                },
            ))

    def test_allows_animation_targets_from_auxiliary_nodes(self) -> None:
        registry = SceneBindingRegistry.model_validate(_minimal_registry(
            auxiliary_nodes=["pvu.fan.rotor", "pvu.flow.room_plumes"],
            animation_rules={
                "fan_rotation": {
                    "target_node": "pvu.fan.rotor",
                    "speed_signal": "flows.flow_fan_to_room.intensity",
                },
                "plume_pulse": {
                    "target_nodes": ["pvu.flow.room_plumes"],
                },
            },
        ))
        assert registry.auxiliary_nodes == ["pvu.fan.rotor", "pvu.flow.room_plumes"]

    def test_rejects_duplicate_auxiliary_nodes(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate auxiliary_nodes"):
            SceneBindingRegistry.model_validate(_minimal_registry(
                auxiliary_nodes=["pvu.fan.rotor", "pvu.fan.rotor"],
            ))

    def test_rejects_duplicate_visual_ids(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate visual_ids"):
            SceneBindingRegistry.model_validate({
                "version": 2,
                "bindings": [
                    _minimal_binding(),
                    _minimal_binding(scene_node="pvu.second.node"),
                ],
            })

    def test_status_colors_rejects_invalid_key(self) -> None:
        with pytest.raises(ValidationError, match="status_colors"):
            SceneBindingRegistry.model_validate(_minimal_registry(
                status_colors={"critical": "#ff0000"},
            ))

    def test_status_colors_rejects_invalid_hex(self) -> None:
        with pytest.raises(ValidationError, match="status_colors"):
            SceneBindingRegistry.model_validate(_minimal_registry(
                status_colors={"normal": "green"},
            ))

    def test_valid_status_colors(self) -> None:
        r = SceneBindingRegistry.model_validate(_minimal_registry(
            status_colors={
                "normal": "#22c55e",
                "warning": "#facc15",
                "alarm": "#ef4444",
                "inactive": "#64748b",
            },
        ))
        assert r.status_colors["normal"] == "#22c55e"

    def test_empty_bindings_skips_cross_ref(self) -> None:
        """When no bindings exist, interactive_targets / animation refs
        are not validated (nothing to cross-reference)."""
        r = SceneBindingRegistry.model_validate({
            "version": 1,
            "bindings": [],
        })
        assert len(r.bindings) == 0


# ---------------------------------------------------------------------------
# ExportRules
# ---------------------------------------------------------------------------

class TestExportRules:
    def test_defaults(self) -> None:
        e = ExportRules()
        assert "png" in e.allowed_texture_formats

    def test_rejects_empty_texture_formats(self) -> None:
        with pytest.raises(ValidationError):
            ExportRules.model_validate({"allowed_texture_formats": []})


# ---------------------------------------------------------------------------
# Integration: real scene3d.json loads without errors
# ---------------------------------------------------------------------------

class TestLoadRealScene3d:
    def test_load_scene_bindings_succeeds(self) -> None:
        from app.ui.scene.bindings import load_scene_bindings
        load_scene_bindings.cache_clear()
        registry = load_scene_bindings()
        assert registry.version == 2
        assert len(registry.bindings) == 15
        assert registry.asset is not None
        assert registry.asset.format == "glb"
        assert len(registry.interactive_targets) == 11
        assert registry.animation_rules is not None
        assert registry.animation_rules.fan_rotation is not None
        assert registry.animation_rules.flow_pulse is not None
        assert len(registry.status_colors) == 4
