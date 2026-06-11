import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.mjs";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.mjs";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.mjs";
import { RenderPass } from "three/addons/postprocessing/RenderPass.mjs";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.mjs";
import { OutputPass } from "three/addons/postprocessing/OutputPass.mjs";
import { SSAOPass } from "three/addons/postprocessing/SSAOPass.mjs";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.mjs";

// Фабрика GLTFLoader с подключённым meshopt-декодером: оптимизированные GLB
// используют EXT_meshopt_compression, без декодера они не загрузятся.
// GLTFLoader r170 сам дожидается MeshoptDecoder.ready перед разбором.
function _createGltfLoader() {
  var loader = new GLTFLoader();
  loader.setMeshoptDecoder(MeshoptDecoder);
  return loader;
}

const STATUS_COLORS = {
  normal: 0x22c55e,
  warning: 0xfacc15,
  alarm: 0xef4444,
  inactive: 0x64748b,
};

const DEFAULT_MODEL_ACCENT = "#14b8a6";
const EMISSIVE_HOVER = 0x335f73;
const EMISSIVE_SELECTED = 0x67e8f9;
const ALARM_FLASH_A = 0xff3b30;
const ALARM_FLASH_B = 0xff9f0a;
const COLD_COLOR = new THREE.Color(0x4cc9f0);
const WARM_COLOR = new THREE.Color(0xfb923c);
const NEUTRAL_COLOR = new THREE.Color(0x8b9aa7);

// Семантическая палитра секций ПВУ (русская инженерная терминология).
// По типовой компоновке СП 60.13330.2020 и рекомендациям АВОК:
// холодные тона — забор и охлаждение, теплые — нагрев, янтарь — клапан,
// сталь/графит — корпус и крепления.
const SECTION_PALETTE = {
  intake: new THREE.Color(0x7dd3fc),    // воздухозабор — ледяной голубой
  damper: new THREE.Color(0xfbbf24),    // воздушный клапан — янтарный
  filter: new THREE.Color(0xf1f5f9),    // фильтр — чистый светло-серый
  silencer: new THREE.Color(0xa78bfa),  // шумоглушитель — приглушённый сиреневый
  heater: new THREE.Color(0xfb7185),    // калорифер (нагреватель) — тёпло-розовый
  fan: new THREE.Color(0x22d3ee),       // приточный вентилятор — бирюзовый
  duct: new THREE.Color(0x94a3b8),      // воздуховод подачи — стальной
  recuperator: new THREE.Color(0x34d399), // пластинчатый рекуператор — изумрудный
  exhaust: new THREE.Color(0x64748b),   // вытяжная ветвь — шиферный серый
  outdoor: new THREE.Color(0x60a5fa),   // наружный/выбросной канал — синий
  enclosure: new THREE.Color(0x475569), // корпус секций — графит
  frame: new THREE.Color(0x6b7280),     // рамы и крепления — холодный серый
};

const ENCLOSURE_KINDS = {
  enclosure_shell: true,
  enclosure_door: true,
  enclosure_handle: true,
};

// Visual IDs, значения которых несут температуру (°C). Для таких узлов
// color materials окрашиваются по температуре (холодный голубой → тёплый
// оранжевый через нейтральный комфортный серый), а emissive остаётся по
// status, чтобы авария/предупреждение были видны как цветной glow.
const TEMPERATURE_VISUAL_IDS = {
  outdoor_air: true,
  supply_duct: true,
  heater_coil: true,
  cooler_coil: true,
  room_supply: true,
  room_zone: true,
  flow_heater_to_fan: true,
  flow_fan_to_room: true,
  sensor_outdoor_temp: true,
  sensor_supply_temp: true,
  sensor_room_temp: true,
};

// Visual IDs, чьё состояние отражает давление на фильтре.
const FILTER_PRESSURE_VISUAL_IDS = {
  filter_bank: true,
  filter_fine: true,
  sensor_filter_pressure: true,
};

// Приоритетные подписи в русской инженерной терминологии для постоянной
// видимости (overlay screen-space). Ключевые секции ПВУ по СП 60.13330.2020 +
// сервисные датчики микроклимата по ГОСТ 30494-2011.
const PRIORITY_LABELS = [
  { node: "pvu.intake.outdoor_air", text: "Забор", type: "section" },
  { node: "pvu.filter.bank", text: "Фильтр", type: "section" },
  { node: "pvu.recuperator.core", text: "Рекуператор", type: "section" },
  { node: "pvu.heater.coil", text: "Калорифер", type: "section" },
  { node: "pvu.fan.supply", text: "Вентилятор", type: "section" },
  { node: "pvu.duct.supply", text: "Подача", type: "section" },
  { node: "building.room.zone_a", text: "Помещение", type: "zone" },
  { node: "pvu.sensors.outdoor_temp", text: "T нар.", type: "sensor" },
  { node: "pvu.sensors.filter_pressure", text: "ΔP фильтра", type: "sensor" },
  { node: "pvu.sensors.supply_temp", text: "T притока", type: "sensor" },
  { node: "pvu.sensors.airflow", text: "Расход", type: "sensor" },
  { node: "building.sensors.room_temp", text: "T помещ.", type: "sensor" },
];

const STATE_LABEL_RU = {
  normal: "Норма",
  warning: "Риск",
  alarm: "Авария",
  inactive: "Неактивно",
};

const TEMP_COLD = new THREE.Color(0x38bdf8);   // < -5 °C
const TEMP_COMFORT = new THREE.Color(0xd1d5db); // 20–24 °C
const TEMP_WARM = new THREE.Color(0xf97316);   // > 32 °C

/**
 * Возвращает цвет, соответствующий температуре по отечественной ОВК-гамме:
 * холодный голубой ниже нуля (СП 131.13330.2025 / ГОСТ 30494-2011 зона холода),
 * нейтральный комфортный при 20–24 °C (ГОСТ 30494-2011 оптимальные значения),
 * тёплый оранжевый при перегреве/горячей подаче.
 */
function _temperatureColor(celsius) {
  if (celsius === null || !Number.isFinite(celsius)) return null;
  var result;
  if (celsius <= 20) {
    // -30 .. 20 °C: cold → comfort.
    var t1 = _clamp((celsius + 30) / 50, 0, 1);
    result = TEMP_COLD.clone().lerp(TEMP_COMFORT, t1);
  } else if (celsius <= 24) {
    // Comfort band (20..24 °C).
    result = TEMP_COMFORT.clone();
  } else {
    // 24 .. 40 °C: comfort → warm.
    var t2 = _clamp((celsius - 24) / 16, 0, 1);
    result = TEMP_COMFORT.clone().lerp(TEMP_WARM, t2);
  }
  return result;
}

/**
 * Классификация роли mesh по имени узла в иерархии GLB-сцены ПВУ.
 * Возвращает { kind, section } — kind задаёт правило отрисовки в режимах
 * studio/xray/schematic, section — ключ в SECTION_PALETTE.
 *
 * Замечание: Three.js GLTFLoader удаляет точки из имён узлов
 * (`pvu.fan.blade_1` -> `pvufanblade_1`). Поэтому регулярки/indexOf здесь
 * работают по нормализованной форме `name` без точек.
 */
function _classifyAhuRole(meshName) {
  if (!meshName) return { kind: "other", section: null };
  // Нормализуем: убираем точки и приводим к нижнему регистру.
  var name = String(meshName).toLowerCase().replace(/\./g, "");
  if (!name) return { kind: "other", section: null };

  // Корпус секций ПВУ: оригинал «pvu.{section}.shell» -> «pvu{section}shell».
  if (/^pvu/.test(name) && /shell$/.test(name) && name !== "pvuductsupplystatus_shell") {
    return { kind: "enclosure_shell", section: "enclosure" };
  }
  if (/^pvu/.test(name) && /door$/.test(name)) {
    return { kind: "enclosure_door", section: "enclosure" };
  }
  if (/^pvu/.test(name) && /handle$/.test(name)) {
    return { kind: "enclosure_handle", section: "enclosure" };
  }
  if (/^pvudamper/.test(name)) {
    return { kind: "damper", section: "damper" };
  }
  if (/^pvuintake/.test(name)) {
    if (/louver/.test(name)) return { kind: "intake_louver", section: "intake" };
    if (/weather_hood/.test(name)) return { kind: "intake_hood", section: "intake" };
    if (/transition/.test(name)) return { kind: "intake_transition", section: "intake" };
    return { kind: "intake_other", section: "intake" };
  }
  if (/^pvufilter/.test(name)) {
    if (/media/.test(name)) return { kind: "filter_media", section: "filter" };
    if (/frame/.test(name)) return { kind: "filter_frame", section: "filter" };
    return { kind: "filter_other", section: "filter" };
  }
  if (/^pvusilencer/.test(name)) {
    if (/baffle/.test(name)) return { kind: "silencer_baffle", section: "silencer" };
    return { kind: "silencer_other", section: "silencer" };
  }
  if (/^pvuheater/.test(name)) {
    if (/fin/.test(name)) return { kind: "heater_fin", section: "heater" };
    if (/pipe/.test(name)) return { kind: "heater_pipe", section: "heater" };
    if (/frame/.test(name)) return { kind: "heater_frame", section: "heater" };
    return { kind: "heater_other", section: "heater" };
  }
  if (/^pvufan/.test(name)) {
    if (/blade/.test(name)) return { kind: "fan_blade", section: "fan" };
    if (/hub/.test(name)) return { kind: "fan_hub", section: "fan" };
    if (/scroll_housing/.test(name)) return { kind: "fan_housing", section: "fan" };
    if (/inlet/.test(name)) return { kind: "fan_inlet", section: "fan" };
    return { kind: "fan_other", section: "fan" };
  }
  if (/^pvurecuperator/.test(name)) {
    if (/plate/.test(name)) return { kind: "recuperator_plate", section: "recuperator" };
    return { kind: "recuperator_other", section: "recuperator" };
  }
  if (/^pvuexhaust/.test(name)) {
    return { kind: "duct", section: "exhaust" };
  }
  if (/^pvuduct/.test(name)) {
    if (/status_shell/.test(name)) return { kind: "status_shell", section: "duct" };
    return { kind: "duct", section: "duct" };
  }
  if (/^pvuplenum/.test(name)) {
    return { kind: "plenum", section: "duct" };
  }
  if (/^pvubase/.test(name)) {
    return { kind: "base", section: "frame" };
  }
  if (/^pvuinstallation/.test(name)) {
    // pvu.installation, pvu.installation.base — внешний контейнер.
    return { kind: "base", section: "frame" };
  }
  if (/^buildingoutdoor/.test(name)) {
    return { kind: "outdoor_stack", section: "outdoor" };
  }
  if (/^buildingsystemssupply/.test(name) || /^duct/.test(name)) {
    return { kind: "duct", section: "duct" };
  }
  if (/^building/.test(name)) {
    return { kind: "building", section: null };
  }
  if (/^extract/.test(name)) {
    // extract.*flow / extract.plume_* / extract.kitchen_run.flow и т.п.
    if (/flow/.test(name) || /plume/.test(name)) {
      return { kind: "flow", section: null };
    }
    return { kind: "building", section: null };
  }
  if (/^zone/.test(name)) {
    return { kind: "building", section: null };
  }
  if (/^pvuflow/.test(name) || /^flow/.test(name)) {
    return { kind: "flow", section: null };
  }
  if (/^pvusensors/.test(name) || /^buildingsensors/.test(name)) {
    return { kind: "sensor", section: null };
  }
  // Мебель помещения: living.sofa, bedroom_north.bed, study.desk, kitchen.counter, utility.cabinet
  if (
    /^living/.test(name) ||
    /^bedroom/.test(name) ||
    /^study/.test(name) ||
    /^kitchen/.test(name) ||
    /^utility/.test(name) ||
    /^bath/.test(name)
  ) {
    return { kind: "building", section: null };
  }
  return { kind: "other", section: null };
}

let renderer = null;
let composer = null;
let bloomPass = null;
let ssaoPass = null;
let scene = null;
let camera = null;
let controls = null;
let animationId = null;
let clock = null;
let container = null;
let infoCard = null;
let labelLayer = null;
let labelsState = [];
let legendOverlay = null;
let resizeObserver = null;
let modelRoot = null;
let overlayRoot = null;
let environmentRoot = null;
let atmosphereRoot = null;
let floorGlow = null;
let ambientLight = null;
let keyLight = null;
let rimLight = null;
let fillLight = null;
let pmremGenerator = null;
let environmentTexture = null;
let shadowCatcher = null;
let shadowsEnabled = false;
let nodeMap = {};
let bindingMap = {};
let bindingByVisualId = {};
let interactiveObjects = [];
let raycaster = null;
let mouse = new THREE.Vector2();
let hoveredObject = null;
let selectedObject = null;
let currentSignals = null;
let currentDisplayMode = "studio";
let currentCameraPreset = "hero";
let currentModelDescriptor = null;
let currentSceneProfile = null;
let currentRoomDescriptor = null;
let measurementMode = false;
let measurementType = "distance"; // "distance" | "angle"
let measurementPoints = []; // маркеры точек режима расстояния (упорядоченная ломаная)
let measurementAngleMarkers = []; // маркеры точек режима угла
let measurementLines = []; // линии (расстояния и лучи углов)
let measurementArcs = []; // дуги визуализации углов
let measurementLabels = []; // подписи (метры/градусы)
let measurementAngles = []; // [{ a:[x,y,z], vertex:[x,y,z], c:[x,y,z], angle: deg }]
let measurementAnglePending = []; // рабочий буфер Vector3 для текущего угла (макс. 3)
const MEASUREMENT_SESSION_KEY = "pvu3d.measurements.v1";
const MEASUREMENT_SCHEMA_VERSION = "pvu-3d-measurements.v1";
let heatmapMode = false;
let heatmapOverlay = null;
let heatmapLegend = null;
let heatmapDataPoints = [];
let heatmapPreviousDataPoints = [];
let heatmapAnimationProgress = 1.0; // 0.0 = старые данные, 1.0 = новые данные
let heatmapAnimationDuration = 1000; // миллисекунды
let heatmapAnimationStartTime = 0;
let heatmapMinTemp = -10;
let heatmapMaxTemp = 40;
// Clipping planes state
let clippingEnabled = false;
let clippingPlanes = []; // Array of THREE.Plane objects
let clippingHelpers = []; // Visual representation of planes
let clippingPlanesData = []; // Metadata: {normal, constant, enabled, inverted}
let maxClippingPlanes = 3;
// LOD (Level of Detail) state
let lodEnabled = false;
let lodObjects = []; // Array of THREE.LOD objects
let lodDistances = [0, 15, 30]; // Distance thresholds: [high, medium, low]
let lodQuality = "auto"; // "high", "medium", "low", "auto"
let lodStats = { high: 0, medium: 0, low: 0 }; // Current LOD level counts
// Flow field (airflow visualization) state
let flowFieldEnabled = false;
let flowFieldMode = "arrows"; // "arrows" | "streamlines" | "particles"
let flowFieldData = null; // Loaded vector field data
let flowFieldObjects = []; // Visual objects (arrows, lines, particles)
let flowFieldParticles = null; // Particle system for "particles" mode
let flowFieldAnimationTime = 0; // Animation time accumulator
let flowFieldDensity = 0.5; // 0.0 to 1.0, controls vector density
let flowFieldAnimationSpeed = 1.0; // Animation speed multiplier
let flowFieldColorScheme = "speed"; // "speed" | "direction" | "pressure"
// Comparison mode (side-by-side) state
let comparisonMode = false; // true when split-screen is active
let comparisonSplit = 0.5; // Split ratio: 0.3 to 0.7 (left/right)
let comparisonOrientation = "vertical"; // "vertical" | "horizontal"
let comparisonSyncCameras = true; // Sync camera position/target between views
let comparisonBeforeRefId = null; // Reference ID for "before" state
let comparisonAfterRefId = null; // Reference ID for "after" state
let comparisonBeforeData = null; // Loaded "before" comparison data
let comparisonAfterData = null; // Loaded "after" comparison data
let comparisonDiffMode = "status"; // "status" | "temperature" | "power" | "alarms"
let comparisonCompatibility = null; // Compatibility check result
// Dual scene system for comparison mode
let comparisonSceneAfter = null; // Second scene for "after" state
let comparisonCameraAfter = null; // Second camera for "after" state (when not synced)
let comparisonModelRootAfter = null; // Model root for "after" scene
let comparisonOverlayRootAfter = null; // Overlay root for "after" scene
let comparisonEnvironmentRootAfter = null; // Environment root for "after" scene
let comparisonNodeMapAfter = {}; // Node map for "after" scene
let comparisonBindingMapAfter = {}; // Binding map for "after" scene
let comparisonInteractiveObjectsAfter = []; // Interactive objects for "after" scene
// Note: In comparison mode, we use the main renderer with viewport splitting
// and render two different scenes (before/after) for better performance
let currentScaleTuning = {
  model_scale: 1,
  model_long_scale: 1,
  model_side_scale: 1,
  model_vertical_scale: 1,
  model_long_delta: 0,
  model_side_delta: 0,
  model_vertical_delta: 0,
  model_rotation_delta_deg: 0,
  model_pitch_delta_deg: 0,
  model_roll_delta_deg: 0,
  room_scale: 1,
  room_long_delta: 0,
  room_side_delta: 0,
  room_vertical_delta: 0,
  room_rotation_delta_deg: 0,
};
let viewMetrics = null;
let sceneMeta = null;
let upAxis = "Y";
let isInitialized = false;
let sharedLoader = null;
let cachedModelEntries = {};
let pendingModelEntries = {};
let roomModelRoot = null;
let cachedRoomEntries = {};
let pendingRoomEntries = {};
let generatedTextureCache = {};
let atmosphereParticles = null;
let atmosphereParticleMotion = [];
let floorBase = null;
let farRing = null;
let stageBackdrop = null;
let seasonAura = null;

function _materialArray(material) {
  return Array.isArray(material) ? material : [material];
}

function _normalizeSceneNodeId(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9_.]+/g, "");
}

function _getNode(nodeName) {
  return nodeMap[nodeName] || nodeMap[_normalizeSceneNodeId(nodeName)] || null;
}

function _axisVector(axisName) {
  if (axisName === "x") return new THREE.Vector3(1, 0, 0);
  if (axisName === "z") return new THREE.Vector3(0, 0, 1);
  return new THREE.Vector3(0, 1, 0);
}

function _vectorFromAxes(xValue, yValue, zValue) {
  return new THREE.Vector3(xValue || 0, yValue || 0, zValue || 0);
}

function _vectorWithAxis(axisName, value) {
  if (axisName === "x") return _vectorFromAxes(value, 0, 0);
  if (axisName === "z") return _vectorFromAxes(0, 0, value);
  return _vectorFromAxes(0, value, 0);
}

function _lerpByAxis(minVec, maxVec, axisName, t) {
  if (axisName === "x") return THREE.MathUtils.lerp(minVec.x, maxVec.x, t);
  if (axisName === "z") return THREE.MathUtils.lerp(minVec.z, maxVec.z, t);
  return THREE.MathUtils.lerp(minVec.y, maxVec.y, t);
}

function _colorFromHex(value) {
  return typeof value === "string" ? new THREE.Color(value) : new THREE.Color(value || 0xffffff);
}

function _statusToColor(status, colors) {
  var palette = colors || STATUS_COLORS;
  var tone = palette[status] || palette.inactive || STATUS_COLORS.inactive;
  if (typeof tone === "string") {
    return parseInt(tone.replace("#", ""), 16);
  }
  return tone;
}

function _clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function _numericTuningValue(payload, key, fallback, minValue, maxValue) {
  var value = payload && payload[key];
  var numericValue = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numericValue)) {
    numericValue = fallback;
  }
  return _clamp(numericValue, minValue, maxValue);
}

function _sanitizeScaleTuning(payload) {
  var source = payload || {};
  return {
    model_scale: _numericTuningValue(source, "model_scale", 1, 0.1, 12),
    model_long_scale: _numericTuningValue(source, "model_long_scale", 1, 0.1, 5),
    model_side_scale: _numericTuningValue(source, "model_side_scale", 1, 0.1, 5),
    model_vertical_scale: _numericTuningValue(source, "model_vertical_scale", 1, 0.1, 5),
    model_long_delta: _numericTuningValue(source, "model_long_delta", 0, -8, 8),
    model_side_delta: _numericTuningValue(source, "model_side_delta", 0, -8, 8),
    model_vertical_delta: _numericTuningValue(source, "model_vertical_delta", 0, -5, 5),
    model_rotation_delta_deg: _numericTuningValue(source, "model_rotation_delta_deg", 0, -360, 360),
    model_pitch_delta_deg: _numericTuningValue(source, "model_pitch_delta_deg", 0, -90, 90),
    model_roll_delta_deg: _numericTuningValue(source, "model_roll_delta_deg", 0, -90, 90),
    room_scale: _numericTuningValue(source, "room_scale", 1, 0.1, 16),
    room_long_delta: _numericTuningValue(source, "room_long_delta", 0, -8, 8),
    room_side_delta: _numericTuningValue(source, "room_side_delta", 0, -8, 8),
    room_vertical_delta: _numericTuningValue(source, "room_vertical_delta", 0, -5, 5),
    room_rotation_delta_deg: _numericTuningValue(source, "room_rotation_delta_deg", 0, -360, 360),
  };
}

function _scaleTuningChanged(nextTuning) {
  return Object.keys(nextTuning).some(function (key) {
    return Math.abs((currentScaleTuning[key] || 0) - nextTuning[key]) > 1e-6;
  });
}

function _deltaByMetrics(metrics, axisName, value) {
  if (!metrics || !value) return 0;
  if (axisName === metrics.verticalAxis) {
    return (metrics.size[axisName] || metrics.maxDim) * value;
  }
  if (axisName === metrics.sideAxis) {
    return metrics.maxDim * value;
  }
  return (metrics.size[axisName] || metrics.maxDim) * value;
}

function _applyModelTransformTuning() {
  if (!modelRoot) return;
  var baseScale = currentScaleTuning.model_scale || 1;
  modelRoot.position.set(0, 0, 0);
  modelRoot.rotation.set(0, 0, 0);
  modelRoot.scale.setScalar(baseScale);
  modelRoot.updateMatrixWorld(true);
  var metrics = _computeViewMetrics(modelRoot);
  modelRoot.scale[metrics.longAxis] = baseScale * (currentScaleTuning.model_long_scale || 1);
  modelRoot.scale[metrics.sideAxis] = baseScale * (currentScaleTuning.model_side_scale || 1);
  modelRoot.scale[metrics.verticalAxis] = baseScale * (currentScaleTuning.model_vertical_scale || 1);
  modelRoot.rotation[metrics.verticalAxis] = THREE.MathUtils.degToRad(
    currentScaleTuning.model_rotation_delta_deg || 0
  );
  modelRoot.rotation[metrics.sideAxis] = THREE.MathUtils.degToRad(
    currentScaleTuning.model_pitch_delta_deg || 0
  );
  modelRoot.rotation[metrics.longAxis] = THREE.MathUtils.degToRad(
    currentScaleTuning.model_roll_delta_deg || 0
  );
  modelRoot.updateMatrixWorld(true);
  metrics = _computeViewMetrics(modelRoot);
  modelRoot.position.add(
    _vectorWithAxis(
      metrics.longAxis,
      _deltaByMetrics(metrics, metrics.longAxis, currentScaleTuning.model_long_delta)
    )
  );
  modelRoot.position.add(
    _vectorWithAxis(
      metrics.sideAxis,
      _deltaByMetrics(metrics, metrics.sideAxis, currentScaleTuning.model_side_delta)
    )
  );
  modelRoot.position.add(
    _vectorWithAxis(
      metrics.verticalAxis,
      _deltaByMetrics(metrics, metrics.verticalAxis, currentScaleTuning.model_vertical_delta)
    )
  );
  modelRoot.updateMatrixWorld(true);
}

function _themeColor(key, fallback) {
  var theme = currentSceneProfile && currentSceneProfile.theme ? currentSceneProfile.theme : {};
  return _colorFromHex(theme[key] || fallback);
}

function _sceneProfileBlock(sceneProfile, key) {
  if (!sceneProfile) return {};
  return sceneProfile[key] || {};
}

function _profileBlock(key) {
  if (!currentSceneProfile) return {};
  return currentSceneProfile[key] || {};
}

function _sizingValue(key, fallback) {
  var sizing = _profileBlock("sizing") || {};
  var value = sizing[key];
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return fallback;
  }
  return value;
}

function _withDefault(value, fallback) {
  return value === undefined || value === null ? fallback : value;
}

function _parseNumericValue(value) {
  if (typeof value === "number") return value;
  var match = String(value || "").match(/-?\d+(?:[.,]\d+)?/);
  if (!match) return null;
  return Number(match[0].replace(",", "."));
}

function _scenarioToken(signals) {
  if (!signals) return "";
  return [
    String(signals.scenario_id || ""),
    String(signals.scenario_title || ""),
  ]
    .join(" ")
    .toLowerCase();
}

function _scenarioAtmosphereProfile(signals) {
  var token = _scenarioToken(signals);
  var profile = {
    id: "neutral",
    particleMode: "ambient",
    particleColor: "#9dd8ff",
    particleOpacity: 0.22,
    particleSize: 0.06,
    particleSpeed: 0.45,
    auraColor: "#14b8a6",
    auraPulse: 0.08,
    auraSpin: 0.06,
    floorColor: "#0f3d4c",
    farRingColor: "#1e293b",
    backdropOpacity: 0.08,
    moodColor: "#8b9aa7",
    moodBlend: 0.14,
    heaterBoost: 1.0,
    dustBoost: 1.0,
    humidityBoost: 1.0,
  };

  if (token.indexOf("winter") !== -1 || token.indexOf("зима") !== -1) {
    return Object.assign(profile, {
      id: "winter",
      particleMode: "snow",
      particleColor: "#dbeafe",
      particleOpacity: 0.32,
      particleSize: 0.08,
      particleSpeed: 0.92,
      auraColor: "#7dd3fc",
      auraPulse: 0.15,
      auraSpin: 0.05,
      floorColor: "#0a3344",
      farRingColor: "#102a43",
      backdropOpacity: 0.11,
      moodColor: "#60a5fa",
      moodBlend: 0.28,
      heaterBoost: 1.22,
      dustBoost: 1.06,
      humidityBoost: 0.92,
    });
  }

  if (token.indexOf("summer") !== -1 || token.indexOf("лето") !== -1) {
    return Object.assign(profile, {
      id: "summer",
      particleMode: "haze",
      particleColor: "#fed7aa",
      particleOpacity: 0.16,
      particleSize: 0.05,
      particleSpeed: 0.56,
      auraColor: "#fb923c",
      auraPulse: 0.11,
      auraSpin: 0.08,
      floorColor: "#3b2f14",
      farRingColor: "#422006",
      backdropOpacity: 0.1,
      moodColor: "#fb923c",
      moodBlend: 0.24,
      heaterBoost: 0.84,
      dustBoost: 0.95,
      humidityBoost: 1.24,
    });
  }

  if (
    token.indexOf("peak_load") !== -1 ||
    token.indexOf("peak") !== -1 ||
    token.indexOf("пик") !== -1
  ) {
    return Object.assign(profile, {
      id: "peak",
      particleMode: "turbulence",
      particleColor: "#fca5a5",
      particleOpacity: 0.3,
      particleSize: 0.075,
      particleSpeed: 1.1,
      auraColor: "#ef4444",
      auraPulse: 0.19,
      auraSpin: 0.13,
      floorColor: "#3a151a",
      farRingColor: "#4c1d1d",
      backdropOpacity: 0.14,
      moodColor: "#ef4444",
      moodBlend: 0.36,
      heaterBoost: 1.25,
      dustBoost: 1.32,
      humidityBoost: 1.18,
    });
  }

  if (
    token.indexOf("dirty_filter") !== -1 ||
    token.indexOf("filter") !== -1 ||
    token.indexOf("загряз") !== -1
  ) {
    return Object.assign(profile, {
      id: "dirty_filter",
      particleMode: "turbulence",
      particleColor: "#fef08a",
      particleOpacity: 0.26,
      particleSize: 0.07,
      particleSpeed: 0.92,
      auraColor: "#f59e0b",
      auraPulse: 0.13,
      auraSpin: 0.1,
      floorColor: "#3f3212",
      farRingColor: "#422c05",
      backdropOpacity: 0.1,
      moodColor: "#f59e0b",
      moodBlend: 0.24,
      heaterBoost: 1.08,
      dustBoost: 1.45,
      humidityBoost: 1.0,
    });
  }

  return profile;
}

function _descriptorKey(modelDescriptor, modelUrl) {
  return String(
    (modelDescriptor && modelDescriptor.id) ||
    modelUrl ||
    "scene-model"
  );
}

function _accentColorForDescriptor(modelDescriptor) {
  return _colorFromHex(
    (modelDescriptor && modelDescriptor.accent) || DEFAULT_MODEL_ACCENT
  );
}

function _toneBaseColor(modelDescriptor) {
  var tone = String((modelDescriptor && modelDescriptor.tone) || "industrial").toLowerCase();
  var accent = _accentColorForDescriptor(modelDescriptor);
  if (tone === "office") return new THREE.Color(0xd7dee3).lerp(accent, 0.14);
  if (tone === "classroom") return new THREE.Color(0xd8dbc8).lerp(accent, 0.12);
  if (tone === "lab") return new THREE.Color(0xd9d4ce).lerp(accent, 0.16);
  if (tone === "room") return new THREE.Color(0xd9ded8).lerp(accent, 0.12);
  if (tone === "precision") return new THREE.Color(0xc7d9e8).lerp(accent, 0.16);
  if (tone === "xray") return new THREE.Color(0xd5d1c9).lerp(accent, 0.18);
  if (tone === "clean") return new THREE.Color(0xd9dfdd).lerp(accent, 0.12);
  if (tone === "studio") return new THREE.Color(0xcfd8d5).lerp(accent, 0.14);
  return new THREE.Color(0xd4d9dd).lerp(accent, 0.12);
}

function _makeCanvasTexture(width, height, painter) {
  var canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  var ctx = canvas.getContext("2d");
  painter(ctx, canvas);
  var texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.anisotropy = 4;
  texture.needsUpdate = true;
  return texture;
}

function _textureBundleForDescriptor(modelDescriptor) {
  var key = _descriptorKey(modelDescriptor, null) + ":" + ((modelDescriptor && modelDescriptor.accent) || DEFAULT_MODEL_ACCENT);
  if (generatedTextureCache[key]) {
    return generatedTextureCache[key];
  }

  var baseColor = _toneBaseColor(modelDescriptor);
  var accent = _accentColorForDescriptor(modelDescriptor);
  var darkColor = baseColor.clone().multiplyScalar(0.58);
  var brightColor = baseColor.clone().lerp(new THREE.Color(0xffffff), 0.22);

  var map = _makeCanvasTexture(768, 768, function (ctx, canvas) {
    var gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, "#" + darkColor.getHexString());
    gradient.addColorStop(0.5, "#" + baseColor.getHexString());
    gradient.addColorStop(1, "#" + brightColor.getHexString());
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.globalAlpha = 0.18;
    ctx.fillStyle = "#" + accent.getHexString();
    for (var row = 0; row < 10; row += 1) {
      ctx.fillRect(0, row * 78 + 18, canvas.width, 6);
    }

    ctx.globalAlpha = 0.12;
    ctx.fillStyle = "rgba(255,255,255,0.9)";
    for (var col = 0; col < 8; col += 1) {
      ctx.fillRect(col * 96 + 12, 0, 2, canvas.height);
    }

    ctx.globalAlpha = 0.42;
    ctx.fillStyle = "rgba(255,255,255,0.65)";
    for (var ix = 0; ix < 7; ix += 1) {
      for (var iy = 0; iy < 7; iy += 1) {
        ctx.beginPath();
        ctx.arc(ix * 110 + 42, iy * 110 + 34, 4, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    ctx.globalAlpha = 0.08;
    for (var noiseIndex = 0; noiseIndex < 1200; noiseIndex += 1) {
      var tone = 120 + Math.floor(Math.random() * 80);
      ctx.fillStyle = "rgba(" + tone + "," + tone + "," + tone + ",0.55)";
      ctx.fillRect(
        Math.random() * canvas.width,
        Math.random() * canvas.height,
        2 + Math.random() * 4,
        2 + Math.random() * 4
      );
    }
  });
  map.colorSpace = THREE.SRGBColorSpace;
  map.repeat.set(2.4, 1.6);

  var roughnessMap = _makeCanvasTexture(512, 512, function (ctx, canvas) {
    ctx.fillStyle = "rgb(176,176,176)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "rgba(88,88,88,0.45)";
    for (var band = 0; band < 11; band += 1) {
      ctx.fillRect(0, band * 46 + 8, canvas.width, 10);
    }
    ctx.fillStyle = "rgba(210,210,210,0.2)";
    for (var n = 0; n < 1500; n += 1) {
      var value = 80 + Math.floor(Math.random() * 120);
      ctx.fillStyle = "rgba(" + value + "," + value + "," + value + ",0.35)";
      ctx.fillRect(Math.random() * canvas.width, Math.random() * canvas.height, 2, 2);
    }
  });
  roughnessMap.repeat.copy(map.repeat);

  generatedTextureCache[key] = {
    map: map,
    roughnessMap: roughnessMap,
  };
  return generatedTextureCache[key];
}

function _normalizedDeltaByAxis(axisName, value) {
  if (!value) return 0;
  if (axisName === viewMetrics.verticalAxis) {
    return (viewMetrics.size[axisName] || viewMetrics.maxDim) * value;
  }
  if (axisName === viewMetrics.sideAxis) {
    return viewMetrics.maxDim * value;
  }
  return (viewMetrics.size[axisName] || viewMetrics.maxDim) * value;
}

function _disposeMaterial(material) {
  if (!material) return;
  [
    "map",
    "alphaMap",
    "aoMap",
    "bumpMap",
    "normalMap",
    "emissiveMap",
    "metalnessMap",
    "roughnessMap",
    "clearcoatMap",
    "clearcoatNormalMap",
    "clearcoatRoughnessMap",
    "transmissionMap",
    "thicknessMap",
    "specularColorMap",
    "specularIntensityMap",
    "envMap",
  ].forEach(function (key) {
    if (material[key] && material[key].isTexture) {
      material[key].dispose();
    }
  });
  material.dispose();
}

function _disposeObject(root) {
  if (!root) return;
  root.traverse(function (child) {
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      _materialArray(child.material).forEach(_disposeMaterial);
    }
  });
}

function _ensureModelMaterialState(material) {
  if (material.userData && material.userData.__pvuBaseState) {
    return material.userData.__pvuBaseState;
  }
  var state = {
    color: material.color ? material.color.clone() : new THREE.Color(0xb6c2cb),
    emissive: material.emissive ? material.emissive.clone() : new THREE.Color(0x000000),
    emissiveIntensity: material.emissiveIntensity || 0,
    transparent: material.transparent === true,
    opacity: typeof material.opacity === "number" ? material.opacity : 1,
    roughness: typeof material.roughness === "number" ? material.roughness : 0.7,
    metalness: typeof material.metalness === "number" ? material.metalness : 0.18,
    depthWrite: material.depthWrite !== false,
  };
  material.userData = material.userData || {};
  material.userData.__pvuBaseState = state;
  return state;
}

function _prepareModelMesh(mesh, modelDescriptor) {
  if (!mesh || !mesh.isMesh || !mesh.material) return;
  var textureBundle = _textureBundleForDescriptor(modelDescriptor);
  var accentColor = _accentColorForDescriptor(modelDescriptor);
  var normalized = _materialArray(mesh.material).map(function (source) {
    if (!source) {
      var fallbackMaterial = new THREE.MeshStandardMaterial({
        color: 0x98a7b2,
        roughness: 0.76,
        metalness: 0.18,
      });
      fallbackMaterial.map = textureBundle.map;
      fallbackMaterial.roughnessMap = textureBundle.roughnessMap;
      return fallbackMaterial;
    }
    var material = source.isMeshStandardMaterial || source.isMeshPhysicalMaterial
      ? source.clone()
      : new THREE.MeshStandardMaterial({
          color: source.color ? source.color.clone() : new THREE.Color(0x98a7b2),
          transparent: source.transparent === true,
          opacity: typeof source.opacity === "number" ? source.opacity : 1,
          roughness: 0.76,
          metalness: 0.18,
        });
    material.side = THREE.DoubleSide;
    if (!material.emissive) {
      material.emissive = new THREE.Color(0x000000);
      material.emissiveIntensity = 0;
    }
    if (!material.map) {
      material.map = textureBundle.map;
    }
    if (!material.roughnessMap) {
      material.roughnessMap = textureBundle.roughnessMap;
    }
    material.color.lerp(accentColor, 0.03);
    _ensureModelMaterialState(material);
    material.needsUpdate = true;
    return material;
  });
  mesh.material = Array.isArray(mesh.material) ? normalized : normalized[0];
  mesh.castShadow = shadowsEnabled;
  mesh.receiveShadow = true;
}

function _showLoading(text) {
  if (!container) return;
  _removeOverlay();
  var overlay = document.createElement("div");
  overlay.className = "viewer3d-overlay";
  overlay.id = "viewer3d-overlay";
  overlay.innerHTML = '<div class="viewer3d-overlay-text">' + (text || "Загрузка 3D-сцены…") + "</div>";
  container.appendChild(overlay);
}

function _updateLoading(text) {
  var overlay = document.getElementById("viewer3d-overlay");
  if (!overlay) return;
  var textNode = overlay.querySelector(".viewer3d-overlay-text");
  if (textNode) textNode.textContent = text;
}

function _showError(text) {
  if (!container) return;
  _removeOverlay();
  var overlay = document.createElement("div");
  overlay.className = "viewer3d-overlay viewer3d-overlay-error";
  overlay.id = "viewer3d-overlay";
  overlay.innerHTML = '<div class="viewer3d-overlay-text">' + text + "</div>";
  container.appendChild(overlay);
}

function _removeOverlay() {
  var overlay = document.getElementById("viewer3d-overlay");
  if (overlay) overlay.remove();
}

function _createInfoCard() {
  infoCard = document.createElement("div");
  infoCard.className = "viewer3d-info-card";
  infoCard.style.display = "none";
  document.body.appendChild(infoCard);
}

function _escapeHtml(text) {
  return String(text == null ? "" : text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function _showInfoCard(target, x, y) {
  if (!infoCard || !target || !target.userData || !target.userData.pvuSignal) return;
  var signal = target.userData.pvuSignal;
  var state = signal.state || "normal";
  var stateText = STATE_LABEL_RU[state] || STATE_LABEL_RU.normal;
  var alarmText = signal.alarm_text
    ? '<div class="viewer3d-info-alarm">' + _escapeHtml(signal.alarm_text) + "</div>"
    : "";
  infoCard.dataset.state = state;
  infoCard.innerHTML =
    '<div class="viewer3d-info-head">' +
    '<span class="viewer3d-info-label">' + _escapeHtml(signal.label || target.name || "Сигнал") + "</span>" +
    '<span class="viewer3d-info-state viewer3d-info-state--' + state + '">' + _escapeHtml(stateText) + "</span>" +
    "</div>" +
    '<div class="viewer3d-info-value">' + _escapeHtml(signal.value || "—") + "</div>" +
    (signal.detail ? '<div class="viewer3d-info-detail">' + _escapeHtml(signal.detail) + "</div>" : "") +
    alarmText;
  infoCard.style.display = "block";
  infoCard.style.left = (x + 18) + "px";
  infoCard.style.top = (y - 8) + "px";
  var rect = infoCard.getBoundingClientRect();
  if (rect.right > window.innerWidth) {
    infoCard.style.left = (x - rect.width - 18) + "px";
  }
  if (rect.bottom > window.innerHeight) {
    infoCard.style.top = (y - rect.height - 8) + "px";
  }
}

function _hideInfoCard() {
  if (infoCard) infoCard.style.display = "none";
}

/**
 * Создаёт overlay-слой с приоритетными подписями секций ПВУ.
 * Слой накладывается на canvas (pointer-events: none, чтобы не блокировать
 * раскрутку OrbitControls). На каждом frame `_updateLabels` обновляет
 * positions и state.
 */
function _createLabelLayer() {
  if (!container) return;
  labelLayer = document.createElement("div");
  labelLayer.className = "viewer3d-label-layer";
  container.appendChild(labelLayer);
  labelsState = PRIORITY_LABELS.map(function (spec) {
    var el = document.createElement("div");
    el.className = "viewer3d-label viewer3d-label--" + spec.type;
    el.textContent = spec.text;
    el.dataset.nodeId = spec.node;
    labelLayer.appendChild(el);
    return Object.assign({}, spec, { element: el, lastVisible: false });
  });
}

function _removeLabelLayer() {
  if (labelLayer && labelLayer.parentNode) {
    labelLayer.parentNode.removeChild(labelLayer);
  }
  labelLayer = null;
  labelsState = [];
}

/**
 * Создаёт легенду статусов / температурных тонов / потоков.
 * Лежит в правом нижнем углу контейнера и не мешает orbit-вращению.
 */
function _createLegendOverlay() {
  if (!container) return;
  legendOverlay = document.createElement("div");
  legendOverlay.className = "viewer3d-legend";
  legendOverlay.innerHTML =
    '<div class="viewer3d-legend__title">Легенда</div>' +
    '<div class="viewer3d-legend__group">' +
    '<div class="viewer3d-legend__group-title">Состояние</div>' +
    '<div class="viewer3d-legend__row"><span class="viewer3d-legend__dot" style="background:#22c55e"></span>Норма</div>' +
    '<div class="viewer3d-legend__row"><span class="viewer3d-legend__dot" style="background:#facc15"></span>Риск</div>' +
    '<div class="viewer3d-legend__row"><span class="viewer3d-legend__dot" style="background:#ef4444"></span>Авария</div>' +
    "</div>" +
    '<div class="viewer3d-legend__group">' +
    '<div class="viewer3d-legend__group-title">Температура</div>' +
    '<div class="viewer3d-legend__row"><span class="viewer3d-legend__dot" style="background:#38bdf8"></span>&lt; 18 °C</div>' +
    '<div class="viewer3d-legend__row"><span class="viewer3d-legend__dot" style="background:#d1d5db"></span>20–24 °C</div>' +
    '<div class="viewer3d-legend__row"><span class="viewer3d-legend__dot" style="background:#f97316"></span>&gt; 26 °C</div>' +
    "</div>" +
    '<div class="viewer3d-legend__group">' +
    '<div class="viewer3d-legend__group-title">Поток</div>' +
    '<div class="viewer3d-legend__row"><span class="viewer3d-legend__dot" style="background:#22d3ee"></span>Воздухопоток</div>' +
    '<div class="viewer3d-legend__row"><span class="viewer3d-legend__dot" style="background:#fbbf24"></span>Клапаны</div>' +
    "</div>" +
    '<div class="viewer3d-legend__hint">Курсор/тап по узлу — карточка с показаниями</div>';
  container.appendChild(legendOverlay);
}

function _initPostProcessing() {
  if (!renderer || !scene || !camera) return;

  // Create EffectComposer
  composer = new EffectComposer(renderer);

  // Add RenderPass (основной проход рендеринга)
  var renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);

  // Add SSAOPass (ambient occlusion) — опционально, выключено по умолчанию.
  // Когда выключен, EffectComposer пропускает проход (поведение идентично прежнему).
  // SSAO требует depth/normal render targets; если конструктор упадёт
  // (например, WebGL1-контекст без depth texture), деградируем мягко: оставляем
  // ssaoPass = null и не роняем весь вьюер. Все вызовы setSSAO*/getSSAO* уже
  // защищены null-проверкой, поэтому эффект просто будет недоступен.
  try {
    ssaoPass = new SSAOPass(
      scene,
      camera,
      window.innerWidth,
      window.innerHeight
    );
    // Параметры подобраны под масштаб модели (несколько метров);
    // дефолты three.js (8 / 0.005 / 0.1) рассчитаны на крупные сцены.
    ssaoPass.kernelRadius = 0.5;
    ssaoPass.minDistance = 0.002;
    ssaoPass.maxDistance = 0.06;
    ssaoPass.output = SSAOPass.OUTPUT.Default;
    ssaoPass.enabled = false;
    composer.addPass(ssaoPass);
  } catch (err) {
    ssaoPass = null;
    if (window.console && console.warn) {
      console.warn("SSAO недоступен в этом окружении, эффект отключён:", err);
    }
  }

  // Add UnrealBloomPass (эффект свечения)
  bloomPass = new UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    1.2,    // strength - интенсивность свечения
    0.4,    // radius - радиус размытия
    0.85    // threshold - порог яркости для свечения
  );
  bloomPass.enabled = true;
  composer.addPass(bloomPass);

  // OutputPass удалён: RenderPass уже применяет ACESFilmicToneMapping
  // через renderer.render(scene, camera). Двойное тонирование (RenderPass
  // ACES + OutputPass ACES) дробило midtones/тени в почти-чёрный.
}

function _createSphereMarker(position, color) {
  var pointGeometry = new THREE.SphereGeometry(0.05, 16, 16);
  var pointMaterial = new THREE.MeshBasicMaterial({
    color: color,
    transparent: true,
    opacity: 0.8,
  });
  var point = new THREE.Mesh(pointGeometry, pointMaterial);
  point.position.copy(position);

  // Добавляем glow эффект
  var glowGeometry = new THREE.SphereGeometry(0.08, 16, 16);
  var glowMaterial = new THREE.MeshBasicMaterial({
    color: color,
    transparent: true,
    opacity: 0.3,
    depthWrite: false,
  });
  var glow = new THREE.Mesh(glowGeometry, glowMaterial);
  point.add(glow);

  overlayRoot.add(point);
  return point;
}

function _createMeasurementPoint(position) {
  var point = _createSphereMarker(position, 0x00ff00);
  measurementPoints.push(point);
  return point;
}

function _createAngleMarker(position) {
  var point = _createSphereMarker(position, 0x22d3ee);
  measurementAngleMarkers.push(point);
  return point;
}

function _createMeasurementSegment(from, to, color) {
  var lineGeometry = new THREE.BufferGeometry().setFromPoints([from, to]);
  var lineMaterial = new THREE.LineBasicMaterial({
    color: color,
    linewidth: 2,
    transparent: true,
    opacity: 0.8,
  });
  var line = new THREE.Line(lineGeometry, lineMaterial);
  overlayRoot.add(line);
  measurementLines.push(line);
  return line;
}

function _createMeasurementLine(point1, point2, distance) {
  var lineGeometry = new THREE.BufferGeometry().setFromPoints([
    point1.position,
    point2.position,
  ]);
  var lineMaterial = new THREE.LineBasicMaterial({
    color: 0x00ff00,
    linewidth: 2,
    transparent: true,
    opacity: 0.8,
  });
  var line = new THREE.Line(lineGeometry, lineMaterial);
  overlayRoot.add(line);
  measurementLines.push(line);

  // Создаём label с расстоянием
  var midpoint = new THREE.Vector3()
    .addVectors(point1.position, point2.position)
    .multiplyScalar(0.5);
  _createMeasurementLabel(midpoint, distance.toFixed(2) + " м");

  return line;
}

function _createMeasurementLabel(position, text) {
  var canvas = document.createElement("canvas");
  var context = canvas.getContext("2d");
  canvas.width = 256;
  canvas.height = 64;

  context.fillStyle = "rgba(0, 0, 0, 0.7)";
  context.fillRect(0, 0, canvas.width, canvas.height);

  context.font = "Bold 24px Arial";
  context.fillStyle = "white";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(text, canvas.width / 2, canvas.height / 2);

  var texture = new THREE.CanvasTexture(canvas);
  var spriteMaterial = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthTest: false,
  });
  var sprite = new THREE.Sprite(spriteMaterial);
  sprite.position.copy(position);
  sprite.scale.set(0.5, 0.125, 1);

  overlayRoot.add(sprite);
  measurementLabels.push(sprite);
  return sprite;
}

function _disposeMeasurementObject(obj) {
  obj.traverse(function (child) {
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      if (child.material.map) child.material.map.dispose();
      child.material.dispose();
    }
  });
}

function _clearMeasurements() {
  [
    measurementPoints,
    measurementAngleMarkers,
    measurementLines,
    measurementArcs,
    measurementLabels,
  ].forEach(function (collection) {
    collection.forEach(function (obj) {
      overlayRoot.remove(obj);
      _disposeMeasurementObject(obj);
    });
  });
  measurementPoints = [];
  measurementAngleMarkers = [];
  measurementLines = [];
  measurementArcs = [];
  measurementLabels = [];
  measurementAngles = [];
  measurementAnglePending = [];
}

function setMeasurementMode(enabled) {
  measurementMode = enabled === true;
  if (!measurementMode) {
    _clearMeasurements();
  }
  return true;
}

function setMeasurementType(type) {
  measurementType = type === "angle" ? "angle" : "distance";
  // Сбрасываем незавершённый угол при смене режима
  measurementAnglePending = [];
  return measurementType;
}

function _computeAngleDegrees(a, vertex, c) {
  var v1 = new THREE.Vector3().subVectors(a, vertex);
  var v2 = new THREE.Vector3().subVectors(c, vertex);
  if (v1.lengthSq() === 0 || v2.lengthSq() === 0) {
    return 0;
  }
  return (v1.angleTo(v2) * 180) / Math.PI;
}

function _createAngleArc(a, vertex, c, angleDeg) {
  var v1 = new THREE.Vector3().subVectors(a, vertex);
  var v2 = new THREE.Vector3().subVectors(c, vertex);
  var len1 = v1.length();
  var len2 = v2.length();
  if (len1 === 0 || len2 === 0) {
    return;
  }
  var radius = _clamp(Math.min(len1, len2) * 0.3, 0.1, 0.6);
  v1.normalize();
  v2.normalize();
  var axis = new THREE.Vector3().crossVectors(v1, v2);
  if (axis.lengthSq() < 1e-8) {
    // Точки коллинеарны — дугу не строим, только подпись.
    // Для 180° сумма v1+v2 ≈ 0 (даёт NaN после normalize), поэтому подстраховываемся.
    var flatDir = new THREE.Vector3().addVectors(v1, v2);
    if (flatDir.lengthSq() < 1e-8) {
      flatDir.copy(v1);
    }
    flatDir.normalize().multiplyScalar(radius * 1.5).add(vertex);
    _createMeasurementLabel(flatDir, angleDeg.toFixed(1) + "°");
    return;
  }
  axis.normalize();
  var totalRad = v1.angleTo(v2);
  var segments = 32;
  var points = [];
  for (var i = 0; i <= segments; i += 1) {
    var t = (i / segments) * totalRad;
    var quat = new THREE.Quaternion().setFromAxisAngle(axis, t);
    var dir = v1.clone().applyQuaternion(quat).multiplyScalar(radius);
    points.push(new THREE.Vector3().addVectors(vertex, dir));
  }
  var arcGeometry = new THREE.BufferGeometry().setFromPoints(points);
  var arcMaterial = new THREE.LineBasicMaterial({
    color: 0xfbbf24,
    transparent: true,
    opacity: 0.9,
  });
  var arc = new THREE.Line(arcGeometry, arcMaterial);
  overlayRoot.add(arc);
  measurementArcs.push(arc);

  var midQuat = new THREE.Quaternion().setFromAxisAngle(axis, totalRad / 2);
  var labelPos = v1
    .clone()
    .applyQuaternion(midQuat)
    .multiplyScalar(radius * 1.5)
    .add(vertex);
  _createMeasurementLabel(labelPos, angleDeg.toFixed(1) + "°");
}

function _createAngleVisual(a, vertex, c, angleDeg) {
  _createMeasurementSegment(vertex, a, 0x22d3ee);
  _createMeasurementSegment(vertex, c, 0x22d3ee);
  _createAngleArc(a, vertex, c, angleDeg);
}

function _pushAngleRecord(a, vertex, c, angleDeg) {
  measurementAngles.push({
    a: a.toArray(),
    vertex: vertex.toArray(),
    c: c.toArray(),
    angle: angleDeg,
  });
}

function _addAnglePoint(position) {
  _createAngleMarker(position);
  measurementAnglePending.push(position.clone());
  if (measurementAnglePending.length >= 3) {
    var a = measurementAnglePending[0];
    var vertex = measurementAnglePending[1];
    var c = measurementAnglePending[2];
    var angleDeg = _computeAngleDegrees(a, vertex, c);
    _createAngleVisual(a, vertex, c, angleDeg);
    _pushAngleRecord(a, vertex, c, angleDeg);
    measurementAnglePending = [];
  }
  // Сохраняем состояние и для незавершённого угла (1–2 точки)
  _persistMeasurements();
}

function getMeasurements() {
  var measurements = [];
  for (var i = 0; i < measurementPoints.length - 1; i += 1) {
    var p1 = measurementPoints[i].position;
    var p2 = measurementPoints[i + 1].position;
    var distance = p1.distanceTo(p2);
    measurements.push({
      point1: p1.toArray(),
      point2: p2.toArray(),
      distance: distance,
    });
  }
  return measurements;
}

function getMeasurementAngles() {
  return measurementAngles.map(function (record) {
    return {
      a: record.a.slice(),
      vertex: record.vertex.slice(),
      c: record.c.slice(),
      angle: record.angle,
    };
  });
}

function getAllMeasurements() {
  return {
    distances: getMeasurements(),
    angles: getMeasurementAngles(),
  };
}

function clearMeasurements() {
  _clearMeasurements();
  _persistMeasurements();
  return true;
}

// --- Сохранение измерений в session storage ---

function _isVec3Array(arr) {
  return (
    Array.isArray(arr) &&
    arr.length >= 3 &&
    isFinite(arr[0]) &&
    isFinite(arr[1]) &&
    isFinite(arr[2])
  );
}

function _serializeMeasurements() {
  return {
    distancePoints: measurementPoints.map(function (point) {
      return point.position.toArray();
    }),
    angles: getMeasurementAngles(),
    pendingAngle: measurementAnglePending.map(function (vec) {
      return vec.toArray();
    }),
  };
}

function _persistMeasurements() {
  try {
    if (typeof sessionStorage === "undefined") {
      return false;
    }
    var payload = {
      schemaVersion: MEASUREMENT_SCHEMA_VERSION,
      savedAt: new Date().toISOString(),
      data: _serializeMeasurements(),
    };
    sessionStorage.setItem(MEASUREMENT_SESSION_KEY, JSON.stringify(payload));
    return true;
  } catch (err) {
    return false;
  }
}

function saveMeasurementsToSession() {
  return _persistMeasurements();
}

function loadMeasurementsFromSession() {
  try {
    if (typeof sessionStorage === "undefined") {
      return null;
    }
    var raw = sessionStorage.getItem(MEASUREMENT_SESSION_KEY);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw);
  } catch (err) {
    return null;
  }
}

function restoreMeasurementsFromSession() {
  var payload = loadMeasurementsFromSession();
  if (!payload || payload.schemaVersion !== MEASUREMENT_SCHEMA_VERSION || !payload.data) {
    return false;
  }
  _clearMeasurements();
  var data = payload.data;

  if (Array.isArray(data.distancePoints)) {
    data.distancePoints.forEach(function (coords) {
      if (!_isVec3Array(coords)) {
        return;
      }
      var position = new THREE.Vector3().fromArray(coords);
      _createMeasurementPoint(position);
      if (measurementPoints.length >= 2) {
        var p1 = measurementPoints[measurementPoints.length - 2];
        var p2 = measurementPoints[measurementPoints.length - 1];
        _createMeasurementLine(p1, p2, p1.position.distanceTo(p2.position));
      }
    });
  }

  if (Array.isArray(data.angles)) {
    data.angles.forEach(function (record) {
      if (
        !record ||
        !_isVec3Array(record.a) ||
        !_isVec3Array(record.vertex) ||
        !_isVec3Array(record.c)
      ) {
        return;
      }
      var a = new THREE.Vector3().fromArray(record.a);
      var vertex = new THREE.Vector3().fromArray(record.vertex);
      var c = new THREE.Vector3().fromArray(record.c);
      _createAngleMarker(a);
      _createAngleMarker(vertex);
      _createAngleMarker(c);
      var angleDeg =
        typeof record.angle === "number"
          ? record.angle
          : _computeAngleDegrees(a, vertex, c);
      _createAngleVisual(a, vertex, c, angleDeg);
      _pushAngleRecord(a, vertex, c, angleDeg);
    });
  }

  if (Array.isArray(data.pendingAngle)) {
    data.pendingAngle.forEach(function (coords) {
      // Незавершённый угол содержит максимум 2 точки
      if (measurementAnglePending.length >= 2 || !_isVec3Array(coords)) {
        return;
      }
      var position = new THREE.Vector3().fromArray(coords);
      _createAngleMarker(position);
      measurementAnglePending.push(position.clone());
    });
  }

  return true;
}

// --- Экспорт измерений ---

function _triggerMeasurementDownload(content, filename, mimeType) {
  var blob = new Blob([content], { type: mimeType });
  var url = URL.createObjectURL(blob);
  var link = document.createElement("a");
  link.download = filename;
  link.href = url;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  setTimeout(function () {
    URL.revokeObjectURL(url);
  }, 0);
  return true;
}

function _measurementExportFilename(ext) {
  var timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  return "pvu3d_measurements_" + timestamp + "." + ext;
}

function _fmtCoord(value) {
  return Number(value).toFixed(4);
}

function exportMeasurements(format) {
  var fmt = format === "csv" ? "csv" : "json";
  var all = getAllMeasurements();
  var total = all.distances.length + all.angles.length;
  if (total === 0) {
    return null;
  }

  if (fmt === "json") {
    var payload = {
      schemaVersion: MEASUREMENT_SCHEMA_VERSION,
      generatedAt: new Date().toISOString(),
      units: { distance: "m", angle: "deg" },
      distances: all.distances,
      angles: all.angles,
    };
    _triggerMeasurementDownload(
      JSON.stringify(payload, null, 2),
      _measurementExportFilename("json"),
      "application/json"
    );
  } else {
    var rows = [];
    rows.push(
      [
        "type",
        "index",
        "p1_x",
        "p1_y",
        "p1_z",
        "p2_x",
        "p2_y",
        "p2_z",
        "p3_x",
        "p3_y",
        "p3_z",
        "value",
        "unit",
      ].join(",")
    );
    all.distances.forEach(function (d, index) {
      rows.push(
        [
          "distance",
          index + 1,
          _fmtCoord(d.point1[0]),
          _fmtCoord(d.point1[1]),
          _fmtCoord(d.point1[2]),
          _fmtCoord(d.point2[0]),
          _fmtCoord(d.point2[1]),
          _fmtCoord(d.point2[2]),
          "",
          "",
          "",
          d.distance.toFixed(4),
          "m",
        ].join(",")
      );
    });
    all.angles.forEach(function (g, index) {
      rows.push(
        [
          "angle",
          index + 1,
          _fmtCoord(g.a[0]),
          _fmtCoord(g.a[1]),
          _fmtCoord(g.a[2]),
          _fmtCoord(g.vertex[0]),
          _fmtCoord(g.vertex[1]),
          _fmtCoord(g.vertex[2]),
          _fmtCoord(g.c[0]),
          _fmtCoord(g.c[1]),
          _fmtCoord(g.c[2]),
          g.angle.toFixed(2),
          "deg",
        ].join(",")
      );
    });
    _triggerMeasurementDownload(
      rows.join("\n") + "\n",
      _measurementExportFilename("csv"),
      "text/csv"
    );
  }

  return {
    format: fmt,
    distances: all.distances.length,
    angles: all.angles.length,
  };
}

function captureScreenshot(options) {
  if (!renderer || !scene || !camera) {
    return Promise.reject(new Error("Viewer not initialized"));
  }

  var opts = options || {};
  var scale = opts.scale || 1;
  var format = opts.format || "png";
  var includeMetadata = opts.includeMetadata !== false;
  var transparent = opts.transparent === true;

  // Сохраняем текущие размеры
  var originalWidth = renderer.domElement.width;
  var originalHeight = renderer.domElement.height;
  var originalPixelRatio = renderer.getPixelRatio();

  try {
    // Устанавливаем новые размеры для высокого разрешения
    var targetWidth = originalWidth * scale;
    var targetHeight = originalHeight * scale;

    renderer.setPixelRatio(1);
    renderer.setSize(targetWidth, targetHeight, false);

    if (composer) {
      composer.setSize(targetWidth, targetHeight);
      if (bloomPass) {
        bloomPass.resolution.set(targetWidth, targetHeight);
      }
    }

    // Рендерим сцену
    if (composer) {
      composer.render();
    } else {
      renderer.render(scene, camera);
    }

    // Захватываем изображение
    var mimeType = format === "jpg" || format === "jpeg"
      ? "image/jpeg"
      : "image/png";
    var dataUrl = renderer.domElement.toDataURL(mimeType, 0.95);

    // Восстанавливаем оригинальные размеры
    renderer.setPixelRatio(originalPixelRatio);
    renderer.setSize(originalWidth, originalHeight, false);

    if (composer) {
      composer.setSize(originalWidth, originalHeight);
      if (bloomPass) {
        bloomPass.resolution.set(originalWidth, originalHeight);
      }
    }

    // Формируем метаданные
    var metadata = null;
    if (includeMetadata) {
      metadata = {
        timestamp: new Date().toISOString(),
        resolution: {
          width: targetWidth,
          height: targetHeight,
          scale: scale,
        },
        camera: {
          position: camera.position.toArray(),
          target: controls ? controls.target.toArray() : null,
          preset: currentCameraPreset,
        },
        scene: {
          displayMode: currentDisplayMode,
          modelId: currentModelDescriptor ? currentModelDescriptor.id : null,
          scenario: currentSignals ? currentSignals.scenario_id : null,
        },
        effects: {
          bloom: bloomPass ? {
            enabled: bloomPass.enabled,
            strength: bloomPass.strength,
            radius: bloomPass.radius,
            threshold: bloomPass.threshold,
          } : null,
        },
      };
    }

    return Promise.resolve({
      dataUrl: dataUrl,
      width: targetWidth,
      height: targetHeight,
      format: format,
      metadata: metadata,
      filename: _generateScreenshotFilename(format),
    });
  } catch (error) {
    // Восстанавливаем размеры в случае ошибки
    renderer.setPixelRatio(originalPixelRatio);
    renderer.setSize(originalWidth, originalHeight, false);

    if (composer) {
      composer.setSize(originalWidth, originalHeight);
    }

    return Promise.reject(error);
  }
}

function _generateScreenshotFilename(format) {
  var now = new Date();
  var timestamp = now.toISOString()
    .replace(/:/g, "-")
    .replace(/\..+/, "")
    .replace("T", "_");
  var modelName = currentModelDescriptor && currentModelDescriptor.id
    ? currentModelDescriptor.id
    : "scene";
  var ext = format === "jpg" || format === "jpeg" ? "jpg" : "png";
  return "pvu3d_" + modelName + "_" + timestamp + "." + ext;
}

function downloadScreenshot(screenshotData) {
  if (!screenshotData || !screenshotData.dataUrl) {
    return false;
  }

  var link = document.createElement("a");
  link.download = screenshotData.filename;
  link.href = screenshotData.dataUrl;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  return true;
}

function _createHeatmapGradientTexture() {
  var canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 1;
  var ctx = canvas.getContext("2d");

  var gradient = ctx.createLinearGradient(0, 0, 256, 0);
  // Холодный → Комфортный → Тёплый → Горячий
  gradient.addColorStop(0.0, "#0ea5e9");  // Холодный синий
  gradient.addColorStop(0.25, "#22d3ee"); // Голубой
  gradient.addColorStop(0.5, "#10b981");  // Зелёный (комфорт)
  gradient.addColorStop(0.75, "#f59e0b"); // Оранжевый
  gradient.addColorStop(1.0, "#ef4444");  // Красный (горячий)

  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 256, 1);

  var texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.ClampToEdgeWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.needsUpdate = true;
  return texture;
}

function _createHeatmapLegend() {
  if (!container) return null;

  var legend = document.createElement("div");
  legend.className = "viewer3d-heatmap-legend";
  legend.innerHTML =
    '<div class="viewer3d-heatmap-legend__title">Тепловая карта</div>' +
    '<div class="viewer3d-heatmap-legend__gradient"></div>' +
    '<div class="viewer3d-heatmap-legend__labels">' +
    '<span class="viewer3d-heatmap-legend__label">Холодно</span>' +
    '<span class="viewer3d-heatmap-legend__label">Комфорт</span>' +
    '<span class="viewer3d-heatmap-legend__label">Тепло</span>' +
    '<span class="viewer3d-heatmap-legend__label">Горячо</span>' +
    '</div>' +
    '<div class="viewer3d-heatmap-legend__range">' +
    '<span id="heatmap-min-temp">-10°C</span>' +
    '<span id="heatmap-max-temp">+40°C</span>' +
    '</div>';

  container.appendChild(legend);
  return legend;
}

function _removeHeatmapLegend() {
  if (heatmapLegend && heatmapLegend.parentNode) {
    heatmapLegend.parentNode.removeChild(heatmapLegend);
  }
  heatmapLegend = null;
}

function _temperatureToGradient(celsius, minTemp, maxTemp) {
  if (celsius === null || !Number.isFinite(celsius)) return 0.5;
  var t = (celsius - minTemp) / (maxTemp - minTemp);
  return _clamp(t, 0, 1);
}

function _interpolateTemperatureAtVertex(vertex, dataPoints) {
  if (!dataPoints || !dataPoints.length) return 20; // Температура по умолчанию

  // Интерполяция по методу обратных расстояний (IDW)
  var weightedSum = 0;
  var weightSum = 0;
  var minDist = Infinity;
  var closestTemp = 20;

  for (var j = 0; j < dataPoints.length; j++) {
    var point = dataPoints[j];
    var distance = vertex.distanceTo(point.position);

    if (distance < 0.01) {
      // Очень близко к точке данных - используем точное значение
      return point.temperature;
    }

    var weight = 1 / Math.pow(distance, 2);
    weightedSum += point.temperature * weight;
    weightSum += weight;

    if (distance < minDist) {
      minDist = distance;
      closestTemp = point.temperature;
    }
  }

  if (weightSum > 0) {
    return weightedSum / weightSum;
  }

  return closestTemp;
}

function _applyHeatmapToMesh(mesh, dataPoints, minTemp, maxTemp, previousDataPoints, animProgress) {
  if (!mesh || !mesh.isMesh || !mesh.geometry) return;

  var geometry = mesh.geometry;
  var positions = geometry.getAttribute("position");
  if (!positions) return;

  // Создаём UV координаты для тепловой карты, если их нет
  var uvs = geometry.getAttribute("uv");
  if (!uvs) {
    var uvArray = new Float32Array(positions.count * 2);
    for (var i = 0; i < positions.count; i++) {
      uvArray[i * 2] = 0.5;
      uvArray[i * 2 + 1] = 0.5;
    }
    geometry.setAttribute("uv", new THREE.BufferAttribute(uvArray, 2));
    uvs = geometry.getAttribute("uv");
  }

  // Определяем, нужна ли анимация
  var useAnimation = previousDataPoints && previousDataPoints.length > 0 && animProgress < 1.0;

  // Для каждой вершины находим температуру с интерполяцией
  for (var i = 0; i < positions.count; i++) {
    var vx = positions.getX(i);
    var vy = positions.getY(i);
    var vz = positions.getZ(i);
    var vertex = new THREE.Vector3(vx, vy, vz);
    mesh.localToWorld(vertex);

    var currentTemp = _interpolateTemperatureAtVertex(vertex, dataPoints);

    // Если есть анимация, интерполируем между старой и новой температурой
    if (useAnimation) {
      var previousTemp = _interpolateTemperatureAtVertex(vertex, previousDataPoints);
      currentTemp = previousTemp + (currentTemp - previousTemp) * animProgress;
    }

    // Преобразуем температуру в UV координату для градиента
    var gradientT = _temperatureToGradient(currentTemp, minTemp, maxTemp);
    uvs.setX(i, gradientT);
    uvs.setY(i, 0.5);
  }

  uvs.needsUpdate = true;

  // Применяем градиентную текстуру
  if (!mesh.userData.originalMaterial) {
    mesh.userData.originalMaterial = mesh.material;
  }

  var heatmapTexture = _createHeatmapGradientTexture();
  var heatmapMaterial = new THREE.MeshBasicMaterial({
    map: heatmapTexture,
    transparent: true,
    opacity: 0.8,
    side: THREE.DoubleSide,
  });

  mesh.material = heatmapMaterial;
}

function _clearHeatmap() {
  if (!modelRoot) return;

  modelRoot.traverse(function (child) {
    if (child.isMesh && child.userData.originalMaterial) {
      child.material = child.userData.originalMaterial;
      child.userData.originalMaterial = null;
    }
  });

  _removeHeatmapLegend();

  // Сбрасываем данные анимации
  heatmapPreviousDataPoints = [];
  heatmapAnimationProgress = 1.0;
}

function _updateHeatmapAnimation() {
  if (!heatmapMode || !modelRoot) return;
  if (heatmapAnimationProgress >= 1.0) return;

  var now = performance.now();
  var elapsed = now - heatmapAnimationStartTime;
  heatmapAnimationProgress = Math.min(1.0, elapsed / heatmapAnimationDuration);

  // Применяем анимированную тепловую карту
  modelRoot.traverse(function (child) {
    if (child.isMesh) {
      var role = _classifyMeshContext(child);
      if (role.section && !ENCLOSURE_KINDS[role.kind]) {
        _applyHeatmapToMesh(
          child,
          heatmapDataPoints,
          heatmapMinTemp,
          heatmapMaxTemp,
          heatmapPreviousDataPoints,
          heatmapAnimationProgress
        );
      }
    }
  });
}

function setHeatmapMode(enabled, dataPoints, options) {
  heatmapMode = enabled === true;

  if (!heatmapMode) {
    _clearHeatmap();
    return true;
  }

  if (!dataPoints || !dataPoints.length) {
    console.warn("[Heatmap] No data points provided");
    return false;
  }

  var opts = options || {};
  var minTemp = opts.minTemp !== undefined ? opts.minTemp : -10;
  var maxTemp = opts.maxTemp !== undefined ? opts.maxTemp : 40;
  var animate = opts.animate !== undefined ? opts.animate : true;
  var animDuration = opts.animationDuration !== undefined ? opts.animationDuration : 1000;

  heatmapMinTemp = minTemp;
  heatmapMaxTemp = maxTemp;

  // Сохраняем предыдущие данные для анимации
  if (animate && heatmapDataPoints.length > 0) {
    heatmapPreviousDataPoints = heatmapDataPoints.slice();
    heatmapAnimationProgress = 0.0;
    heatmapAnimationStartTime = performance.now();
    heatmapAnimationDuration = animDuration;
  } else {
    heatmapPreviousDataPoints = [];
    heatmapAnimationProgress = 1.0;
  }

  // Преобразуем точки данных в формат с THREE.Vector3
  heatmapDataPoints = dataPoints.map(function (point) {
    return {
      position: new THREE.Vector3(point.x || 0, point.y || 0, point.z || 0),
      temperature: point.temperature || 20,
    };
  });

  // Создаём легенду
  if (!heatmapLegend) {
    heatmapLegend = _createHeatmapLegend();
  }

  // Обновляем диапазон температур в легенде
  var minLabel = document.getElementById("heatmap-min-temp");
  var maxLabel = document.getElementById("heatmap-max-temp");
  if (minLabel) minLabel.textContent = minTemp.toFixed(0) + "°C";
  if (maxLabel) maxLabel.textContent = maxTemp.toFixed(0) + "°C";

  // Применяем тепловую карту к модели
  if (modelRoot) {
    modelRoot.traverse(function (child) {
      if (child.isMesh) {
        var role = _classifyMeshContext(child);
        // Применяем только к основным секциям, не к корпусу
        if (role.section && !ENCLOSURE_KINDS[role.kind]) {
          _applyHeatmapToMesh(
            child,
            heatmapDataPoints,
            minTemp,
            maxTemp,
            heatmapPreviousDataPoints,
            heatmapAnimationProgress
          );
        }
      }
    });
  }

  return true;
}

function updateHeatmapData(dataPoints, options) {
  if (!heatmapMode) {
    console.warn("[Heatmap] Cannot update data when heatmap mode is disabled");
    return false;
  }

  if (!dataPoints || !dataPoints.length) {
    console.warn("[Heatmap] No data points provided");
    return false;
  }

  var opts = options || {};
  var minTemp = opts.minTemp !== undefined ? opts.minTemp : heatmapMinTemp;
  var maxTemp = opts.maxTemp !== undefined ? opts.maxTemp : heatmapMaxTemp;
  var animate = opts.animate !== undefined ? opts.animate : true;
  var animDuration = opts.animationDuration !== undefined ? opts.animationDuration : 1000;

  heatmapMinTemp = minTemp;
  heatmapMaxTemp = maxTemp;

  // Сохраняем предыдущие данные для анимации
  if (animate) {
    heatmapPreviousDataPoints = heatmapDataPoints.slice();
    heatmapAnimationProgress = 0.0;
    heatmapAnimationStartTime = performance.now();
    heatmapAnimationDuration = animDuration;
  } else {
    heatmapPreviousDataPoints = [];
    heatmapAnimationProgress = 1.0;
  }

  // Преобразуем точки данных в формат с THREE.Vector3
  heatmapDataPoints = dataPoints.map(function (point) {
    return {
      position: new THREE.Vector3(point.x || 0, point.y || 0, point.z || 0),
      temperature: point.temperature || 20,
    };
  });

  // Обновляем диапазон температур в легенде
  var minLabel = document.getElementById("heatmap-min-temp");
  var maxLabel = document.getElementById("heatmap-max-temp");
  if (minLabel) minLabel.textContent = minTemp.toFixed(0) + "°C";
  if (maxLabel) maxLabel.textContent = maxTemp.toFixed(0) + "°C";

  // Применяем обновлённую тепловую карту
  if (modelRoot) {
    modelRoot.traverse(function (child) {
      if (child.isMesh) {
        var role = _classifyMeshContext(child);
        if (role.section && !ENCLOSURE_KINDS[role.kind]) {
          _applyHeatmapToMesh(
            child,
            heatmapDataPoints,
            minTemp,
            maxTemp,
            heatmapPreviousDataPoints,
            heatmapAnimationProgress
          );
        }
      }
    });
  }

  return true;
}

function getHeatmapData() {
  return {
    enabled: heatmapMode,
    dataPoints: heatmapDataPoints.map(function (point) {
      return {
        x: point.position.x,
        y: point.position.y,
        z: point.position.z,
        temperature: point.temperature,
      };
    }),
  };
}

// ============================================================================
// Clipping Planes (Режим сечений)
// ============================================================================

/**
 * Включить/выключить режим сечений.
 * @param {boolean} enabled - включить режим
 * @param {Object} options - опции: planes (массив плоскостей)
 */
function setClippingMode(enabled, options) {
  if (!renderer) return false;

  clippingEnabled = enabled === true;
  renderer.localClippingEnabled = clippingEnabled;

  if (clippingEnabled && options && options.planes) {
    // Инициализировать плоскости из опций
    _clearClippingPlanes();
    for (var i = 0; i < options.planes.length && i < maxClippingPlanes; i++) {
      var planeData = options.planes[i];
      addClippingPlane(planeData);
    }
  } else if (!clippingEnabled) {
    // Выключить режим - скрыть helpers, но сохранить данные
    _updateClippingHelpersVisibility();
  }

  _updateMaterialsClipping();
  return true;
}

/**
 * Добавить новую плоскость сечения.
 * @param {Object} planeData - {normal: [x,y,z], constant: number, enabled: boolean, inverted: boolean}
 * @returns {number} индекс добавленной плоскости или -1
 */
function addClippingPlane(planeData) {
  if (clippingPlanes.length >= maxClippingPlanes) {
    console.warn("Maximum clipping planes reached:", maxClippingPlanes);
    return -1;
  }

  var normal = planeData.normal || [0, 1, 0];
  var constant = planeData.constant !== undefined ? planeData.constant : 0;
  var enabled = planeData.enabled !== false;
  var inverted = planeData.inverted === true;

  // Создать THREE.Plane
  var normalVec = new THREE.Vector3(normal[0], normal[1], normal[2]).normalize();
  if (inverted) {
    normalVec.negate();
  }
  var plane = new THREE.Plane(normalVec, constant);

  // Создать визуальный helper
  var helper = _createClippingPlaneHelper(plane, enabled);

  // Сохранить данные
  var index = clippingPlanes.length;
  clippingPlanes.push(plane);
  clippingHelpers.push(helper);
  clippingPlanesData.push({
    normal: [normal[0], normal[1], normal[2]],
    constant: constant,
    enabled: enabled,
    inverted: inverted,
  });

  if (scene && helper) {
    scene.add(helper);
  }

  _updateMaterialsClipping();
  return index;
}

/**
 * Обновить параметры плоскости сечения.
 * @param {number} index - индекс плоскости
 * @param {Object} params - {normal, constant, enabled, inverted}
 */
function updateClippingPlane(index, params) {
  if (index < 0 || index >= clippingPlanes.length) {
    console.warn("Invalid clipping plane index:", index);
    return false;
  }

  var plane = clippingPlanes[index];
  var data = clippingPlanesData[index];
  var helper = clippingHelpers[index];

  var needsUpdate = false;

  if (params.normal !== undefined) {
    data.normal = [params.normal[0], params.normal[1], params.normal[2]];
    needsUpdate = true;
  }

  if (params.constant !== undefined) {
    data.constant = params.constant;
    needsUpdate = true;
  }

  if (params.inverted !== undefined) {
    data.inverted = params.inverted === true;
    needsUpdate = true;
  }

  if (params.enabled !== undefined) {
    data.enabled = params.enabled !== false;
    if (helper) {
      helper.visible = data.enabled && clippingEnabled;
    }
  }

  if (needsUpdate) {
    // Пересоздать plane с новыми параметрами
    var normalVec = new THREE.Vector3(
      data.normal[0],
      data.normal[1],
      data.normal[2]
    ).normalize();

    if (data.inverted) {
      normalVec.negate();
    }

    plane.normal.copy(normalVec);
    plane.constant = data.constant;

    // Обновить helper
    if (helper) {
      _updateClippingPlaneHelper(helper, plane);
    }

    _updateMaterialsClipping();
  }

  return true;
}

/**
 * Удалить плоскость сечения.
 * @param {number} index - индекс плоскости
 */
function removeClippingPlane(index) {
  if (index < 0 || index >= clippingPlanes.length) {
    console.warn("Invalid clipping plane index:", index);
    return false;
  }

  var helper = clippingHelpers[index];
  if (helper && scene) {
    scene.remove(helper);
    if (helper.geometry) helper.geometry.dispose();
    if (helper.material) helper.material.dispose();
  }

  clippingPlanes.splice(index, 1);
  clippingHelpers.splice(index, 1);
  clippingPlanesData.splice(index, 1);

  _updateMaterialsClipping();
  return true;
}

/**
 * Получить данные всех плоскостей сечения.
 */
function getClippingPlanes() {
  return {
    enabled: clippingEnabled,
    planes: clippingPlanesData.map(function (data, index) {
      return {
        index: index,
        normal: data.normal.slice(),
        constant: data.constant,
        enabled: data.enabled,
        inverted: data.inverted,
      };
    }),
  };
}

/**
 * Очистить все плоскости сечения.
 */
function clearClippingPlanes() {
  _clearClippingPlanes();
  _updateMaterialsClipping();
  return true;
}

// ============================================================================
// LOD (Level of Detail) System
// ============================================================================

/**
 * Создать упрощённую версию геометрии.
 * @param {THREE.BufferGeometry} geometry - исходная геометрия
 * @param {number} ratio - коэффициент упрощения (0.0-1.0)
 * @returns {THREE.BufferGeometry} упрощённая геометрия
 */
function _simplifyGeometry(geometry, ratio) {
  if (!geometry || !geometry.isBufferGeometry) {
    return geometry;
  }

  // Для очень простой геометрии (< 100 вершин) не упрощаем
  var vertexCount = geometry.attributes.position ? geometry.attributes.position.count : 0;
  if (vertexCount < 100) {
    return geometry.clone();
  }

  var simplified = geometry.clone();

  // Простое упрощение: прореживание вершин
  // Для production можно использовать SimplifyModifier из three/examples
  if (ratio >= 0.9) {
    return simplified;
  }

  // Базовое упрощение через decimation
  var targetCount = Math.max(Math.floor(vertexCount * ratio), 12);
  var step = Math.max(1, Math.floor(vertexCount / targetCount));

  if (step > 1 && simplified.index) {
    var indices = simplified.index.array;
    var newIndices = [];

    for (var i = 0; i < indices.length; i += step * 3) {
      if (i + 2 < indices.length) {
        newIndices.push(indices[i], indices[i + 1], indices[i + 2]);
      }
    }

    simplified.setIndex(newIndices);
  }

  return simplified;
}

/**
 * Создать LOD-версии для mesh.
 * @param {THREE.Mesh} mesh - исходный mesh
 * @returns {THREE.LOD|null} LOD объект или null
 */
function _createLODForMesh(mesh) {
  if (!mesh || !mesh.isMesh || !mesh.geometry) {
    return null;
  }

  // Не создаём LOD для очень простых объектов
  var vertexCount = mesh.geometry.attributes.position ? mesh.geometry.attributes.position.count : 0;
  if (vertexCount < 100) {
    return null;
  }

  var lod = new THREE.LOD();
  lod.name = mesh.name + "_LOD";
  lod.position.copy(mesh.position);
  lod.rotation.copy(mesh.rotation);
  lod.scale.copy(mesh.scale);
  lod.userData = Object.assign({}, mesh.userData);

  // Level 0: High detail (оригинал)
  var highDetail = mesh.clone();
  lod.addLevel(highDetail, lodDistances[0]);

  // Level 1: Medium detail (60% вершин)
  var mediumGeometry = _simplifyGeometry(mesh.geometry, 0.6);
  var mediumDetail = new THREE.Mesh(mediumGeometry, mesh.material);
  mediumDetail.name = mesh.name + "_medium";
  mediumDetail.userData = Object.assign({}, mesh.userData);
  lod.addLevel(mediumDetail, lodDistances[1]);

  // Level 2: Low detail (30% вершин)
  var lowGeometry = _simplifyGeometry(mesh.geometry, 0.3);
  var lowDetail = new THREE.Mesh(lowGeometry, mesh.material);
  lowDetail.name = mesh.name + "_low";
  lowDetail.userData = Object.assign({}, mesh.userData);
  lod.addLevel(lowDetail, lodDistances[2]);

  return lod;
}

/**
 * Конвертировать модель в LOD-версию.
 * @param {THREE.Object3D} root - корень модели
 */
function _convertModelToLOD(root) {
  if (!root) return;

  var meshesToConvert = [];

  root.traverse(function (child) {
    if (child.isMesh && child.geometry) {
      var vertexCount = child.geometry.attributes.position ? child.geometry.attributes.position.count : 0;
      if (vertexCount >= 100) {
        meshesToConvert.push(child);
      }
    }
  });

  meshesToConvert.forEach(function (mesh) {
    var lodObject = _createLODForMesh(mesh);
    if (lodObject) {
      var parent = mesh.parent;
      if (parent) {
        var index = parent.children.indexOf(mesh);
        parent.remove(mesh);
        parent.children.splice(index, 0, lodObject);
        lodObject.parent = parent;
        lodObjects.push(lodObject);
      }
    }
  });
}

/**
 * Удалить все LOD объекты из модели.
 * @param {THREE.Object3D} root - корень модели
 */
function _removeLODFromModel(root) {
  if (!root) return;

  var lodsToRemove = [];

  root.traverse(function (child) {
    if (child.isLOD) {
      lodsToRemove.push(child);
    }
  });

  lodsToRemove.forEach(function (lod) {
    var parent = lod.parent;
    if (parent && lod.levels.length > 0) {
      // Восстановить оригинальный mesh (level 0)
      var originalMesh = lod.levels[0].object.clone();
      originalMesh.position.copy(lod.position);
      originalMesh.rotation.copy(lod.rotation);
      originalMesh.scale.copy(lod.scale);

      var index = parent.children.indexOf(lod);
      parent.remove(lod);
      parent.children.splice(index, 0, originalMesh);
      originalMesh.parent = parent;

      // Очистка
      lod.levels.forEach(function (level) {
        if (level.object.geometry) {
          level.object.geometry.dispose();
        }
      });
    }
  });

  lodObjects = [];
}

/**
 * Обновить LOD объекты (вызывается в render loop).
 */
function _updateLOD() {
  if (!lodEnabled || !camera || lodObjects.length === 0) {
    return;
  }

  lodStats = { high: 0, medium: 0, low: 0 };

  lodObjects.forEach(function (lod) {
    lod.update(camera);

    // Статистика текущего уровня
    var currentLevel = lod.getCurrentLevel();
    if (currentLevel === 0) {
      lodStats.high++;
    } else if (currentLevel === 1) {
      lodStats.medium++;
    } else {
      lodStats.low++;
    }
  });
}

/**
 * Включить/выключить LOD режим.
 * @param {boolean} enabled - включить LOD
 * @param {object} options - параметры: {distances: [0, 15, 30], quality: "auto"}
 */
function setLODMode(enabled, options) {
  if (!modelRoot) {
    console.warn("No model loaded");
    return false;
  }

  options = options || {};

  // Обновить параметры
  if (options.distances && Array.isArray(options.distances) && options.distances.length === 3) {
    lodDistances = options.distances.slice();
  }

  if (options.quality) {
    lodQuality = options.quality;
  }

  var wasEnabled = lodEnabled;
  lodEnabled = enabled === true;

  if (lodEnabled && !wasEnabled) {
    // Включаем LOD
    _convertModelToLOD(modelRoot);
    console.log("[LOD] Enabled:", lodObjects.length, "objects converted");
  } else if (!lodEnabled && wasEnabled) {
    // Выключаем LOD
    _removeLODFromModel(modelRoot);
    console.log("[LOD] Disabled");
  } else if (lodEnabled && wasEnabled) {
    // Обновляем параметры существующих LOD
    lodObjects.forEach(function (lod) {
      if (lod.levels.length >= 3) {
        lod.levels[0].distance = lodDistances[0];
        lod.levels[1].distance = lodDistances[1];
        lod.levels[2].distance = lodDistances[2];
      }
    });
  }

  return true;
}

/**
 * Получить статистику LOD.
 */
function getLODStats() {
  return {
    enabled: lodEnabled,
    totalObjects: lodObjects.length,
    distances: lodDistances.slice(),
    quality: lodQuality,
    currentLevels: Object.assign({}, lodStats),
  };
}

/**
 * Применить пресет LOD.
 * @param {string} preset - "performance", "balanced", "quality", "off"
 */
function applyLODPreset(preset) {
  var presets = {
    performance: { enabled: true, distances: [0, 10, 20], quality: "low" },
    balanced: { enabled: true, distances: [0, 15, 30], quality: "medium" },
    quality: { enabled: true, distances: [0, 25, 50], quality: "high" },
    off: { enabled: false, distances: [0, 15, 30], quality: "auto" },
  };

  var config = presets[preset];
  if (!config) {
    console.warn("Unknown LOD preset:", preset);
    return false;
  }

  return setLODMode(config.enabled, {
    distances: config.distances,
    quality: config.quality,
  });
}

// ============================================================================
// Flow Field (Airflow Visualization)
// ============================================================================

/**
 * Загрузить данные векторного поля из JSON файла.
 * @param {string} url - URL файла с данными векторного поля
 * @returns {Promise<boolean>} - true если загрузка успешна
 */
function loadFlowFieldData(url) {
  return fetch(url)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to load flow field: ${response.statusText}`);
      }
      return response.json();
    })
    .then((data) => {
      // Validate data structure
      if (!data.points || !Array.isArray(data.points)) {
        throw new Error("Invalid flow field data: missing points array");
      }

      flowFieldData = data;
      console.log(
        `Flow field loaded: ${data.points.length} vectors, bounds:`,
        data.metadata?.bounds
      );

      // If flow field is enabled, recreate visualization with new data
      if (flowFieldEnabled) {
        _clearFlowField();
        _createFlowFieldVisualization();
      }

      return true;
    })
    .catch((error) => {
      console.error("Error loading flow field:", error);
      flowFieldData = null;
      return false;
    });
}

/**
 * Очистить все объекты векторного поля из сцены.
 */
function _clearFlowField() {
  flowFieldObjects.forEach((obj) => {
    if (obj.parent) {
      obj.parent.remove(obj);
    }
    if (obj.geometry) obj.geometry.dispose();
    if (obj.material) {
      if (Array.isArray(obj.material)) {
        obj.material.forEach((m) => m.dispose());
      } else {
        obj.material.dispose();
      }
    }
  });
  flowFieldObjects = [];

  if (flowFieldParticles) {
    if (flowFieldParticles.parent) {
      flowFieldParticles.parent.remove(flowFieldParticles);
    }
    if (flowFieldParticles.geometry) flowFieldParticles.geometry.dispose();
    if (flowFieldParticles.material) flowFieldParticles.material.dispose();
    flowFieldParticles = null;
  }
}

/**
 * Создать визуализацию векторного поля в текущем режиме.
 */
function _createFlowFieldVisualization() {
  if (!flowFieldData || !flowFieldData.points) {
    console.warn("No flow field data loaded");
    return;
  }

  _clearFlowField();

  switch (flowFieldMode) {
    case "arrows":
      _createArrowField();
      break;
    case "streamlines":
      _createStreamlines();
      break;
    case "particles":
      _createParticleField();
      break;
    default:
      console.warn("Unknown flow field mode:", flowFieldMode);
  }
}

/**
 * Создать поле стрелок для визуализации векторов.
 */
function _createArrowField() {
  if (!flowFieldData || !scene) return;

  const points = flowFieldData.points;
  const densityFactor = flowFieldDensity;
  const step = Math.max(1, Math.floor(1 / densityFactor));

  // Find min/max speed for color mapping
  let minSpeed = Infinity;
  let maxSpeed = -Infinity;
  points.forEach((p) => {
    if (p.speed < minSpeed) minSpeed = p.speed;
    if (p.speed > maxSpeed) maxSpeed = p.speed;
  });

  const speedRange = maxSpeed - minSpeed || 1;

  // Create arrows with instanced rendering for performance
  for (let i = 0; i < points.length; i += step) {
    const point = points[i];
    const pos = new THREE.Vector3(point.pos[0], point.pos[1], point.pos[2]);
    const vel = new THREE.Vector3(point.vel[0], point.vel[1], point.vel[2]);
    const speed = point.speed;

    // Skip zero-velocity vectors
    if (speed < 0.01) continue;

    // Normalize velocity for direction
    const dir = vel.clone().normalize();

    // Arrow length based on speed (scaled for visibility)
    const length = Math.max(0.1, speed * 0.3);

    // Color based on speed (blue -> cyan -> green -> yellow -> red)
    let color;
    if (flowFieldColorScheme === "speed") {
      const t = (speed - minSpeed) / speedRange;
      color = new THREE.Color();
      if (t < 0.25) {
        // Blue to cyan
        color.setRGB(0, t * 4, 1);
      } else if (t < 0.5) {
        // Cyan to green
        const t2 = (t - 0.25) * 4;
        color.setRGB(0, 1, 1 - t2);
      } else if (t < 0.75) {
        // Green to yellow
        const t2 = (t - 0.5) * 4;
        color.setRGB(t2, 1, 0);
      } else {
        // Yellow to red
        const t2 = (t - 0.75) * 4;
        color.setRGB(1, 1 - t2, 0);
      }
    } else if (flowFieldColorScheme === "direction") {
      // Color based on direction (X=red, Y=green, Z=blue)
      const absDir = new THREE.Vector3(
        Math.abs(dir.x),
        Math.abs(dir.y),
        Math.abs(dir.z)
      );
      color = new THREE.Color(absDir.x, absDir.y, absDir.z);
    } else {
      // Default: cyan
      color = new THREE.Color(0x00ffff);
    }

    // Create arrow
    const arrow = new THREE.ArrowHelper(
      dir,
      pos,
      length,
      color.getHex(),
      length * 0.2,
      length * 0.15
    );

    scene.add(arrow);
    flowFieldObjects.push(arrow);
  }

  console.log(`Created ${flowFieldObjects.length} arrows`);
}

/**
 * Создать линии тока (streamlines) для визуализации потока.
 */
function _createStreamlines() {
  if (!flowFieldData || !scene) return;

  const points = flowFieldData.points;
  const numLines = Math.floor(20 * flowFieldDensity);

  // Find bounds for seeding streamlines
  const bounds = flowFieldData.metadata?.bounds || {
    min: [-3, -2, -1],
    max: [3, 2, 1],
  };

  // Create streamlines by integrating the vector field
  for (let i = 0; i < numLines; i++) {
    // Random seed point within bounds
    const seedX =
      bounds.min[0] + Math.random() * (bounds.max[0] - bounds.min[0]);
    const seedY =
      bounds.min[1] + Math.random() * (bounds.max[1] - bounds.min[1]);
    const seedZ =
      bounds.min[2] + Math.random() * (bounds.max[2] - bounds.min[2]);

    const linePoints = [];
    let currentPos = new THREE.Vector3(seedX, seedY, seedZ);

    // Integrate forward
    const maxSteps = 100;
    const stepSize = 0.1;

    for (let step = 0; step < maxSteps; step++) {
      linePoints.push(currentPos.clone());

      // Interpolate velocity at current position
      const vel = _interpolateVelocity(currentPos);
      if (!vel || vel.length() < 0.01) break;

      // Move to next position
      currentPos.add(vel.multiplyScalar(stepSize));

      // Check bounds
      if (
        currentPos.x < bounds.min[0] ||
        currentPos.x > bounds.max[0] ||
        currentPos.y < bounds.min[1] ||
        currentPos.y > bounds.max[1] ||
        currentPos.z < bounds.min[2] ||
        currentPos.z > bounds.max[2]
      ) {
        break;
      }
    }

    if (linePoints.length < 2) continue;

    // Create line geometry
    const geometry = new THREE.BufferGeometry().setFromPoints(linePoints);
    const material = new THREE.LineBasicMaterial({
      color: 0x00ffff,
      opacity: 0.6,
      transparent: true,
    });
    const line = new THREE.Line(geometry, material);

    scene.add(line);
    flowFieldObjects.push(line);
  }

  console.log(`Created ${flowFieldObjects.length} streamlines`);
}

/**
 * Создать систему частиц для визуализации потока.
 */
function _createParticleField() {
  if (!flowFieldData || !scene) return;

  const numParticles = Math.floor(1000 * flowFieldDensity);
  const bounds = flowFieldData.metadata?.bounds || {
    min: [-3, -2, -1],
    max: [3, 2, 1],
  };

  // Create particle geometry
  const positions = new Float32Array(numParticles * 3);
  const velocities = new Float32Array(numParticles * 3);
  const colors = new Float32Array(numParticles * 3);
  const sizes = new Float32Array(numParticles);

  // Initialize particles
  for (let i = 0; i < numParticles; i++) {
    const i3 = i * 3;

    // Random position within bounds
    positions[i3] =
      bounds.min[0] + Math.random() * (bounds.max[0] - bounds.min[0]);
    positions[i3 + 1] =
      bounds.min[1] + Math.random() * (bounds.max[1] - bounds.min[1]);
    positions[i3 + 2] =
      bounds.min[2] + Math.random() * (bounds.max[2] - bounds.min[2]);

    // Get velocity at this position
    const pos = new THREE.Vector3(
      positions[i3],
      positions[i3 + 1],
      positions[i3 + 2]
    );
    const vel = _interpolateVelocity(pos);

    if (vel) {
      velocities[i3] = vel.x;
      velocities[i3 + 1] = vel.y;
      velocities[i3 + 2] = vel.z;
    }

    // Color: cyan
    colors[i3] = 0;
    colors[i3 + 1] = 1;
    colors[i3 + 2] = 1;

    // Size
    sizes[i] = 0.05;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("velocity", new THREE.BufferAttribute(velocities, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute("size", new THREE.BufferAttribute(sizes, 1));

  const material = new THREE.PointsMaterial({
    size: 0.05,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    sizeAttenuation: true,
  });

  flowFieldParticles = new THREE.Points(geometry, material);
  scene.add(flowFieldParticles);

  console.log(`Created ${numParticles} particles`);
}

/**
 * Интерполировать скорость в произвольной точке пространства.
 * Использует ближайший сосед (можно улучшить до trilinear interpolation).
 * @param {THREE.Vector3} position - позиция для интерполяции
 * @returns {THREE.Vector3|null} - вектор скорости или null
 */
function _interpolateVelocity(position) {
  if (!flowFieldData || !flowFieldData.points) return null;

  const points = flowFieldData.points;

  // Find nearest point (simple nearest neighbor)
  let nearestDist = Infinity;
  let nearestPoint = null;

  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    const dx = position.x - p.pos[0];
    const dy = position.y - p.pos[1];
    const dz = position.z - p.pos[2];
    const dist = dx * dx + dy * dy + dz * dz;

    if (dist < nearestDist) {
      nearestDist = dist;
      nearestPoint = p;
    }
  }

  if (!nearestPoint) return null;

  return new THREE.Vector3(
    nearestPoint.vel[0],
    nearestPoint.vel[1],
    nearestPoint.vel[2]
  );
}

/**
 * Обновить анимацию векторного поля (вызывается каждый кадр).
 * @param {number} deltaTime - время с предыдущего кадра в секундах
 */
function _updateFlowFieldAnimation(deltaTime) {
  if (!flowFieldEnabled || !flowFieldData) return;

  flowFieldAnimationTime += deltaTime * flowFieldAnimationSpeed;

  // Update particles
  if (flowFieldMode === "particles" && flowFieldParticles) {
    const positions = flowFieldParticles.geometry.attributes.position.array;
    const velocities = flowFieldParticles.geometry.attributes.velocity.array;
    const bounds = flowFieldData.metadata?.bounds || {
      min: [-3, -2, -1],
      max: [3, 2, 1],
    };

    const numParticles = positions.length / 3;

    for (let i = 0; i < numParticles; i++) {
      const i3 = i * 3;

      // Update position based on velocity
      positions[i3] += velocities[i3] * deltaTime * flowFieldAnimationSpeed;
      positions[i3 + 1] +=
        velocities[i3 + 1] * deltaTime * flowFieldAnimationSpeed;
      positions[i3 + 2] +=
        velocities[i3 + 2] * deltaTime * flowFieldAnimationSpeed;

      // Wrap around or regenerate if out of bounds
      if (
        positions[i3] < bounds.min[0] ||
        positions[i3] > bounds.max[0] ||
        positions[i3 + 1] < bounds.min[1] ||
        positions[i3 + 1] > bounds.max[1] ||
        positions[i3 + 2] < bounds.min[2] ||
        positions[i3 + 2] > bounds.max[2]
      ) {
        // Regenerate at random position
        positions[i3] =
          bounds.min[0] + Math.random() * (bounds.max[0] - bounds.min[0]);
        positions[i3 + 1] =
          bounds.min[1] + Math.random() * (bounds.max[1] - bounds.min[1]);
        positions[i3 + 2] =
          bounds.min[2] + Math.random() * (bounds.max[2] - bounds.min[2]);

        // Update velocity
        const pos = new THREE.Vector3(
          positions[i3],
          positions[i3 + 1],
          positions[i3 + 2]
        );
        const vel = _interpolateVelocity(pos);
        if (vel) {
          velocities[i3] = vel.x;
          velocities[i3 + 1] = vel.y;
          velocities[i3 + 2] = vel.z;
        }
      }
    }

    flowFieldParticles.geometry.attributes.position.needsUpdate = true;
  }
}

/**
 * Включить/выключить визуализацию векторного поля.
 * @param {string} mode - режим: "off", "arrows", "streamlines", "particles"
 * @param {Object} options - опции: {density, animationSpeed, colorScheme}
 * @returns {boolean} - true если успешно
 */
function setFlowFieldMode(mode, options = {}) {
  if (mode === "off") {
    flowFieldEnabled = false;
    _clearFlowField();
    return true;
  }

  if (!["arrows", "streamlines", "particles"].includes(mode)) {
    console.warn("Invalid flow field mode:", mode);
    return false;
  }

  flowFieldEnabled = true;
  flowFieldMode = mode;

  if (options.density !== undefined) {
    flowFieldDensity = Math.max(0, Math.min(1, options.density));
  }
  if (options.animationSpeed !== undefined) {
    flowFieldAnimationSpeed = Math.max(0.1, Math.min(5, options.animationSpeed));
  }
  if (options.colorScheme !== undefined) {
    flowFieldColorScheme = options.colorScheme;
  }

  _createFlowFieldVisualization();
  return true;
}

/**
 * Получить статистику векторного поля.
 * @returns {Object} - статистика
 */
function getFlowFieldStats() {
  return {
    enabled: flowFieldEnabled,
    mode: flowFieldMode,
    dataLoaded: flowFieldData !== null,
    vectorCount: flowFieldData ? flowFieldData.points.length : 0,
    visibleObjects: flowFieldObjects.length,
    particleCount:
      flowFieldParticles && flowFieldParticles.geometry
        ? flowFieldParticles.geometry.attributes.position.count
        : 0,
    density: flowFieldDensity,
    animationSpeed: flowFieldAnimationSpeed,
    colorScheme: flowFieldColorScheme,
  };
}

// ============================================================================
// COMPARISON MODE (SIDE-BY-SIDE)
// ============================================================================

/**
 * Загрузить данные сравнения из API.
 * @param {string} beforeRefId - Reference ID для состояния "до"
 * @param {string} afterRefId - Reference ID для состояния "после"
 * @returns {Promise<object>} - Данные сравнения
 */
async function loadComparisonData(beforeRefId, afterRefId) {
  try {
    const response = await fetch("/api/comparison/runs/build", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        before_reference_id: beforeRefId,
        after_reference_id: afterRefId,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to load comparison data: " + response.statusText);
    }

    const comparison = await response.json();

    // Store comparison data
    comparisonBeforeRefId = beforeRefId;
    comparisonAfterRefId = afterRefId;
    comparisonBeforeData = comparison.before_source;
    comparisonAfterData = comparison.after_source;
    comparisonCompatibility = comparison.compatibility;

    console.log("[PVU3D] Comparison data loaded:", {
      before: comparison.before_source.display_label,
      after: comparison.after_source.display_label,
      compatible: comparison.compatibility.is_compatible,
    });

    return comparison;
  } catch (error) {
    console.error("[PVU3D] Failed to load comparison data:", error);
    throw error;
  }
}

/**
 * Включить/выключить режим сравнения.
 * @param {string} mode - "off" | "split"
 * @param {object} options - Опции: {split, orientation, syncCameras, diffMode}
 */
function setComparisonMode(mode, options = {}) {
  if (mode === "off") {
    if (comparisonMode) {
      comparisonMode = false;
      // Dispose comparison scene
      _disposeComparisonSceneAfter();
      // Restore full viewport
      if (renderer && camera) {
        renderer.setViewport(0, 0, renderer.domElement.width, renderer.domElement.height);
        renderer.setScissor(0, 0, renderer.domElement.width, renderer.domElement.height);
        renderer.setScissorTest(false);
        camera.aspect = renderer.domElement.width / renderer.domElement.height;
        camera.updateProjectionMatrix();
      }

      // Remove visual elements
      _updateComparisonLabels(); // This will remove labels
      const divider = document.getElementById('pvu3d-comparison-divider');
      if (divider) divider.remove();

      console.log("[PVU3D] Comparison mode disabled");
    }
    return;
  }

  if (mode === "split") {
    if (!comparisonBeforeData || !comparisonAfterData) {
      console.warn("[PVU3D] Cannot enable comparison mode: data not loaded");
      return;
    }

    if (!comparisonCompatibility || !comparisonCompatibility.is_compatible) {
      console.warn("[PVU3D] Cannot enable comparison mode: sources are incompatible");
      return;
    }

    comparisonMode = true;
    comparisonSplit = options.split !== undefined ? options.split : 0.5;
    comparisonOrientation = options.orientation || "vertical";
    comparisonSyncCameras = options.syncCameras !== undefined ? options.syncCameras : true;
    comparisonDiffMode = options.diffMode || "status";

    console.log("[PVU3D] Comparison mode enabled:", {
      split: comparisonSplit,
      orientation: comparisonOrientation,
      syncCameras: comparisonSyncCameras,
      diffMode: comparisonDiffMode,
    });

    // Create and load comparison scene
    _createComparisonSceneAfter();
    _loadComparisonModelAfter().then(function () {
      // Apply signals to both scenes
      if (comparisonBeforeData && comparisonBeforeData.simulation_result) {
        _applyComparisonSignals(comparisonBeforeData.simulation_result, "before");
      }
      if (comparisonAfterData && comparisonAfterData.simulation_result) {
        _applyComparisonSignals(comparisonAfterData.simulation_result, "after");
      }

      // Apply difference highlighting if diff mode is enabled
      if (comparisonDiffMode && comparisonDiffMode !== "none") {
        _highlightDifferences();
      }

      // Update viewport and labels
      _updateComparisonViewport();
      _updateComparisonLabels();
    }).catch(function (error) {
      console.error("[PVU3D] Failed to load comparison model:", error);
      comparisonMode = false;
    });
  }
}

/**
 * Обновить viewport для split-screen режима.
 * @private
 */
function _updateComparisonViewport() {
  if (!renderer || !camera || !comparisonMode) return;

  const width = renderer.domElement.width;
  const height = renderer.domElement.height;

  if (comparisonOrientation === "vertical") {
    // Vertical split (left/right)
    const leftWidth = Math.floor(width * comparisonSplit);
    const rightWidth = width - leftWidth;

    // Left viewport will be rendered first
    // Right viewport will be rendered second
    // We'll handle this in the render loop

    // For now, just update camera aspect for the left side
    camera.aspect = leftWidth / height;
    camera.updateProjectionMatrix();
  } else {
    // Horizontal split (top/bottom)
    const topHeight = Math.floor(height * comparisonSplit);
    const bottomHeight = height - topHeight;

    camera.aspect = width / topHeight;
    camera.updateProjectionMatrix();
  }

  // Update labels position
  _updateComparisonLabels();
}

/**
 * Получить статистику режима сравнения.
 * @returns {object} - Статистика
 */
function getComparisonStats() {
  return {
    enabled: comparisonMode,
    split: comparisonSplit,
    orientation: comparisonOrientation,
    syncCameras: comparisonSyncCameras,
    diffMode: comparisonDiffMode,
    beforeRefId: comparisonBeforeRefId,
    afterRefId: comparisonAfterRefId,
    beforeLabel: comparisonBeforeData ? comparisonBeforeData.display_label : null,
    afterLabel: comparisonAfterData ? comparisonAfterData.display_label : null,
    compatibility: comparisonCompatibility,
    dataLoaded: comparisonBeforeData !== null && comparisonAfterData !== null,
  };
}

/**
 * Создать вторую сцену для режима сравнения.
 * @private
 */
function _createComparisonSceneAfter() {
  if (comparisonSceneAfter) {
    _disposeComparisonSceneAfter();
  }

  // Create second scene with same structure as main scene
  comparisonSceneAfter = new THREE.Scene();
  comparisonEnvironmentRootAfter = new THREE.Group();
  comparisonOverlayRootAfter = new THREE.Group();
  comparisonEnvironmentRootAfter.name = "comparison-environment-after";
  comparisonOverlayRootAfter.name = "comparison-overlay-after";
  comparisonSceneAfter.add(comparisonEnvironmentRootAfter);
  comparisonSceneAfter.add(comparisonOverlayRootAfter);

  // Add lights (same as main scene)
  const ambientLightAfter = new THREE.AmbientLight(0xe6f3ff, 0.9);
  const keyLightAfter = new THREE.DirectionalLight(0xffffff, 2.0);
  const rimLightAfter = new THREE.DirectionalLight(0x7dd3fc, 0.9);
  const fillLightAfter = new THREE.DirectionalLight(0xfef3c7, 0.55);
  keyLightAfter.position.set(6, 10, 8);
  rimLightAfter.position.set(-8, 7, -10);
  fillLightAfter.position.set(0, 4, 10);
  if (shadowsEnabled) {
    keyLightAfter.castShadow = true;
    keyLightAfter.shadow.mapSize.set(2048, 2048);
    keyLightAfter.shadow.bias = -0.0005;
    keyLightAfter.shadow.normalBias = 0.02;
    keyLightAfter.shadow.radius = 4;
    const keyShadowCamAfter = keyLightAfter.shadow.camera;
    keyShadowCamAfter.near = 0.5;
    keyShadowCamAfter.far = 60;
    keyShadowCamAfter.left = -14;
    keyShadowCamAfter.right = 14;
    keyShadowCamAfter.top = 14;
    keyShadowCamAfter.bottom = -14;
    keyShadowCamAfter.updateProjectionMatrix();

    const shadowCatcherAfter = new THREE.Mesh(
      new THREE.PlaneGeometry(40, 40),
      new THREE.ShadowMaterial({ opacity: 0.32 })
    );
    shadowCatcherAfter.rotation.x = -Math.PI / 2;
    shadowCatcherAfter.receiveShadow = true;
    comparisonEnvironmentRootAfter.add(shadowCatcherAfter);
  }
  comparisonSceneAfter.add(ambientLightAfter);
  comparisonSceneAfter.add(keyLightAfter);
  comparisonSceneAfter.add(rimLightAfter);
  comparisonSceneAfter.add(fillLightAfter);

  // Reuse the same procedural IBL environment as the main scene.
  _applyEnvironmentLighting(comparisonSceneAfter);

  // Create camera for "after" scene (used when cameras are not synced)
  if (!comparisonCameraAfter && camera) {
    comparisonCameraAfter = camera.clone();
    comparisonCameraAfter.position.copy(camera.position);
    comparisonCameraAfter.rotation.copy(camera.rotation);
  }

  console.log("[PVU3D] Comparison scene 'after' created");
}

/**
 * Обновить режим выделения различий.
 * @param {string} mode - Новый режим: "status" | "temperature" | "power" | "alarms" | "none"
 */
function updateComparisonDiffMode(mode) {
  if (!comparisonMode) {
    console.warn("[PVU3D] Cannot update diff mode: comparison mode is not active");
    return;
  }

  comparisonDiffMode = mode;

  // Re-apply signals to clear previous highlighting
  if (comparisonAfterData && comparisonAfterData.simulation_result) {
    _applyComparisonSignals(comparisonAfterData.simulation_result, "after");
  }

  // Apply new highlighting if mode is not "none"
  if (mode && mode !== "none") {
    _highlightDifferences();
  }

  console.log("[PVU3D] Comparison diff mode updated to:", mode);
}

/**
 * Удалить вторую сцену для режима сравнения.
 * @private
 */
function _disposeComparisonSceneAfter() {
  if (comparisonModelRootAfter) {
    _disposeObject(comparisonModelRootAfter);
    comparisonModelRootAfter = null;
  }
  if (comparisonSceneAfter) {
    _disposeObject(comparisonSceneAfter);
    comparisonSceneAfter = null;
  }
  comparisonEnvironmentRootAfter = null;
  comparisonOverlayRootAfter = null;
  comparisonNodeMapAfter = {};
  comparisonBindingMapAfter = {};
  comparisonInteractiveObjectsAfter = [];
  comparisonCameraAfter = null;
  console.log("[PVU3D] Comparison scene 'after' disposed");
}

/**
 * Загрузить модель для "after" сцены.
 * @private
 */
async function _loadComparisonModelAfter() {
  if (!comparisonAfterData || !currentModelDescriptor) {
    console.warn("[PVU3D] Cannot load comparison model: missing data or descriptor");
    return;
  }

  // Ensure comparison scene exists
  if (!comparisonSceneAfter) {
    _createComparisonSceneAfter();
  }

  // Clone the current model for the "after" scene
  // We reuse the cached model entry to avoid loading the same GLB twice
  const modelKey = _descriptorKey(currentModelDescriptor, currentModelDescriptor.model_url);
  const entry = cachedModelEntries[modelKey];

  if (!entry || !entry.root) {
    console.warn("[PVU3D] Cannot load comparison model: model not cached");
    return;
  }

  // Clone the model root
  comparisonModelRootAfter = entry.root.clone(true);
  comparisonModelRootAfter.name = "comparison-model-after";
  comparisonSceneAfter.add(comparisonModelRootAfter);

  // Build node map for "after" scene
  comparisonNodeMapAfter = {};
  comparisonModelRootAfter.traverse(function (node) {
    if (node.name) {
      const normalizedName = _normalizeSceneNodeId(node.name);
      comparisonNodeMapAfter[node.name] = node;
      comparisonNodeMapAfter[normalizedName] = node;
    }
  });

  // Copy binding map
  comparisonBindingMapAfter = { ...bindingMap };

  console.log("[PVU3D] Comparison model 'after' loaded:", {
    nodes: Object.keys(comparisonNodeMapAfter).length / 2,
  });
}

/**
 * Применить signals к "before" или "after" сцене.
 * @param {object} signals - Simulation signals
 * @param {string} side - "before" | "after"
 * @private
 */
function _applyComparisonSignals(signals, side) {
  if (!signals) return;

  const targetNodeMap = side === "after" ? comparisonNodeMapAfter : nodeMap;
  const targetBindingMap = side === "after" ? comparisonBindingMapAfter : bindingMap;

  if (Object.keys(targetNodeMap).length === 0) {
    console.warn("[PVU3D] Cannot apply signals to", side, "scene: node map is empty");
    return;
  }

  const statusColors = sceneMeta.status_colors || STATUS_COLORS;

  ["nodes", "sensors", "flows", "room_sensors"].forEach(function (section) {
    const items = signals[section] || {};
    Object.keys(items).forEach(function (visualId) {
      const signal = items[visualId];
      const binding = targetBindingMap[visualId];
      if (!binding) return;

      const node = targetNodeMap[binding.scene_node] || targetNodeMap[_normalizeSceneNodeId(binding.scene_node)];
      if (!node) return;

      const colorHex = _statusToColor(signal.state, statusColors);
      _applyNodeSignal(node, signal, binding.kind, colorHex);
    });
  });

  console.log("[PVU3D] Signals applied to", side, "scene");
}

/**
 * Синхронизировать камеру "after" с основной камерой.
 * Копирует position, rotation, zoom и target из основной камеры.
 * @private
 */
function _syncCameras() {
  if (!comparisonCameraAfter || !camera || !controls) return;

  // Copy camera position and rotation
  comparisonCameraAfter.position.copy(camera.position);
  comparisonCameraAfter.rotation.copy(camera.rotation);
  comparisonCameraAfter.quaternion.copy(camera.quaternion);

  // Copy camera properties
  comparisonCameraAfter.zoom = camera.zoom;
  comparisonCameraAfter.fov = camera.fov;
  comparisonCameraAfter.near = camera.near;
  comparisonCameraAfter.far = camera.far;

  // Note: aspect ratio is set per-viewport in _renderSplitScreen()
  // so we don't copy it here to avoid conflicts
}

/**
 * Применить цветовое выделение различий.
 * Сравнивает метрики между "before" и "after" состояниями
 * и применяет цветовое кодирование на основе дельт.
 * @private
 */
function _highlightDifferences() {
  if (!comparisonMode || !comparisonBeforeData || !comparisonAfterData) {
    console.warn("[PVU3D] Cannot highlight differences: missing data");
    return;
  }

  const beforeSignals = comparisonBeforeData.simulation_result;
  const afterSignals = comparisonAfterData.simulation_result;

  if (!beforeSignals || !afterSignals) {
    console.warn("[PVU3D] Cannot highlight differences: missing simulation results");
    return;
  }

  // Color palette for difference highlighting
  const DIFF_COLORS = {
    improved: 0x10b981,    // Green - metric improved
    worsened: 0xef4444,    // Red - metric worsened
    unchanged: 0x6b7280,   // Gray - no significant change
    new: 0x3b82f6,         // Blue - new element
    removed: 0x8b5cf6,     // Purple - removed element
  };

  const DIFF_THRESHOLD = 0.05; // 5% change threshold

  console.log("[PVU3D] Highlighting differences, mode:", comparisonDiffMode);

  // Process each section
  ["nodes", "sensors", "flows", "room_sensors"].forEach(function (section) {
    const beforeItems = beforeSignals[section] || {};
    const afterItems = afterSignals[section] || {};

    // Get all unique IDs from both states
    const allIds = new Set([...Object.keys(beforeItems), ...Object.keys(afterItems)]);

    allIds.forEach(function (visualId) {
      const beforeSignal = beforeItems[visualId];
      const afterSignal = afterItems[visualId];

      // Determine difference type
      let diffColor = DIFF_COLORS.unchanged;
      let diffType = "unchanged";

      if (!beforeSignal && afterSignal) {
        // New element in "after" state
        diffColor = DIFF_COLORS.new;
        diffType = "new";
      } else if (beforeSignal && !afterSignal) {
        // Element removed in "after" state
        diffColor = DIFF_COLORS.removed;
        diffType = "removed";
      } else if (beforeSignal && afterSignal) {
        // Compare based on diff mode
        const delta = _computeSignalDelta(beforeSignal, afterSignal, comparisonDiffMode);

        if (Math.abs(delta) > DIFF_THRESHOLD) {
          if (delta > 0) {
            diffColor = DIFF_COLORS.improved;
            diffType = "improved";
          } else {
            diffColor = DIFF_COLORS.worsened;
            diffType = "worsened";
          }
        }
      }

      // Apply highlight to "after" scene only
      if (diffType !== "unchanged") {
        const binding = comparisonBindingMapAfter[visualId];
        if (binding) {
          const node = comparisonNodeMapAfter[binding.scene_node] ||
                      comparisonNodeMapAfter[_normalizeSceneNodeId(binding.scene_node)];
          if (node) {
            _applyDifferenceHighlight(node, diffColor, binding.kind);
          }
        }
      }
    });
  });

  console.log("[PVU3D] Differences highlighted");
}

/**
 * Вычислить дельту между двумя signals на основе режима сравнения.
 * @param {object} beforeSignal - Signal "до"
 * @param {object} afterSignal - Signal "после"
 * @param {string} mode - Режим сравнения: "status" | "temperature" | "power" | "alarms"
 * @returns {number} - Нормализованная дельта (-1 до 1)
 * @private
 */
function _computeSignalDelta(beforeSignal, afterSignal, mode) {
  switch (mode) {
    case "status":
      // Compare status: green=1, amber=0, red=-1
      const statusValue = { green: 1, amber: 0, red: -1, inactive: -0.5 };
      const beforeValue = statusValue[beforeSignal.state] || 0;
      const afterValue = statusValue[afterSignal.state] || 0;
      return afterValue - beforeValue;

    case "temperature":
      // Compare temperature (if available)
      if (beforeSignal.temperature !== undefined && afterSignal.temperature !== undefined) {
        const tempDelta = afterSignal.temperature - beforeSignal.temperature;
        // Normalize: -10°C to +10°C -> -1 to 1
        return Math.max(-1, Math.min(1, tempDelta / 10));
      }
      return 0;

    case "power":
      // Compare power consumption (if available)
      if (beforeSignal.power !== undefined && afterSignal.power !== undefined) {
        const powerDelta = beforeSignal.power - afterSignal.power; // Lower is better
        const avgPower = (beforeSignal.power + afterSignal.power) / 2;
        if (avgPower > 0) {
          return Math.max(-1, Math.min(1, powerDelta / avgPower));
        }
      }
      return 0;

    case "alarms":
      // Compare alarm count (if available)
      if (beforeSignal.alarms !== undefined && afterSignal.alarms !== undefined) {
        const alarmDelta = beforeSignal.alarms - afterSignal.alarms; // Lower is better
        return alarmDelta > 0 ? 0.5 : (alarmDelta < 0 ? -0.5 : 0);
      }
      return 0;

    default:
      return 0;
  }
}

/**
 * Применить цветовое выделение различия к узлу.
 * @param {THREE.Object3D} node - Узел сцены
 * @param {number} color - Цвет выделения (hex)
 * @param {string} kind - Тип узла: "node" | "sensor" | "flow" | "room_sensor"
 * @private
 */
function _applyDifferenceHighlight(node, color, kind) {
  if (!node) return;

  // Apply highlight based on node kind
  if (kind === "node" || kind === "sensor") {
    // For nodes and sensors, add emissive glow
    node.traverse(function (child) {
      if (child.isMesh && child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach(function (mat) {
            if (mat.emissive) {
              mat.emissive.setHex(color);
              mat.emissiveIntensity = 0.3;
            }
          });
        } else {
          if (child.material.emissive) {
            child.material.emissive.setHex(color);
            child.material.emissiveIntensity = 0.3;
          }
        }
      }
    });
  } else if (kind === "flow") {
    // For flows, change line color
    if (node.material && node.material.color) {
      node.material.color.setHex(color);
    }
  }
}

/**
 * Применить пресет плоскостей сечения.
 * @param {string} preset - имя пресета: "x", "y", "z", "diagonal", "cross"
 */
function applyClippingPreset(preset) {
  _clearClippingPlanes();

  // Получить центр модели для позиционирования плоскостей
  var center = new THREE.Vector3(0, 0, 0);
  if (modelRoot) {
    var box = new THREE.Box3().setFromObject(modelRoot);
    if (!box.isEmpty()) {
      box.getCenter(center);
    }
  }

  switch (preset) {
    case "x":
      // Сечение по оси X (вертикальная плоскость YZ)
      addClippingPlane({
        normal: [1, 0, 0],
        constant: -center.x,
        enabled: true,
        inverted: false,
      });
      break;

    case "y":
      // Сечение по оси Y (горизонтальная плоскость XZ)
      addClippingPlane({
        normal: [0, 1, 0],
        constant: -center.y,
        enabled: true,
        inverted: false,
      });
      break;

    case "z":
      // Сечение по оси Z (вертикальная плоскость XY)
      addClippingPlane({
        normal: [0, 0, 1],
        constant: -center.z,
        enabled: true,
        inverted: false,
      });
      break;

    case "diagonal":
      // Диагональное сечение
      addClippingPlane({
        normal: [1, 0, 1],
        constant: -(center.x + center.z) / Math.sqrt(2),
        enabled: true,
        inverted: false,
      });
      break;

    case "cross":
      // Крестообразное сечение (X + Z)
      addClippingPlane({
        normal: [1, 0, 0],
        constant: -center.x,
        enabled: true,
        inverted: false,
      });
      addClippingPlane({
        normal: [0, 0, 1],
        constant: -center.z,
        enabled: true,
        inverted: false,
      });
      break;

    default:
      console.warn("Unknown clipping preset:", preset);
      return false;
  }

  setClippingMode(true);
  return true;
}

/**
 * Внутренняя функция: создать визуальный helper для плоскости.
 */
function _createClippingPlaneHelper(plane, enabled) {
  // Создать PlaneHelper для визуализации
  var size = 5; // размер helper в метрах
  var helper = new THREE.PlaneHelper(plane, size, 0xffff00);
  helper.visible = enabled && clippingEnabled;

  // Добавить рамку для лучшей видимости
  var edgesGeometry = new THREE.EdgesGeometry(helper.geometry);
  var edgesMaterial = new THREE.LineBasicMaterial({
    color: 0xffffff,
    linewidth: 2,
    transparent: true,
    opacity: 0.8,
  });
  var edges = new THREE.LineSegments(edgesGeometry, edgesMaterial);
  helper.add(edges);

  return helper;
}

/**
 * Внутренняя функция: обновить helper после изменения plane.
 */
function _updateClippingPlaneHelper(helper, plane) {
  if (!helper || !plane) return;

  // PlaneHelper автоматически следует за plane через референс
  // Но нужно обновить позицию и ориентацию
  var distance = plane.constant;
  var normal = plane.normal.clone();

  helper.position.copy(normal.multiplyScalar(-distance));
  helper.lookAt(helper.position.clone().add(normal));
}

/**
 * Внутренняя функция: обновить видимость helpers.
 */
function _updateClippingHelpersVisibility() {
  for (var i = 0; i < clippingHelpers.length; i++) {
    var helper = clippingHelpers[i];
    var data = clippingPlanesData[i];
    if (helper) {
      helper.visible = data.enabled && clippingEnabled;
    }
  }
}

/**
 * Внутренняя функция: очистить все плоскости.
 */
function _clearClippingPlanes() {
  for (var i = 0; i < clippingHelpers.length; i++) {
    var helper = clippingHelpers[i];
    if (helper && scene) {
      scene.remove(helper);
      if (helper.geometry) helper.geometry.dispose();
      if (helper.material) helper.material.dispose();
    }
  }

  clippingPlanes = [];
  clippingHelpers = [];
  clippingPlanesData = [];
}

/**
 * Внутренняя функция: обновить clipping planes во всех материалах.
 */
function _updateMaterialsClipping() {
  if (!modelRoot && !roomModelRoot) return;

  // Собрать активные плоскости
  var activePlanes = [];
  for (var i = 0; i < clippingPlanes.length; i++) {
    if (clippingPlanesData[i].enabled) {
      activePlanes.push(clippingPlanes[i]);
    }
  }

  // Применить к материалам модели
  var updateMaterial = function (material) {
    if (!material) return;
    material.clippingPlanes = clippingEnabled && activePlanes.length > 0
      ? activePlanes
      : null;
    material.clipShadows = true;
    material.needsUpdate = true;
  };

  var traverse = function (root) {
    if (!root) return;
    root.traverse(function (child) {
      if (child.isMesh) {
        if (Array.isArray(child.material)) {
          child.material.forEach(updateMaterial);
        } else {
          updateMaterial(child.material);
        }
      }
    });
  };

  traverse(modelRoot);
  traverse(roomModelRoot);
}

function _removeLegendOverlay() {
  if (legendOverlay && legendOverlay.parentNode) {
    legendOverlay.parentNode.removeChild(legendOverlay);
  }
  legendOverlay = null;
}

function _updateLabels() {
  if (!labelLayer || !camera || !container || !labelsState.length) return;
  var rect = container.getBoundingClientRect();
  var width = rect.width;
  var height = rect.height;
  if (!width || !height) return;
  var margin = 16;
  for (var i = 0; i < labelsState.length; i += 1) {
    var label = labelsState[i];
    var node = _getNode(label.node);
    if (!node) {
      if (label.lastVisible !== false) {
        label.element.style.display = "none";
        label.lastVisible = false;
      }
      continue;
    }
    var target = new THREE.Vector3();
    node.getWorldPosition(target);
    var projected = target.project(camera);
    if (projected.z >= 1) {
      // Behind near/far planes — скрываем без обновления координат.
      if (label.lastVisible !== false) {
        label.element.style.display = "none";
        label.lastVisible = false;
      }
      continue;
    }
    var x = ((projected.x + 1) / 2) * width;
    var y = ((-projected.y + 1) / 2) * height;
    x = Math.max(margin, Math.min(width - margin, x));
    y = Math.max(margin, Math.min(height - margin, y));
    label.element.style.left = x + "px";
    label.element.style.top = y + "px";
    if (label.lastVisible !== true) {
      label.element.style.display = "block";
      label.lastVisible = true;
    }
    var signal = node.userData && node.userData.pvuSignal;
    var state = signal && signal.state ? signal.state : "normal";
    if (label.element.dataset.state !== state) {
      label.element.dataset.state = state;
    }
  }
}

function _createSceneScaffold() {
  scene = new THREE.Scene();
  // Сплошной фон сцены — убирает просвечивание тёмного CSS-градиента через прозрачные области
  scene.background = new THREE.Color(0x0a1119);
  environmentRoot = new THREE.Group();
  atmosphereRoot = new THREE.Group();
  overlayRoot = new THREE.Group();
  environmentRoot.name = "environment-root";
  atmosphereRoot.name = "atmosphere-root";
  overlayRoot.name = "overlay-root";
  scene.add(environmentRoot);
  scene.add(atmosphereRoot);
  scene.add(overlayRoot);

  ambientLight = new THREE.AmbientLight(0xe6f3ff, 0.9);
  keyLight = new THREE.DirectionalLight(0xffffff, 2.0);
  rimLight = new THREE.DirectionalLight(0x7dd3fc, 0.9);
  fillLight = new THREE.DirectionalLight(0xfef3c7, 0.55);
  keyLight.position.set(6, 10, 8);
  rimLight.position.set(-8, 7, -10);
  fillLight.position.set(0, 4, 10);
  if (shadowsEnabled) {
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(2048, 2048);
    keyLight.shadow.bias = -0.0005;
    keyLight.shadow.normalBias = 0.02;
    keyLight.shadow.radius = 4;
    var keyShadowCam = keyLight.shadow.camera;
    keyShadowCam.near = 0.5;
    keyShadowCam.far = 60;
    keyShadowCam.left = -14;
    keyShadowCam.right = 14;
    keyShadowCam.top = 14;
    keyShadowCam.bottom = -14;
    keyShadowCam.updateProjectionMatrix();
  }
  scene.add(ambientLight);
  scene.add(keyLight);
  scene.add(rimLight);
  scene.add(fillLight);

  _applyEnvironmentLighting(scene);

  _buildEnvironmentDecor();
}

/**
 * Построить процедурную "студийную" среду и назначить её scene.environment
 * через PMREM. Это даёт image-based lighting: металлические корпуса и патрубки
 * установки получают правдоподобные отражения и мягкую заливку без внешних
 * HDR-ассетов. Отключается через performance_budget.image_based_lighting === false.
 * @private
 */
function _buildEnvironmentTexture() {
  if (environmentTexture) return environmentTexture;
  if (!renderer) return null;
  if (((sceneMeta.performance_budget || {}).image_based_lighting === false)) return null;

  if (!pmremGenerator) {
    pmremGenerator = new THREE.PMREMGenerator(renderer);
    pmremGenerator.compileEquirectangularShader();
  }

  // Мини-сцена-источник: тёмный "пол", светлый "потолок" и пара цветных
  // софт-боксов. PMREM свернёт её в свёртку освещения по шероховатости.
  var envScene = new THREE.Scene();
  envScene.background = new THREE.Color(0x0b1722);

  var domeGeo = new THREE.SphereGeometry(40, 24, 16);
  var domeMat = new THREE.MeshBasicMaterial({
    color: 0x1a2b3a,
    side: THREE.BackSide,
  });
  envScene.add(new THREE.Mesh(domeGeo, domeMat));

  // Верхняя заливка (холодный дневной свет).
  var ceiling = new THREE.Mesh(
    new THREE.PlaneGeometry(60, 60),
    new THREE.MeshBasicMaterial({ color: 0xeaf4ff })
  );
  ceiling.position.set(0, 24, 0);
  ceiling.rotation.x = Math.PI / 2;
  envScene.add(ceiling);

  // Тёплый ключевой софт-бокс.
  var keyPanel = new THREE.Mesh(
    new THREE.PlaneGeometry(22, 16),
    new THREE.MeshBasicMaterial({ color: 0xfff1d6 })
  );
  keyPanel.position.set(14, 12, 16);
  keyPanel.lookAt(0, 2, 0);
  envScene.add(keyPanel);

  // Холодный контровой софт-бокс.
  var rimPanel = new THREE.Mesh(
    new THREE.PlaneGeometry(18, 14),
    new THREE.MeshBasicMaterial({ color: 0xbfe4ff })
  );
  rimPanel.position.set(-16, 9, -18);
  rimPanel.lookAt(0, 2, 0);
  envScene.add(rimPanel);

  var target = pmremGenerator.fromScene(envScene, 0.04);
  environmentTexture = target.texture;

  domeGeo.dispose();
  domeMat.dispose();
  envScene.traverse(function (child) {
    if (child.isMesh) {
      child.geometry.dispose();
      child.material.dispose();
    }
  });

  return environmentTexture;
}

/**
 * Назначить процедурную IBL-среду переданной сцене (основной или сравнения).
 * @private
 */
function _applyEnvironmentLighting(targetScene) {
  if (!targetScene) return;
  var envTex = _buildEnvironmentTexture();
  if (envTex) {
    targetScene.environment = envTex;
  }
}

function _buildEnvironmentDecor() {
  floorBase = new THREE.Mesh(
    new THREE.CircleGeometry(18, 128),
    new THREE.MeshBasicMaterial({
      color: _themeColor("floor_color", "#0f3d4c"),
      transparent: true,
      opacity: 0.25,
      side: THREE.DoubleSide,
    })
  );
  floorBase.rotation.x = -Math.PI / 2;
  floorBase.position.y = -0.001;
  environmentRoot.add(floorBase);

  if (shadowsEnabled) {
    // Невидимый "ловец теней": ShadowMaterial рисует только падающую тень,
    // оставляя прозрачным остальной canvas. Это заземляет установку, не
    // закрывая декоративный пол и halo под ней.
    shadowCatcher = new THREE.Mesh(
      new THREE.PlaneGeometry(40, 40),
      new THREE.ShadowMaterial({ opacity: 0.32 })
    );
    shadowCatcher.rotation.x = -Math.PI / 2;
    shadowCatcher.position.y = 0;
    shadowCatcher.receiveShadow = true;
    environmentRoot.add(shadowCatcher);
  }

  floorGlow = new THREE.Mesh(
    new THREE.RingGeometry(4.5, 11.5, 128),
    new THREE.MeshBasicMaterial({
      color: _themeColor("halo_color", DEFAULT_MODEL_ACCENT),
      transparent: true,
      opacity: 0.18,
      side: THREE.DoubleSide,
    })
  );
  floorGlow.rotation.x = -Math.PI / 2;
  floorGlow.position.y = 0.002;
  environmentRoot.add(floorGlow);

  farRing = new THREE.Mesh(
    new THREE.RingGeometry(12.5, 16.8, 128),
    new THREE.MeshBasicMaterial({
      color: _themeColor("far_ring_color", "#1e293b"),
      transparent: true,
      opacity: 0.2,
      side: THREE.DoubleSide,
    })
  );
  farRing.rotation.x = -Math.PI / 2;
  farRing.position.y = -0.002;
  environmentRoot.add(farRing);

  var particlePositions = [];
  atmosphereParticleMotion = [];
  for (var i = 0; i < 180; i += 1) {
    var x = (Math.random() - 0.5) * 28;
    var y = Math.random() * 8 + 0.8;
    var z = (Math.random() - 0.5) * 28;
    particlePositions.push(
      x,
      y,
      z
    );
    atmosphereParticleMotion.push({
      baseX: x,
      baseY: y,
      baseZ: z,
      currentY: y,
      phase: Math.random() * Math.PI * 2,
      drift: 0.4 + Math.random() * 1.2,
      sway: 0.35 + Math.random() * 1.1,
    });
  }
  var particlesGeometry = new THREE.BufferGeometry();
  particlesGeometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(particlePositions, 3)
  );
  atmosphereParticles = new THREE.Points(
    particlesGeometry,
    new THREE.PointsMaterial({
      color: _themeColor("particles_color", "#9dd8ff"),
      transparent: true,
      opacity: 0.22,
      size: 0.06,
      sizeAttenuation: true,
      depthWrite: false,
    })
  );
  atmosphereParticles.userData.baseOpacity = atmosphereParticles.material.opacity;
  atmosphereParticles.userData.baseSize = atmosphereParticles.material.size;
  atmosphereRoot.add(atmosphereParticles);

  seasonAura = new THREE.Mesh(
    new THREE.RingGeometry(6.4, 15.2, 96),
    new THREE.MeshBasicMaterial({
      color: _themeColor("halo_color", DEFAULT_MODEL_ACCENT),
      transparent: true,
      opacity: 0.08,
      side: THREE.DoubleSide,
      depthWrite: false,
    })
  );
  seasonAura.rotation.x = -Math.PI / 2;
  seasonAura.position.y = 0.004;
  atmosphereRoot.add(seasonAura);

  stageBackdrop = new THREE.Mesh(
    new THREE.SphereGeometry(30, 40, 40, 0, Math.PI),
    new THREE.MeshBasicMaterial({
      color: _themeColor("floor_color", "#0f3d4c"),
      transparent: true,
      opacity: 0.08,
      side: THREE.BackSide,
      depthWrite: false,
    })
  );
  stageBackdrop.position.set(0, 8, 0);
  environmentRoot.add(stageBackdrop);
}

function _applyThemeToEnvironment() {
  if (!ambientLight || !keyLight || !rimLight || !fillLight || !floorGlow) return;
  ambientLight.color.copy(_themeColor("ambient_color", "#e6f3ff"));
  keyLight.color.copy(_themeColor("key_color", "#ffffff"));
  rimLight.color.copy(_themeColor("rim_color", "#7dd3fc"));
  fillLight.color.copy(_themeColor("fill_color", "#fef3c7"));
  floorGlow.material.color.copy(_themeColor("halo_color", DEFAULT_MODEL_ACCENT));
  if (floorBase && floorBase.material && floorBase.material.color) {
    floorBase.material.color.copy(_themeColor("floor_color", "#0f3d4c"));
  }
  if (farRing && farRing.material && farRing.material.color) {
    farRing.material.color.copy(_themeColor("far_ring_color", "#1e293b"));
  }
  if (stageBackdrop && stageBackdrop.material && stageBackdrop.material.color) {
    stageBackdrop.material.color.copy(_themeColor("floor_color", "#0f3d4c"));
  }
  if (atmosphereParticles && atmosphereParticles.material && atmosphereParticles.material.color) {
    atmosphereParticles.material.color.copy(_themeColor("particles_color", "#9dd8ff"));
  }
  if (seasonAura && seasonAura.material && seasonAura.material.color) {
    seasonAura.material.color.copy(_themeColor("halo_color", DEFAULT_MODEL_ACCENT));
  }
}

function _onContextLost(event) {
  event.preventDefault();
  _showError("WebGL недоступен, переключение на 2D");
  window.__pvu3d_fallback = true;
  _stopAnimation();
}

function _onContextRestored() {
  _removeOverlay();
  _startAnimation();
}

function _onResize() {
  if (!container || !renderer || !camera) return;
  var width = Math.max(container.clientWidth || 800, 320);
  var height = Math.max(container.clientHeight || 540, 320);
  var maxPixelRatio = ((sceneMeta.performance_budget || {}).max_pixel_ratio || 2.0);
  var widthBudget = width >= 1600 ? 1.15 : width >= 1280 ? 1.28 : width >= 960 ? 1.45 : maxPixelRatio;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, maxPixelRatio, widthBudget));

  // Update camera aspect based on comparison mode
  if (comparisonMode) {
    _updateComparisonViewport();
  } else {
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }

  renderer.setSize(width, height);
  if (composer) {
    composer.setSize(width, height);
    // Обновить размер bloom pass при изменении размера окна
    if (bloomPass) {
      bloomPass.resolution.set(width, height);
    }
  }
}

function init(containerId, meta) {
  container = document.getElementById(containerId);
  if (!container) return false;
  sceneMeta = meta || {};
  upAxis = String(((sceneMeta.asset || {}).up_axis || "Y")).toUpperCase();

  var testCanvas = document.createElement("canvas");
  var gl = testCanvas.getContext("webgl2") || testCanvas.getContext("webgl");
  if (!gl) {
    _showError("WebGL недоступен — используется 2D");
    return false;
  }

  try {
    sharedLoader = _createGltfLoader();
    renderer = new THREE.WebGLRenderer({
      antialias: ((sceneMeta.performance_budget || {}).antialias !== false),
      alpha: false,  // Непрозрачный canvas — устраняет просвечивание тёмного CSS-фона
      powerPreference: "high-performance",
    });
    renderer.setSize(container.clientWidth || 800, container.clientHeight || 540);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    // Счётчики кадра сбрасываются вручную в цикле анимации (см. lastFrameStats).
    renderer.info.autoReset = false;
    // Мягкие контактные тени заземляют установку и резко повышают реализм.
    // Отключаются через performance_budget.shadows === false на слабом железе.
    shadowsEnabled = ((sceneMeta.performance_budget || {}).shadows !== false);
    if (shadowsEnabled) {
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    }
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";
    container.appendChild(renderer.domElement);

    renderer.domElement.addEventListener("webglcontextlost", _onContextLost);
    renderer.domElement.addEventListener("webglcontextrestored", _onContextRestored);

    camera = new THREE.PerspectiveCamera(42, 1, 0.1, 160);
    if (upAxis === "Z") {
      camera.up.set(0, 0, 1);
    }
    camera.position.set(5.2, 3.2, 5.4);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.minDistance = 2.2;
    controls.maxDistance = 160;
    controls.minPolarAngle = 0.12;
    controls.maxPolarAngle = Math.PI * 0.48;
    controls.target.set(0, 0.6, 0);
    controls.update();

    raycaster = new THREE.Raycaster();
    clock = new THREE.Clock();
    _createSceneScaffold();
    _createInfoCard();
    _createLabelLayer();
    _createLegendOverlay();
    _initPostProcessing();
    _onResize();

    renderer.domElement.addEventListener("mousemove", _onMouseMove);
    renderer.domElement.addEventListener("click", _onClick);
    window.addEventListener("resize", _onResize);
    if (window.ResizeObserver) {
      resizeObserver = new window.ResizeObserver(function () {
        _onResize();
      });
      resizeObserver.observe(container);
    }

    isInitialized = true;

    // Load flow field data asynchronously
    loadFlowFieldData("/assets/data/visualization/flow_field.json").catch(
      function (error) {
        console.warn("Flow field data not available:", error);
      }
    );

    return true;
  } catch (error) {
    console.error("[PVU3D] init failed", error);
    _showError("Ошибка инициализации 3D-сцены");
    return false;
  }
}

function _clearOverlayRoot() {
  if (!overlayRoot) return;
  while (overlayRoot.children.length) {
    var child = overlayRoot.children[overlayRoot.children.length - 1];
    overlayRoot.remove(child);
    _disposeObject(child);
  }
}

function _clearLoadedModel() {
  _hideInfoCard();
  hoveredObject = null;
  selectedObject = null;
  interactiveObjects = [];
  nodeMap = {};
  if (modelRoot) {
    modelRoot.visible = false;
    modelRoot = null;
  }
  viewMetrics = null;
  _clearOverlayRoot();
}

function _clearLoadedRoom() {
  if (roomModelRoot) {
    roomModelRoot.visible = false;
    roomModelRoot = null;
  }
}

function _disposeCachedModels() {
  Object.keys(cachedModelEntries).forEach(function (key) {
    var entry = cachedModelEntries[key];
    if (!entry || !entry.root) return;
    if (scene && entry.root.parent === scene) {
      scene.remove(entry.root);
    }
    _disposeObject(entry.root);
  });
  cachedModelEntries = {};
  pendingModelEntries = {};
}

function _disposeCachedRooms() {
  Object.keys(cachedRoomEntries).forEach(function (key) {
    var entry = cachedRoomEntries[key];
    if (!entry || !entry.root) return;
    if (scene && entry.root.parent === scene) {
      scene.remove(entry.root);
    }
    _disposeObject(entry.root);
  });
  cachedRoomEntries = {};
  pendingRoomEntries = {};
}

function _normalizeLoadedModel(rawRoot, sceneProfile, modelDescriptor) {
  var wrapper = new THREE.Group();
  wrapper.name = "loaded-model";
  wrapper.add(rawRoot);
  var transformProfile = _sceneProfileBlock(sceneProfile, "transform");
  rawRoot.traverse(function (child) {
    if (child.isMesh) {
      _prepareModelMesh(child, modelDescriptor);
    }
  });
  var rotation = transformProfile.rotation_deg || {};
  rawRoot.rotation.x = THREE.MathUtils.degToRad(rotation.x || 0);
  rawRoot.rotation.y = THREE.MathUtils.degToRad(rotation.y || 0);
  rawRoot.rotation.z = THREE.MathUtils.degToRad(rotation.z || 0);
  var scaleMultiplier = _withDefault(transformProfile.scale_multiplier, 1);
  if (scaleMultiplier !== 1) {
    rawRoot.scale.multiplyScalar(scaleMultiplier);
  }
  rawRoot.updateMatrixWorld(true);
  var box = new THREE.Box3().setFromObject(rawRoot);
  var center = box.getCenter(new THREE.Vector3());
  rawRoot.position.x -= center.x;
  rawRoot.position.z -= center.z;
  if (upAxis === "Z") {
    rawRoot.position.z -= box.min.z;
  } else {
    rawRoot.position.y -= box.min.y;
  }
  rawRoot.position[upAxis === "Z" ? "z" : "y"] +=
    (_withDefault(transformProfile.lift_ratio, 0) * box.getSize(new THREE.Vector3())[upAxis === "Z" ? "z" : "y"]);
  wrapper.updateMatrixWorld(true);

  // Initialize fan blades for motion blur effect
  _initializeFanBlades(rawRoot);

  return wrapper;
}

function _initializeFanBlades(root) {
  // Find fan rotor node and collect blade meshes
  var fanRule = sceneMeta.animation_rules && sceneMeta.animation_rules.fan_rotation;
  if (!fanRule || !fanRule.target_node) return;

  root.traverse(function (child) {
    var normalizedName = String(child.name || "").toLowerCase().replace(/\./g, "");

    // Check if this is the fan rotor node
    var targetNodeNormalized = fanRule.target_node.toLowerCase().replace(/\./g, "");
    if (normalizedName === targetNodeNormalized) {
      // Collect all blade meshes
      var blades = [];
      child.traverse(function (blade) {
        if (blade.isMesh && blade.name && /blade/i.test(blade.name)) {
          // Store base opacity for blur effect
          if (blade.material) {
            blade.userData.baseOpacity = blade.material.opacity !== undefined ? blade.material.opacity : 1.0;
          }
          blades.push(blade);
        }
      });

      if (blades.length > 0) {
        child.userData.fanBlades = blades;
      }
    }
  });
}

function _normalizeRoomModel(rawRoot, roomDescriptor) {
  var wrapper = new THREE.Group();
  wrapper.name = "loaded-room-model";
  wrapper.add(rawRoot);
  rawRoot.traverse(function (child) {
    if (child.isMesh) {
      _prepareModelMesh(child, roomDescriptor);
    }
  });
  rawRoot.updateMatrixWorld(true);
  var box = new THREE.Box3().setFromObject(rawRoot);
  var size = box.getSize(new THREE.Vector3());
  var center = box.getCenter(new THREE.Vector3());
  rawRoot.position.x -= center.x;
  rawRoot.position.z -= center.z;
  rawRoot.position[upAxis === "Z" ? "z" : "y"] -= box.min[upAxis === "Z" ? "z" : "y"];
  wrapper.userData.baseSize = size;
  wrapper.userData.baseLongSize = Math.max(size.x, size.z, 0.001);
  wrapper.userData.baseMaxDim = Math.max(size.x, size.y, size.z, 0.001);
  wrapper.updateMatrixWorld(true);
  return wrapper;
}

function _computeViewMetrics(root) {
  var box = new THREE.Box3().setFromObject(root);
  var center = box.getCenter(new THREE.Vector3());
  var size = box.getSize(new THREE.Vector3());
  var verticalAxis = upAxis === "Z" ? "z" : "y";
  var longAxis = size.x >= size.z ? "x" : "z";
  var sideAxis = longAxis === "x" ? "z" : "x";
  var maxDim = Math.max(size.x, size.y, size.z, 1);
  var markerScale = _sizingValue("marker_scale", 1);
  var flowScale = _sizingValue("flow_scale", 1);
  var connectorScale = _sizingValue("connector_scale", 1);
  var effectScale = _sizingValue("effect_scale", 1);
  return {
    box: box,
    center: center,
    size: size,
    verticalAxis: verticalAxis,
    longAxis: longAxis,
    sideAxis: sideAxis,
    maxDim: maxDim,
    markerSize: maxDim * 0.028 * markerScale,
    flowRadius: maxDim * 0.015 * flowScale,
    connectorScale: connectorScale,
    effectScale: effectScale,
  };
}

function _positionFromMetrics(longT, verticalT, sideT) {
  if (!viewMetrics) return new THREE.Vector3();
  var point = viewMetrics.center.clone();
  point[viewMetrics.longAxis] = _lerpByAxis(
    viewMetrics.box.min,
    viewMetrics.box.max,
    viewMetrics.longAxis,
    longT
  );
  point[viewMetrics.verticalAxis] = _lerpByAxis(
    viewMetrics.box.min,
    viewMetrics.box.max,
    viewMetrics.verticalAxis,
    verticalT
  );
  point[viewMetrics.sideAxis] =
    viewMetrics.center[viewMetrics.sideAxis] +
    (viewMetrics.size[viewMetrics.sideAxis] || viewMetrics.maxDim * 0.2) * sideT;
  return point;
}

function _resolvePointFromSpec(spec, anchors, fallbackSpec) {
  var namedAnchors = anchors || {};
  if (typeof spec === "string" && namedAnchors[spec]) {
    return namedAnchors[spec].clone();
  }

  var merged = Object.assign({}, fallbackSpec || {}, spec || {});
  var basePoint = null;
  if (merged.anchor && namedAnchors[merged.anchor]) {
    basePoint = namedAnchors[merged.anchor].clone();
    if (merged.long_delta) {
      basePoint[viewMetrics.longAxis] += _normalizedDeltaByAxis(viewMetrics.longAxis, merged.long_delta);
    }
    if (merged.vertical_delta) {
      basePoint[viewMetrics.verticalAxis] += _normalizedDeltaByAxis(viewMetrics.verticalAxis, merged.vertical_delta);
    }
    if (merged.side_delta) {
      basePoint[viewMetrics.sideAxis] += _normalizedDeltaByAxis(viewMetrics.sideAxis, merged.side_delta);
    }
    return basePoint;
  }

  return _positionFromMetrics(
    _withDefault(merged.long, 0.5),
    _withDefault(merged.vertical, 0.5),
    _withDefault(merged.side, 0)
  );
}

function _resolvePathSpecs(specs, anchors, fallbackSpecs) {
  var sourceSpecs = Array.isArray(specs) && specs.length ? specs : fallbackSpecs;
  return sourceSpecs.map(function (spec, index) {
    return _resolvePointFromSpec(spec, anchors, fallbackSpecs[index]);
  });
}

function _lineToFloor(point) {
  var floorValue = viewMetrics.box.min[viewMetrics.verticalAxis] + viewMetrics.maxDim * 0.02;
  var base = point.clone();
  base[viewMetrics.verticalAxis] = floorValue;
  return base;
}

function _createVerticalConnector(point, color) {
  var base = _lineToFloor(point);
  var direction = new THREE.Vector3().subVectors(point, base);
  var length = direction.length();
  var connectorScale = viewMetrics.connectorScale || 1;
  var geometry = new THREE.CylinderGeometry(
    viewMetrics.markerSize * 0.09 * connectorScale,
    viewMetrics.markerSize * 0.09 * connectorScale,
    Math.max(length, 0.01),
    12
  );
  var material = new THREE.MeshBasicMaterial({
    color: color,
    transparent: true,
    opacity: 0.4,
    depthWrite: false,
  });
  var mesh = new THREE.Mesh(geometry, material);
  mesh.position.copy(base.clone().add(direction.multiplyScalar(0.5)));
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.clone().normalize());
  return mesh;
}

function _registerNode(sceneNode, group, interactive) {
  group.name = sceneNode;
  nodeMap[sceneNode] = group;
  nodeMap[_normalizeSceneNodeId(sceneNode)] = group;
  if (interactive !== false) {
    group.traverse(function (child) {
      if (child.isMesh) {
        child.userData.interactiveOwner = group;
        interactiveObjects.push(child);
      }
    });
  }
}

function _registerSyntheticBinding(sceneNode, visualId, kind) {
  if (!visualId) return;
  var binding = {
    visual_id: visualId,
    scene_node: sceneNode,
    kind: kind || "sensor",
  };
  bindingMap[sceneNode] = binding;
  bindingMap[_normalizeSceneNodeId(sceneNode)] = binding;
  bindingByVisualId[visualId] = binding;
}

function _roomDescriptorKey(roomDescriptor) {
  return String(
    (roomDescriptor && roomDescriptor.id) ||
    (roomDescriptor && roomDescriptor.model_url) ||
    "room-model"
  );
}

function _roomPlacementPoint(anchors) {
  var placement = (currentRoomDescriptor && currentRoomDescriptor.placement) || {};
  return _resolvePointFromSpec(
    {
      anchor: placement.anchor || "room",
      long_delta: (placement.long_delta || 0) + currentScaleTuning.room_long_delta,
      vertical_delta: (placement.vertical_delta || 0) + currentScaleTuning.room_vertical_delta,
      side_delta: (placement.side_delta || 0) + currentScaleTuning.room_side_delta,
    },
    anchors,
    { anchor: "room" }
  );
}

function _placementDirection(deltaValue, fallback) {
  if (typeof deltaValue === "number" && Number.isFinite(deltaValue) && Math.abs(deltaValue) > 1e-6) {
    return deltaValue >= 0 ? 1 : -1;
  }
  if (typeof fallback === "number" && Number.isFinite(fallback) && Math.abs(fallback) > 1e-6) {
    return fallback >= 0 ? 1 : -1;
  }
  return 1;
}

function _roomPlacementClearance(placement) {
  var base = viewMetrics ? viewMetrics.maxDim : 1;
  return {
    long: Math.max(base * 0.02, base * _withDefault(placement.clearance_ratio, 0.24)),
    side: Math.max(0, base * _withDefault(placement.side_clearance_ratio, 0.1)),
    vertical: Math.max(0, base * _withDefault(placement.vertical_clearance_ratio, 0.03)),
    maxAutoShift: Math.max(base * 0.6, base * _withDefault(placement.max_auto_shift_ratio, 3.2)),
  };
}

function _expandedRoomClearanceBox(modelBox, clearance) {
  var expanded = modelBox.clone();
  expanded.min[viewMetrics.longAxis] -= clearance.long;
  expanded.max[viewMetrics.longAxis] += clearance.long;
  expanded.min[viewMetrics.sideAxis] -= clearance.side;
  expanded.max[viewMetrics.sideAxis] += clearance.side;
  expanded.min[viewMetrics.verticalAxis] -= clearance.vertical;
  expanded.max[viewMetrics.verticalAxis] += clearance.vertical;
  return expanded;
}

function _roomPlacementDirections(roomBox, modelBox, placement) {
  var roomCenter = roomBox.getCenter(new THREE.Vector3());
  var modelCenter = modelBox.getCenter(new THREE.Vector3());
  return {
    long: _placementDirection(
      placement.long_delta,
      roomCenter[viewMetrics.longAxis] - modelCenter[viewMetrics.longAxis]
    ),
    side: _placementDirection(
      placement.side_delta,
      roomCenter[viewMetrics.sideAxis] - modelCenter[viewMetrics.sideAxis]
    ),
    vertical: _placementDirection(
      placement.vertical_delta,
      roomCenter[viewMetrics.verticalAxis] - modelCenter[viewMetrics.verticalAxis]
    ),
  };
}

function _axisGapAlongDirection(referenceBox, movingBox, axisName, direction) {
  if (direction >= 0) {
    return movingBox.min[axisName] - referenceBox.max[axisName];
  }
  return referenceBox.min[axisName] - movingBox.max[axisName];
}

function _computeRoomSeparation(roomBox, modelBox, directions, clearance) {
  if (!roomBox || !modelBox || !viewMetrics) return null;
  var expandedBox = _expandedRoomClearanceBox(modelBox, clearance);
  return {
    longGap: _axisGapAlongDirection(modelBox, roomBox, viewMetrics.longAxis, directions.long),
    sideGap: _axisGapAlongDirection(modelBox, roomBox, viewMetrics.sideAxis, directions.side),
    verticalGap: _axisGapAlongDirection(modelBox, roomBox, viewMetrics.verticalAxis, directions.vertical),
    intersectsModel: roomBox.intersectsBox(modelBox),
    intersectsClearance: roomBox.intersectsBox(expandedBox),
    clearance: {
      long: clearance.long,
      side: clearance.side,
      vertical: clearance.vertical,
    },
    directions: {
      long: directions.long,
      side: directions.side,
      vertical: directions.vertical,
    },
  };
}

function _applyRoomClearance(roomRoot, placement) {
  if (!roomRoot || !modelRoot || !viewMetrics) return null;
  var roomBox = new THREE.Box3().setFromObject(roomRoot);
  var modelBox = new THREE.Box3().setFromObject(modelRoot);
  if (roomBox.isEmpty() || modelBox.isEmpty()) return null;

  var clearance = _roomPlacementClearance(placement || {});
  var directions = _roomPlacementDirections(roomBox, modelBox, placement || {});
  var shiftLong = 0;
  var shiftSide = 0;

  for (var iteration = 0; iteration < 5; iteration += 1) {
    var expandedBox = _expandedRoomClearanceBox(modelBox, clearance);
    if (!roomBox.intersectsBox(expandedBox)) {
      break;
    }

    var requiredLong = directions.long >= 0
      ? expandedBox.max[viewMetrics.longAxis] - roomBox.min[viewMetrics.longAxis]
      : roomBox.max[viewMetrics.longAxis] - expandedBox.min[viewMetrics.longAxis];
    var requiredSide = directions.side >= 0
      ? expandedBox.max[viewMetrics.sideAxis] - roomBox.min[viewMetrics.sideAxis]
      : roomBox.max[viewMetrics.sideAxis] - expandedBox.min[viewMetrics.sideAxis];

    var canLong = requiredLong > 1e-5 && shiftLong < clearance.maxAutoShift;
    var canSide = requiredSide > 1e-5 && shiftSide < clearance.maxAutoShift;
    if (!canLong && !canSide) {
      break;
    }

    var moveAlongSide = canSide && (!canLong || requiredSide < requiredLong * 0.72);
    if (moveAlongSide) {
      var sideStep = Math.min(requiredSide + clearance.side * 0.08, clearance.maxAutoShift - shiftSide);
      roomRoot.position[viewMetrics.sideAxis] += sideStep * directions.side;
      shiftSide += sideStep;
    } else {
      var longStep = Math.min(requiredLong + clearance.long * 0.08, clearance.maxAutoShift - shiftLong);
      roomRoot.position[viewMetrics.longAxis] += longStep * directions.long;
      shiftLong += longStep;
    }

    roomRoot.updateMatrixWorld(true);
    roomBox.setFromObject(roomRoot);
  }

  return {
    shiftLong: shiftLong,
    shiftSide: shiftSide,
    separation: _computeRoomSeparation(roomBox, modelBox, directions, clearance),
  };
}

function _roomPlacementRuntimeMetrics() {
  if (!roomModelRoot || !modelRoot || !viewMetrics) return null;
  var placement = (currentRoomDescriptor && currentRoomDescriptor.placement) || {};
  var roomBox = new THREE.Box3().setFromObject(roomModelRoot);
  var modelBox = new THREE.Box3().setFromObject(modelRoot);
  if (roomBox.isEmpty() || modelBox.isEmpty()) return null;
  var clearance = _roomPlacementClearance(placement);
  var directions = _roomPlacementDirections(roomBox, modelBox, placement);
  return _computeRoomSeparation(roomBox, modelBox, directions, clearance);
}

function _resolveRoomScale(roomRoot, placement) {
  var tunedScale = _withDefault(placement.scale_multiplier, 1) * (currentScaleTuning.room_scale || 1);
  if (!viewMetrics || !roomRoot || !roomRoot.userData) {
    return _clamp(tunedScale, 0.1, 20);
  }
  var targetLongRatio = _withDefault(placement.target_long_ratio, 1.5);
  var baseLongSize = roomRoot.userData.baseLongSize || roomRoot.userData.baseMaxDim;
  if (!baseLongSize || !Number.isFinite(baseLongSize)) {
    return _clamp(tunedScale, 0.1, 20);
  }
  var referenceLongSize = viewMetrics.size[viewMetrics.longAxis] || viewMetrics.maxDim;
  var desiredLongSize = referenceLongSize * Math.max(targetLongRatio, 0.1);
  var adaptiveScale = desiredLongSize / baseLongSize;
  return _clamp(adaptiveScale * tunedScale, 0.1, 40);
}

function _applyRoomPlacement(roomRoot, anchors) {
  if (!roomRoot || !anchors) return;
  var placement = (currentRoomDescriptor && currentRoomDescriptor.placement) || {};
  roomRoot.position.copy(_roomPlacementPoint(anchors));
  roomRoot.rotation.set(
    0,
    THREE.MathUtils.degToRad(
      (placement.rotation_deg_y || 0) +
      (currentScaleTuning.room_rotation_delta_deg || 0)
    ),
    0
  );
  var scale = _resolveRoomScale(roomRoot, placement);
  roomRoot.scale.setScalar(scale);
  roomRoot.updateMatrixWorld(true);
  var clearanceResult = _applyRoomClearance(roomRoot, placement);
  roomRoot.userData.placementRuntime = {
    appliedScale: scale,
    autoShiftLong: clearanceResult ? clearanceResult.shiftLong : 0,
    autoShiftSide: clearanceResult ? clearanceResult.shiftSide : 0,
    separation: clearanceResult ? clearanceResult.separation : null,
  };
}

function _roomAnchorPoint(nodeName, fallbackPoint) {
  if (!roomModelRoot) {
    return fallbackPoint ? fallbackPoint.clone() : null;
  }
  var anchorNode = roomModelRoot.getObjectByName(nodeName);
  if (!anchorNode) {
    return fallbackPoint ? fallbackPoint.clone() : null;
  }
  return anchorNode.getWorldPosition(new THREE.Vector3());
}

function _createStageMarker(sceneNode, labelPoint, options) {
  var radius = viewMetrics.markerSize * (options.scale || 1);
  var group = new THREE.Group();
  group.position.copy(labelPoint);
  group.userData.overlayKind = options.kind || "node";
  group.userData.colorMaterials = [];
  group.userData.glowMaterials = [];

  var ring = new THREE.Mesh(
    new THREE.TorusGeometry(radius * 1.4, radius * 0.16, 18, 48),
    new THREE.MeshStandardMaterial({
      color: STATUS_COLORS.inactive,
      emissive: new THREE.Color(0x0f172a),
      emissiveIntensity: 0.3,
      roughness: 0.28,
      metalness: 0.1,
      transparent: true,
      opacity: 0.95,
    })
  );
  ring.rotation.x = Math.PI / 2;
  group.add(ring);

  // Мини-модель оборудования вместо абстрактного октаэдра (замечание
  // рецензента editing-3 про «жёлтые/зелёные шары»). Сенсорная ветка и
  // fallback на октаэдр (нет options.model / неизвестное имя) — без изменений.
  var miniModel = options.kind === "sensor"
    ? null
    : _buildStageMiniModel(options.model, radius);
  var core = null;
  if (miniModel) {
    miniModel.userData.overlayKind = "mini-model";
    group.add(miniModel);
  } else {
    var coreGeometry = options.kind === "sensor"
      ? new THREE.SphereGeometry(radius * 0.72, 24, 24)
      : new THREE.OctahedronGeometry(radius * 0.82, 0);
    core = new THREE.Mesh(
      coreGeometry,
      new THREE.MeshStandardMaterial({
        color: STATUS_COLORS.inactive,
        emissive: new THREE.Color(0x0b1220),
        emissiveIntensity: 0.18,
        roughness: options.kind === "sensor" ? 0.18 : 0.34,
        metalness: options.kind === "sensor" ? 0.24 : 0.1,
        transparent: true,
        opacity: 0.95,
      })
    );
    group.add(core);
  }

  var halo = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 1.45, 24, 24),
    new THREE.MeshBasicMaterial({
      color: STATUS_COLORS.inactive,
      transparent: true,
      opacity: options.kind === "sensor" ? 0.12 : 0.09,
      depthWrite: false,
    })
  );
  group.add(halo);
  group.add(_createVerticalConnector(labelPoint, STATUS_COLORS.inactive));

  // Тела мини-моделей НАМЕРЕННО не попадают в colorMaterials/glowMaterials:
  // _applyNodeSignal перекрашивает эти массивы целиком в цвет статуса, и
  // оборудование снова стало бы одноцветным «шаром». Статус читается по
  // кольцу + гало + коннектору.
  group.userData.colorMaterials.push(ring.material, halo.material);
  group.userData.glowMaterials.push(ring.material);
  if (core) {
    group.userData.colorMaterials.push(core.material);
    group.userData.glowMaterials.push(core.material);
  }
  if (group.children[3] && group.children[3].material) {
    group.userData.colorMaterials.push(group.children[3].material);
  }
  _registerNode(sceneNode, group, true);
  overlayRoot.add(group);
  return group;
}

// --- Процедурные мини-модели секций ПВУ (замечание рецензента editing-3) ---
// Узнаваемые силуэты оборудования вместо абстрактных октаэдров. Материалы
// статичны (палитра SECTION_PALETTE) и не регистрируются в статусных
// массивах — см. комментарий в _createStageMarker.

function _buildStageMiniModel(modelName, radius) {
  switch (modelName) {
    case "intake": return _buildIntakeModel(radius);
    case "filter": return _buildFilterModel(radius, false);
    case "filter_fine": return _buildFilterModel(radius, true);
    case "heater": return _buildHeaterModel(radius);
    case "fan": return _buildFanModel(radius);
    case "cooler": return _buildCoolerModel(radius);
    case "silencer": return _buildSilencerModel(radius);
    case "duct": return _buildDuctModel(radius);
    case "recuperator": return _buildRecuperatorModel(radius);
    default: return null;
  }
}

function _miniModelMaterial(colorHex, options) {
  var settings = options || {};
  return new THREE.MeshStandardMaterial({
    color: colorHex,
    emissive: new THREE.Color(settings.emissive || 0x0b1220),
    emissiveIntensity: _withDefault(settings.emissiveIntensity, 0.18),
    roughness: _withDefault(settings.roughness, 0.38),
    metalness: _withDefault(settings.metalness, 0.22),
    transparent: true,
    opacity: _withDefault(settings.opacity, 0.96),
  });
}

// Билдеры строят модель с осью потока вдоль локальной Z; затем группа
// поворачивается так, чтобы локальная Z совпала с длинной осью установки.
function _orientAlongLongAxis(object) {
  if (!viewMetrics) return;
  if (viewMetrics.longAxis === "x") {
    object.rotation.y = Math.PI / 2;
  } else if (viewMetrics.longAxis === "y") {
    object.rotation.x = -Math.PI / 2;
  }
}

function _buildIntakeModel(radius) {
  var group = new THREE.Group();
  var frame = new THREE.Mesh(
    new THREE.BoxGeometry(radius * 1.6, radius * 1.6, radius * 0.22),
    _miniModelMaterial(SECTION_PALETTE.frame.getHex(), { metalness: 0.34 })
  );
  group.add(frame);
  for (var i = 0; i < 4; i += 1) {
    var louver = new THREE.Mesh(
      new THREE.BoxGeometry(radius * 1.34, radius * 0.14, radius * 0.4),
      _miniModelMaterial(SECTION_PALETTE.intake.getHex(), { metalness: 0.3 })
    );
    louver.position.y = (i - 1.5) * radius * 0.36;
    louver.position.z = radius * 0.16;
    louver.rotation.x = -0.6;
    group.add(louver);
  }
  _orientAlongLongAxis(group);
  return group;
}

function _buildFilterModel(radius, fine) {
  var group = new THREE.Group();
  var mediaColor = fine ? 0xbae6fd : SECTION_PALETTE.filter.getHex();
  var frame = new THREE.Mesh(
    new THREE.BoxGeometry(radius * 1.7, radius * 1.7, radius * 0.3),
    _miniModelMaterial(SECTION_PALETTE.frame.getHex(), { metalness: 0.34 })
  );
  group.add(frame);
  var pleats = fine ? 9 : 7;
  for (var i = 0; i < pleats; i += 1) {
    var pleat = new THREE.Mesh(
      new THREE.BoxGeometry(radius * 0.16, radius * 1.46, radius * 0.52),
      _miniModelMaterial(mediaColor, { roughness: 0.6, metalness: 0.05 })
    );
    pleat.position.x = (i - (pleats - 1) / 2) * ((radius * 1.4) / pleats);
    pleat.rotation.y = i % 2 === 0 ? 0.5 : -0.5;
    group.add(pleat);
  }
  _orientAlongLongAxis(group);
  return group;
}

function _buildHeaterModel(radius) {
  var group = new THREE.Group();
  var frame = new THREE.Mesh(
    new THREE.BoxGeometry(radius * 1.7, radius * 1.7, radius * 0.34),
    _miniModelMaterial(SECTION_PALETTE.frame.getHex(), { metalness: 0.3 })
  );
  group.add(frame);
  // ТЭНы электрокалорифера светятся статично (не зависят от статуса).
  for (var i = 0; i < 4; i += 1) {
    var element = new THREE.Mesh(
      new THREE.CylinderGeometry(radius * 0.09, radius * 0.09, radius * 1.42, 12),
      _miniModelMaterial(0xff6a3d, {
        emissive: 0xff6a3d,
        emissiveIntensity: 0.85,
        roughness: 0.3,
        metalness: 0.1,
      })
    );
    element.rotation.z = Math.PI / 2;
    element.position.y = (i - 1.5) * radius * 0.4;
    element.position.z = radius * 0.2;
    group.add(element);
  }
  _orientAlongLongAxis(group);
  return group;
}

function _buildFanModel(radius) {
  var group = new THREE.Group();
  var shroud = new THREE.Mesh(
    new THREE.TorusGeometry(radius * 0.92, radius * 0.14, 14, 42),
    _miniModelMaterial(SECTION_PALETTE.frame.getHex(), { metalness: 0.4, roughness: 0.3 })
  );
  group.add(shroud);
  var hub = new THREE.Mesh(
    new THREE.CylinderGeometry(radius * 0.24, radius * 0.24, radius * 0.34, 18),
    _miniModelMaterial(SECTION_PALETTE.fan.getHex(), { metalness: 0.4 })
  );
  hub.rotation.x = Math.PI / 2;
  group.add(hub);
  for (var i = 0; i < 6; i += 1) {
    var angle = (Math.PI * 2 * i) / 6;
    var blade = new THREE.Mesh(
      new THREE.BoxGeometry(radius * 0.2, radius * 0.66, radius * 0.07),
      _miniModelMaterial(SECTION_PALETTE.fan.getHex(), { metalness: 0.3, opacity: 0.94 })
    );
    blade.position.x = Math.cos(angle) * radius * 0.5;
    blade.position.y = Math.sin(angle) * radius * 0.5;
    blade.rotation.z = angle;
    blade.rotation.y = 0.42;
    group.add(blade);
  }
  _orientAlongLongAxis(group);
  return group;
}

function _buildCoolerModel(radius) {
  var group = new THREE.Group();
  var frame = new THREE.Mesh(
    new THREE.BoxGeometry(radius * 1.6, radius * 1.6, radius * 0.3),
    _miniModelMaterial(SECTION_PALETTE.frame.getHex(), { metalness: 0.3 })
  );
  group.add(frame);
  for (var i = 0; i < 6; i += 1) {
    var fin = new THREE.Mesh(
      new THREE.BoxGeometry(radius * 0.06, radius * 1.36, radius * 0.5),
      _miniModelMaterial(0x7dd3fc, { roughness: 0.3, metalness: 0.5 })
    );
    fin.position.x = (i - 2.5) * radius * 0.24;
    group.add(fin);
  }
  var header = new THREE.Mesh(
    new THREE.CylinderGeometry(radius * 0.1, radius * 0.1, radius * 1.5, 12),
    _miniModelMaterial(0x0ea5e9, { metalness: 0.5 })
  );
  header.rotation.z = Math.PI / 2;
  header.position.y = -radius * 0.86;
  group.add(header);
  _orientAlongLongAxis(group);
  return group;
}

function _buildSilencerModel(radius) {
  var group = new THREE.Group();
  var shellMaterial = _miniModelMaterial(SECTION_PALETTE.silencer.getHex(), {
    opacity: 0.62,
    roughness: 0.5,
    metalness: 0.12,
  });
  shellMaterial.side = THREE.DoubleSide;
  var shell = new THREE.Mesh(
    new THREE.CylinderGeometry(radius * 0.8, radius * 0.8, radius * 1.9, 20, 1, true),
    shellMaterial
  );
  shell.rotation.x = Math.PI / 2;
  group.add(shell);
  for (var i = 0; i < 3; i += 1) {
    var baffle = new THREE.Mesh(
      new THREE.BoxGeometry(radius * 0.14, radius * 1.3, radius * 1.66),
      _miniModelMaterial(0xc4b5fd, { roughness: 0.66, metalness: 0.04 })
    );
    baffle.position.x = (i - 1) * radius * 0.46;
    group.add(baffle);
  }
  _orientAlongLongAxis(group);
  return group;
}

function _buildDuctModel(radius) {
  var group = new THREE.Group();
  var duct = new THREE.Mesh(
    new THREE.BoxGeometry(radius * 1.2, radius * 1.2, radius * 2.0),
    _miniModelMaterial(SECTION_PALETTE.duct.getHex(), { metalness: 0.42, roughness: 0.3, opacity: 0.9 })
  );
  group.add(duct);
  for (var i = -1; i <= 1; i += 1) {
    var flange = new THREE.Mesh(
      new THREE.BoxGeometry(radius * 1.34, radius * 1.34, radius * 0.08),
      _miniModelMaterial(SECTION_PALETTE.frame.getHex(), { metalness: 0.4 })
    );
    flange.position.z = i * radius * 0.92;
    group.add(flange);
  }
  _orientAlongLongAxis(group);
  return group;
}

function _buildRecuperatorModel(radius) {
  var group = new THREE.Group();
  // Пластинчатый перекрёстноточный теплообменник: ромб (куб, повёрнутый на
  // 45°) с пакетом пластин — классическое обозначение на схемах ОВиК.
  var core = new THREE.Group();
  core.rotation.z = Math.PI / 4;
  var shellMaterial = _miniModelMaterial(SECTION_PALETTE.recuperator.getHex(), {
    opacity: 0.42,
    roughness: 0.4,
  });
  shellMaterial.depthWrite = false;
  var shell = new THREE.Mesh(
    new THREE.BoxGeometry(radius * 1.3, radius * 1.3, radius * 1.3),
    shellMaterial
  );
  core.add(shell);
  for (var i = 0; i < 6; i += 1) {
    var plate = new THREE.Mesh(
      new THREE.BoxGeometry(radius * 1.18, radius * 0.05, radius * 1.18),
      _miniModelMaterial(0x6ee7b7, { roughness: 0.5, metalness: 0.26 })
    );
    plate.position.y = (i - 2.5) * radius * 0.2;
    core.add(plate);
  }
  group.add(core);
  _orientAlongLongAxis(group);
  return group;
}

function _createZoneVolume(sceneNode, centerPoint, roomProfile, options) {
  var profile = roomProfile || {};
  var settings = options || {};
  var zoneColor = _colorFromHex(settings.color || "#67e8f9");
  var roomSize = {
    x: viewMetrics.longAxis === "x"
      ? viewMetrics.maxDim * _withDefault(profile.long_scale, 0.5)
      : viewMetrics.maxDim * _withDefault(profile.side_scale, 0.28),
    y: viewMetrics.verticalAxis === "y"
      ? viewMetrics.maxDim * _withDefault(profile.vertical_scale, 0.38)
      : viewMetrics.maxDim * _withDefault(profile.long_scale, 0.5),
    z: viewMetrics.longAxis === "z"
      ? viewMetrics.maxDim * _withDefault(profile.long_scale, 0.5)
      : viewMetrics.maxDim * _withDefault(profile.side_scale, 0.28),
  };
  var geometry = new THREE.BoxGeometry(roomSize.x, roomSize.y, roomSize.z);
  var material = new THREE.MeshBasicMaterial({
    color: zoneColor,
    transparent: true,
    opacity: _withDefault(settings.opacity, 0.14),
    depthWrite: false,
  });
  var box = new THREE.Mesh(geometry, material);
  box.position.copy(centerPoint);
  var edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(geometry),
    new THREE.LineBasicMaterial({
      color: zoneColor,
      transparent: true,
      opacity: _withDefault(settings.edgeOpacity, 0.38),
    })
  );
  edges.position.copy(centerPoint);
  var group = new THREE.Group();
  group.userData.overlayKind = settings.overlayKind || "room";
  group.userData.colorMaterials = [material, edges.material];
  group.userData.glowMaterials = [material];
  group.add(box);
  group.add(edges);
  if (settings.signal) {
    group.userData.pvuSignal = settings.signal;
    group.userData.pvuState = "inactive";
  }
  _registerNode(sceneNode, group, _withDefault(settings.interactive, true));
  overlayRoot.add(group);
  return group;
}

function _roomVolumeProfile(baseProfile, roomDescriptor) {
  var profile = Object.assign({}, baseProfile || {});
  var volume = roomDescriptor && roomDescriptor.volume_m3 ? roomDescriptor.volume_m3 : 250;
  var volumeFactor = _clamp(Math.pow(volume / 250, 1 / 3), 0.82, 1.55);
  return {
    long_scale: _withDefault(profile.long_scale, 0.5) * volumeFactor,
    vertical_scale: _withDefault(profile.vertical_scale, 0.38) * Math.min(1.28, 0.92 + volumeFactor * 0.24),
    side_scale: _withDefault(profile.side_scale, 0.28) * Math.min(1.36, 0.88 + volumeFactor * 0.28),
  };
}

function _createRoomZone(sceneNode, centerPoint, roomProfile) {
  return _createZoneVolume(sceneNode, centerPoint, roomProfile, {
    color: "#67e8f9",
    overlayKind: "room",
    interactive: true,
  });
}

function _createFanRotor(sceneNode, anchor) {
  var group = new THREE.Group();
  group.position.copy(anchor);
  group.userData.overlayKind = "fan-rotor";
  for (var i = 0; i < 4; i += 1) {
    var blade = new THREE.Mesh(
      new THREE.BoxGeometry(
        viewMetrics.markerSize * 2.1,
        viewMetrics.markerSize * 0.14,
        viewMetrics.markerSize * 0.5
      ),
      new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        emissive: new THREE.Color(0x164e63),
        emissiveIntensity: 0.4,
        transparent: true,
        opacity: 0.92,
        roughness: 0.24,
        metalness: 0.18,
      })
    );
    blade.rotation.x = Math.PI / 2;
    blade.rotation.y = (Math.PI / 2) * i;
    group.add(blade);
  }
  _registerNode(sceneNode, group, false);
  overlayRoot.add(group);
  return group;
}

function _louverAxis() {
  return viewMetrics.sideAxis === "x" ? "z" : "x";
}

function _createDamper(sceneNode, anchor, sideOffset) {
  var group = new THREE.Group();
  group.position.copy(anchor);
  group.position.add(_vectorWithAxis(viewMetrics.sideAxis, sideOffset || 0));
  group.userData.overlayKind = "damper";
  for (var index = -1; index <= 1; index += 1) {
    var louver = new THREE.Mesh(
      new THREE.BoxGeometry(
        viewMetrics.markerSize * 1.6,
        viewMetrics.markerSize * 0.08,
        viewMetrics.markerSize * 0.44
      ),
      new THREE.MeshStandardMaterial({
        color: 0x94a3b8,
        emissive: new THREE.Color(0x111827),
        emissiveIntensity: 0.12,
        roughness: 0.22,
        metalness: 0.18,
        transparent: true,
        opacity: 0.86,
      })
    );
    louver.position[_louverAxis()] = index * viewMetrics.markerSize * 0.28;
    group.add(louver);
  }
  _registerNode(sceneNode, group, false);
  overlayRoot.add(group);
  return group;
}

function _createPlume(sceneNode, anchor) {
  var group = new THREE.Group();
  group.position.copy(anchor);
  group.userData.overlayKind = "plume";
  group.userData.colorMaterials = [];
  var effectScale = viewMetrics.effectScale || 1;
  for (var i = 0; i < 5; i += 1) {
    var sphere = new THREE.Mesh(
      new THREE.SphereGeometry(viewMetrics.markerSize * effectScale * (0.36 + i * 0.08), 20, 20),
      new THREE.MeshBasicMaterial({
        color: 0x67e8f9,
        transparent: true,
        opacity: 0.14 - i * 0.018,
        depthWrite: false,
      })
    );
    sphere.position[viewMetrics.verticalAxis] = i * viewMetrics.markerSize * 0.85 * effectScale;
    group.userData.colorMaterials.push(sphere.material);
    group.add(sphere);
  }
  _registerNode(sceneNode, group, false);
  overlayRoot.add(group);
  return group;
}

function _createAuraRings(sceneNode, anchor, colorHex, scaleMultiplier, overlayKind) {
  var group = new THREE.Group();
  group.position.copy(anchor);
  group.userData.overlayKind = overlayKind || "effect";
  group.userData.colorMaterials = [];
  group.userData.glowMaterials = [];
  var effectScale = viewMetrics.effectScale || 1;
  for (var i = 0; i < 3; i += 1) {
    var ring = new THREE.Mesh(
      new THREE.TorusGeometry(
        viewMetrics.markerSize * effectScale * (1.05 + i * 0.28) * (scaleMultiplier || 1),
        viewMetrics.markerSize * 0.07,
        18,
        52
      ),
      new THREE.MeshStandardMaterial({
        color: colorHex,
        emissive: _colorFromHex(colorHex),
        emissiveIntensity: 0.28,
        roughness: 0.18,
        metalness: 0.04,
        transparent: true,
        opacity: 0.22 - i * 0.04,
        depthWrite: false,
      })
    );
    ring.rotation.x = Math.PI / 2;
    ring.position[viewMetrics.verticalAxis] = i * viewMetrics.markerSize * 0.18;
    group.userData.colorMaterials.push(ring.material);
    group.userData.glowMaterials.push(ring.material);
    group.add(ring);
  }
  _registerNode(sceneNode, group, false);
  overlayRoot.add(group);
  return group;
}

function _createDustField(sceneNode, anchor, scaleMultiplier) {
  var group = new THREE.Group();
  group.position.copy(anchor);
  group.userData.overlayKind = "dust";
  group.userData.colorMaterials = [];
  var effectScale = viewMetrics.effectScale || 1;

  for (var i = 0; i < 12; i += 1) {
    var mote = new THREE.Mesh(
      new THREE.SphereGeometry(viewMetrics.flowRadius * effectScale * (0.22 + (i % 3) * 0.08), 12, 12),
      new THREE.MeshBasicMaterial({
        color: 0xf8fafc,
        transparent: true,
        opacity: 0.08 + (i % 4) * 0.015,
        depthWrite: false,
      })
    );
    mote.position.set(
      (Math.random() - 0.5) * viewMetrics.markerSize * effectScale * 2.8 * (scaleMultiplier || 1),
      (Math.random() - 0.1) * viewMetrics.markerSize * effectScale * 1.6 * (scaleMultiplier || 1),
      (Math.random() - 0.5) * viewMetrics.markerSize * effectScale * 2.6 * (scaleMultiplier || 1)
    );
    mote.userData.phase = Math.random() * Math.PI * 2;
    mote.userData.basePosition = mote.position.clone();
    group.userData.colorMaterials.push(mote.material);
    group.add(mote);
  }

  _registerNode(sceneNode, group, false);
  overlayRoot.add(group);
  return group;
}

function _createFlowNode(sceneNode, points, colorHex) {
  var curve = new THREE.CatmullRomCurve3(points);
  var group = new THREE.Group();
  group.userData.overlayKind = "flow";
  group.userData.flowCurve = curve;
  group.userData.flowParticles = [];
  group.userData.flowIntensity = 0.6;

  var tube = new THREE.Mesh(
    new THREE.TubeGeometry(curve, 72, viewMetrics.flowRadius, 12, false),
    new THREE.MeshStandardMaterial({
      color: colorHex,
      emissive: _colorFromHex(colorHex),
      emissiveIntensity: 0.65,
      roughness: 0.16,
      metalness: 0.0,
      transparent: true,
      opacity: 0.48,
      depthWrite: false,
    })
  );
  group.add(tube);

  var auraTube = new THREE.Mesh(
    new THREE.TubeGeometry(curve, 48, viewMetrics.flowRadius * 1.8, 12, false),
    new THREE.MeshBasicMaterial({
      color: colorHex,
      transparent: true,
      opacity: 0.1,
      depthWrite: false,
    })
  );
  group.add(auraTube);

  // Плотная цепочка направленных меток-частиц вдоль curve. Это даёт
  // «течение» воздуха, интенсивность которого управляется
  // `flows.*.intensity` (см. _animateFlowNodes). 24 частицы дают
  // заметное визуальное различие между малым и большим расходом без
  // заметной нагрузки на GPU на performance_budget 30 fps.
  var particleCount = 24;
  for (var i = 0; i < particleCount; i += 1) {
    var particle = new THREE.Mesh(
      new THREE.SphereGeometry(viewMetrics.flowRadius * 0.58, 14, 14),
      new THREE.MeshBasicMaterial({
        color: colorHex,
        transparent: true,
        opacity: 0.82,
        depthWrite: false,
      })
    );
    particle.userData.flowOffset = i / particleCount;
    group.userData.flowParticles.push(particle);
    group.add(particle);
  }

  group.userData.colorMaterials = [tube.material, auraTube.material];
  group.userData.glowMaterials = [tube.material];
  group.userData.flowParticleMaterials = group.userData.flowParticles.map(function (particle) {
    return particle.material;
  });
  _registerNode(sceneNode, group, true);
  overlayRoot.add(group);
  return group;
}

function _activeRoomProfile() {
  var roomProfile = _profileBlock("room_zone");
  var descriptorProfile = currentRoomDescriptor && currentRoomDescriptor.room_profile
    ? currentRoomDescriptor.room_profile
    : {};
  return _roomVolumeProfile(
    Object.assign({}, roomProfile || {}, descriptorProfile || {}),
    currentRoomDescriptor
  );
}

function _buildSyntheticScene() {
  if (!viewMetrics) return;
  var anchorsProfile = _profileBlock("anchors");
  var sensorProfile = _profileBlock("sensors");
  var flowProfile = _profileBlock("flows");
  var damperProfile = _profileBlock("dampers");
  var effectsProfile = _profileBlock("effects");
  var roomZoneProfile = _activeRoomProfile();
  var anchors = {
    outdoor: _resolvePointFromSpec(anchorsProfile.outdoor, null, { long: 0.06, vertical: 0.72, side: -0.28 }),
    filter: _resolvePointFromSpec(anchorsProfile.filter, null, { long: 0.24, vertical: 0.74, side: -0.12 }),
    recuperator: _resolvePointFromSpec(anchorsProfile.recuperator, null, { long: 0.35, vertical: 0.74, side: -0.06 }),
    heater: _resolvePointFromSpec(anchorsProfile.heater, null, { long: 0.46, vertical: 0.74, side: 0.0 }),
    fan: _resolvePointFromSpec(anchorsProfile.fan, null, { long: 0.68, vertical: 0.74, side: 0.14 }),
    duct: _resolvePointFromSpec(anchorsProfile.duct, null, { long: 0.88, vertical: 0.72, side: 0.24 }),
    filter_fine: _resolvePointFromSpec(anchorsProfile.filter_fine, null, { long: 0.78, vertical: 0.72, side: 0.2 }),
    cooler: _resolvePointFromSpec(anchorsProfile.cooler, null, { long: 0.55, vertical: 0.56, side: -0.18 }),
    silencer: _resolvePointFromSpec(anchorsProfile.silencer, null, { long: 0.98, vertical: 0.68, side: 0.28 }),
    room: _resolvePointFromSpec(anchorsProfile.room, null, { long: 1.12, vertical: 0.36, side: 0.26 }),
    room_sensor: _resolvePointFromSpec(anchorsProfile.room_sensor, null, { long: 1.12, vertical: 0.58, side: 0.26 }),
  };
  if (roomModelRoot) {
    _applyRoomPlacement(roomModelRoot, anchors);
  }
  var roomCenter = _roomAnchorPoint("room.anchor.center", anchors.room);
  var roomInlet = _roomAnchorPoint(
    "room.anchor.inlet",
    _resolvePointFromSpec({ anchor: "room", vertical_delta: 0.12, side_delta: -0.08 }, anchors, { anchor: "room" })
  );
  var occupiedZone = _roomAnchorPoint(
    "room.anchor.occupied_zone",
    _resolvePointFromSpec({ anchor: "room", vertical_delta: 0.06 }, anchors, { anchor: "room" })
  );
  var roomTempPoint = _roomAnchorPoint(
    "room.sensor.temperature",
    _resolvePointFromSpec(sensorProfile.room_temp, anchors, { anchor: "room_sensor" })
  );
  var roomCo2Point = _roomAnchorPoint(
    "room.sensor.co2",
    roomCenter.clone().add(_vectorWithAxis(viewMetrics.sideAxis, viewMetrics.markerSize * 1.6))
  );
  var roomHumidityPoint = _roomAnchorPoint(
    "room.sensor.humidity",
    roomCenter.clone().add(_vectorWithAxis(viewMetrics.sideAxis, -viewMetrics.markerSize * 1.6))
  );
  var roomOccupancyPoint = _roomAnchorPoint(
    "room.sensor.occupancy",
    occupiedZone.clone().add(_vectorWithAxis(viewMetrics.verticalAxis, viewMetrics.markerSize * 0.8))
  );

  _createStageMarker("pvu.intake.outdoor_air", anchors.outdoor, { kind: "node", scale: 1.18, model: "intake" });
  _createStageMarker("pvu.filter.bank", anchors.filter, { kind: "node", scale: 1.14, model: "filter" });
  _createStageMarker("pvu.recuperator.core", anchors.recuperator, { kind: "node", scale: 1.06, model: "recuperator" });
  _createStageMarker("pvu.heater.coil", anchors.heater, { kind: "node", scale: 1.14, model: "heater" });
  _createStageMarker("pvu.fan.supply", anchors.fan, { kind: "node", scale: 1.14, model: "fan" });
  _createStageMarker("pvu.filter.fine", anchors.filter_fine, { kind: "node", scale: 1.02, model: "filter_fine" });
  _createStageMarker("pvu.cooler.coil", anchors.cooler, { kind: "node", scale: 1.02, model: "cooler" });
  _createStageMarker("pvu.silencer", anchors.silencer, { kind: "node", scale: 1.0, model: "silencer" });
  _createStageMarker("pvu.duct.supply", anchors.duct, { kind: "node", scale: 1.1, model: "duct" });
  _createStageMarker("building.room.supply_air", roomInlet, { kind: "node", scale: 1.0 });
  _createRoomZone("building.room.zone_a", roomCenter, roomZoneProfile);

  _createStageMarker(
    "pvu.sensors.outdoor_temp",
    _resolvePointFromSpec(sensorProfile.outdoor, anchors, { anchor: "outdoor", vertical_delta: 0.09 }),
    { kind: "sensor", scale: 1.02 }
  );
  _createStageMarker(
    "pvu.sensors.filter_pressure",
    _resolvePointFromSpec(sensorProfile.filter_pressure, anchors, { anchor: "filter", vertical_delta: 0.08 }),
    { kind: "sensor", scale: 0.98 }
  );
  _createStageMarker(
    "pvu.sensors.supply_temp",
    _resolvePointFromSpec(sensorProfile.supply_temp, anchors, { anchor: "heater", vertical_delta: 0.08 }),
    { kind: "sensor", scale: 0.98 }
  );
  _createStageMarker(
    "pvu.sensors.airflow",
    _resolvePointFromSpec(sensorProfile.airflow, anchors, { anchor: "duct", vertical_delta: 0.08 }),
    { kind: "sensor", scale: 0.98 }
  );
  _createStageMarker(
    "building.sensors.room_temp",
    roomTempPoint,
    { kind: "sensor", scale: 1.04 }
  );
  _registerSyntheticBinding("building.sensors.room_co2", "sensor_room_co2", "sensor");
  _createStageMarker("building.sensors.room_co2", roomCo2Point, { kind: "sensor", scale: 1.0 });
  _registerSyntheticBinding("building.sensors.room_humidity", "sensor_room_humidity", "sensor");
  _createStageMarker("building.sensors.room_humidity", roomHumidityPoint, { kind: "sensor", scale: 1.0 });
  _registerSyntheticBinding("building.sensors.room_occupancy", "sensor_room_occupancy", "sensor");
  _createStageMarker("building.sensors.room_occupancy", roomOccupancyPoint, { kind: "sensor", scale: 1.02 });

  _createFlowNode(
    "pvu.flow.outdoor_to_filter",
    _resolvePathSpecs(
      flowProfile.outdoor_to_filter,
      anchors,
      ["outdoor", { long: 0.12, vertical: 0.72, side: -0.24 }, "filter"]
    ),
    0x38bdf8
  );
  _createFlowNode(
    "pvu.flow.filter_to_heater",
    _resolvePathSpecs(
      flowProfile.filter_to_heater,
      anchors,
      ["filter", { long: 0.34, vertical: 0.72, side: -0.06 }, "heater"]
    ),
    0x14b8a6
  );
  _createFlowNode(
    "pvu.flow.heater_to_fan",
    _resolvePathSpecs(
      flowProfile.heater_to_fan,
      anchors,
      ["heater", { long: 0.56, vertical: 0.72, side: 0.08 }, "fan"]
    ),
    0xfb923c
  );
  _createFlowNode(
    "pvu.flow.fan_to_room",
    _resolvePathSpecs(
      flowProfile.fan_to_room,
      anchors,
      ["fan", "duct", { long: 0.98, vertical: 0.64, side: 0.28 }, { anchor: "room", vertical_delta: 0.04 }]
    ),
    0x22c55e
  );
  _createFlowNode(
    "building.flow.extract_context",
    Array.isArray(flowProfile.extract_context) && flowProfile.extract_context.length
      ? _resolvePathSpecs(
          flowProfile.extract_context,
          Object.assign({}, anchors, { room: roomCenter }),
          [
            { anchor: "room", vertical_delta: 0.04 },
            { anchor: "room", vertical_delta: 0.18, side_delta: -0.12 },
            { anchor: "room", vertical_delta: 0.34, side_delta: -0.28 },
          ]
        )
      : [
          roomCenter.clone(),
          roomCenter.clone().add(_vectorWithAxis(viewMetrics.verticalAxis, viewMetrics.markerSize * 1.6)),
          roomCenter.clone().add(_vectorWithAxis(viewMetrics.sideAxis, -viewMetrics.markerSize * 2.8)),
        ],
    0x94a3b8
  );
  _createFlowNode(
    "building.flow.room_supply_context",
    [anchors.duct, roomInlet, occupiedZone],
    0x7dd3fc
  );
  // Вытяжная ветвь контура рекуперации (замечание рецензента editing-2):
  // воздух из помещения проходит через пластинчатый рекуператор и
  // выбрасывается наружу. Сигналов у этих потоков нет (auxiliary_nodes),
  // поэтому они анимируются с интенсивностью по умолчанию.
  _createFlowNode(
    "building.flow.room_to_recuperator",
    _resolvePathSpecs(
      flowProfile.room_to_recuperator,
      Object.assign({}, anchors, { room: roomCenter }),
      [
        { anchor: "room", vertical_delta: 0.2, side_delta: -0.1 },
        { long: 0.72, vertical: 0.6, side: -0.2 },
        { anchor: "recuperator", vertical_delta: -0.04, side_delta: -0.04 },
      ]
    ),
    0x94a3b8
  );
  _createFlowNode(
    "pvu.flow.recuperator_to_exhaust",
    _resolvePathSpecs(
      flowProfile.recuperator_to_exhaust,
      anchors,
      [
        { anchor: "recuperator", vertical_delta: -0.06, side_delta: -0.08 },
        { long: 0.16, vertical: 0.62, side: -0.26 },
        { long: 0.04, vertical: 0.5, side: -0.3 },
      ]
    ),
    0x64748b
  );

  _createFanRotor(
    "pvu.fan.rotor",
    _resolvePointFromSpec({ anchor: "fan", vertical_delta: -0.03 }, anchors, { anchor: "fan" })
  );
  _createDamper(
    "pvu.damper.intake",
    _resolvePointFromSpec(damperProfile.intake, anchors, { anchor: "outdoor", vertical_delta: -0.03 }),
    0
  );
  _createDamper(
    "pvu.damper.living",
    _resolvePointFromSpec(damperProfile.living, anchors, { anchor: "duct", vertical_delta: -0.02 }),
    0
  );
  _createDamper(
    "pvu.damper.bedroom_north",
    _resolvePointFromSpec(
      Object.assign({}, damperProfile.bedroom_north || {}, { side_delta: 0 }),
      anchors,
      { anchor: "duct" }
    ),
    _normalizedDeltaByAxis(viewMetrics.sideAxis, _withDefault((damperProfile.bedroom_north || {}).side_delta, 0.08))
  );
  _createDamper(
    "pvu.damper.bedroom_south",
    _resolvePointFromSpec(
      Object.assign({}, damperProfile.bedroom_south || {}, { side_delta: 0 }),
      anchors,
      { anchor: "duct" }
    ),
    _normalizedDeltaByAxis(viewMetrics.sideAxis, _withDefault((damperProfile.bedroom_south || {}).side_delta, -0.08))
  );
  _createDamper(
    "pvu.damper.study",
    _resolvePointFromSpec(
      Object.assign({}, damperProfile.study || {}, { side_delta: 0 }),
      anchors,
      { anchor: "duct", vertical_delta: 0.04 }
    ),
    _normalizedDeltaByAxis(viewMetrics.sideAxis, _withDefault((damperProfile.study || {}).side_delta, 0.16))
  );
  _createDamper(
    "pvu.damper.kitchen",
    _resolvePointFromSpec(
      Object.assign({}, damperProfile.kitchen || {}, { side_delta: 0 }),
      anchors,
      { anchor: "duct", vertical_delta: -0.04 }
    ),
    _normalizedDeltaByAxis(viewMetrics.sideAxis, _withDefault((damperProfile.kitchen || {}).side_delta, -0.16))
  );
  _createPlume("pvu.flow.room_plumes", occupiedZone.clone());
  _createAuraRings(
    "pvu.effect.intake_aura",
    _resolvePointFromSpec(effectsProfile.intake_aura, anchors, { anchor: "outdoor" }),
    _themeColor("halo_color", DEFAULT_MODEL_ACCENT),
    _withDefault((effectsProfile.intake_aura || {}).scale, 1),
    "intake-aura"
  );
  _createDustField(
    "pvu.effect.filter_dust",
    _resolvePointFromSpec(effectsProfile.filter_dust, anchors, { anchor: "filter" }),
    _withDefault((effectsProfile.filter_dust || {}).scale, 1)
  );
  // Дополнительный маркер перепада давления ΔP на фильтре: полупрозрачное
  // красно-оранжевое halo-кольцо, видимое только при warning/alarm состоянии
  // sensor_filter_pressure. См. _animateFilterPressureCue.
  _createAuraRings(
    "pvu.effect.filter_pressure_cue",
    _resolvePointFromSpec(effectsProfile.filter_dust, anchors, { anchor: "filter" }),
    0xef4444,
    _withDefault((effectsProfile.filter_dust || {}).scale, 1) * 0.85,
    "filter-pressure-cue"
  );
  _createAuraRings(
    "pvu.effect.heater_field",
    _resolvePointFromSpec(effectsProfile.heater_field, anchors, { anchor: "heater" }),
    0xfb923c,
    _withDefault((effectsProfile.heater_field || {}).scale, 1),
    "heater-field"
  );
  _createAuraRings("room.effect.air_quality", roomCenter.clone(), 0xfacc15, 1.18, "room-air-quality");
  _createPlume("room.effect.humidity_cloud", roomHumidityPoint.clone());
  _createAuraRings("room.effect.occupancy_orbit", occupiedZone.clone(), 0x38bdf8, 0.96, "room-occupancy");
}

function _cameraTarget() {
  if (!viewMetrics) return new THREE.Vector3();
  var cameraProfile = (_profileBlock("camera") || {})[currentCameraPreset] || {};
  if (cameraProfile.target) {
    var anchors = _profileBlock("anchors");
    return _resolvePointFromSpec(cameraProfile.target, {
      outdoor: _resolvePointFromSpec(anchors.outdoor, null, { long: 0.06, vertical: 0.72, side: -0.28 }),
      filter: _resolvePointFromSpec(anchors.filter, null, { long: 0.24, vertical: 0.74, side: -0.12 }),
      heater: _resolvePointFromSpec(anchors.heater, null, { long: 0.46, vertical: 0.74, side: 0.0 }),
      fan: _resolvePointFromSpec(anchors.fan, null, { long: 0.68, vertical: 0.74, side: 0.14 }),
      duct: _resolvePointFromSpec(anchors.duct, null, { long: 0.88, vertical: 0.72, side: 0.24 }),
      room: _resolvePointFromSpec(anchors.room, null, { long: 1.12, vertical: 0.36, side: 0.26 }),
      room_sensor: _resolvePointFromSpec(anchors.room_sensor, null, { long: 1.12, vertical: 0.58, side: 0.26 }),
    });
  }
  return viewMetrics.center.clone().add(_vectorWithAxis(viewMetrics.verticalAxis, viewMetrics.maxDim * 0.18));
}

function _cameraPositionForPreset(presetName) {
  var preset = String(presetName || "hero");
  var profile = (_profileBlock("camera") || {})[preset] || {};
  var target = _cameraTarget();
  var longDir = _axisVector(viewMetrics.longAxis);
  var sideDir = _axisVector(viewMetrics.sideAxis);
  var upDir = _axisVector(viewMetrics.verticalAxis);
  var distance = viewMetrics.maxDim * _withDefault(profile.distance, 1.9);

  if (preset === "top") {
    return target.clone().add(upDir.multiplyScalar(distance * _withDefault(profile.up, 1.45)));
  }
  if (preset === "service") {
    return target
      .clone()
      .add(longDir.multiplyScalar(distance * _withDefault(profile.long, -0.95)))
      .add(sideDir.multiplyScalar(distance * _withDefault(profile.side, 0.42)))
      .add(upDir.multiplyScalar(distance * _withDefault(profile.up, 0.45)));
  }
  return target
    .clone()
    .add(longDir.multiplyScalar(distance * _withDefault(profile.long, 0.95)))
    .add(sideDir.multiplyScalar(distance * _withDefault(profile.side, -0.5)))
    .add(upDir.multiplyScalar(distance * _withDefault(profile.up, 0.4)));
}

function setCameraPreset(presetName) {
  currentCameraPreset = presetName || "hero";
  if (!camera || !controls || !viewMetrics) return false;
  var target = _cameraTarget();
  var position = _cameraPositionForPreset(currentCameraPreset);
  camera.position.copy(position);
  controls.target.copy(target);
  var activeProfile = (_profileBlock("camera") || {})[currentCameraPreset] || {};
  controls.minDistance = viewMetrics.maxDim * _withDefault(activeProfile.min_distance, 0.7);
  controls.maxDistance = viewMetrics.maxDim * _withDefault(activeProfile.max_distance, 14.0);
  controls.update();
  return true;
}

function _captureCameraState() {
  if (!camera || !controls) return null;
  return {
    position: camera.position.clone(),
    target: controls.target.clone(),
    zoom: camera.zoom,
  };
}

function _restoreCameraState(cameraState) {
  if (!cameraState || !camera || !controls) return;
  camera.position.copy(cameraState.position);
  controls.target.copy(cameraState.target);
  camera.zoom = cameraState.zoom;
  camera.updateProjectionMatrix();
  controls.update();
}

function _rebuildSyntheticScene(options) {
  var preserveCamera = options && options.preserveCamera === true;
  _hideInfoCard();
  hoveredObject = null;
  selectedObject = null;
  _clearOverlayRoot();
  nodeMap = {};
  interactiveObjects = [];
  if (!viewMetrics) return false;
  _buildSyntheticScene();
  setDisplayMode(currentDisplayMode, currentModelDescriptor || {});
  if (!preserveCamera) {
    setCameraPreset(currentCameraPreset);
  }
  if (currentSignals) {
    applySignals(currentSignals);
  }
  return true;
}

function setRoomTemplate(roomDescriptor) {
  currentRoomDescriptor = roomDescriptor || null;
  if (!isInitialized) return true;
  if (!modelRoot || !viewMetrics) return true;
  return _ensureActiveRoomModel();
}

function setScaleTuning(scaleTuning) {
  var nextTuning = _sanitizeScaleTuning(scaleTuning);
  if (!_scaleTuningChanged(nextTuning)) {
    return true;
  }
  currentScaleTuning = nextTuning;
  if (!isInitialized || !modelRoot) {
    return true;
  }
  var cameraState = _captureCameraState();
  _applyModelTransformTuning();
  viewMetrics = _computeViewMetrics(modelRoot);
  _rebuildSyntheticScene({ preserveCamera: true });
  if (!roomModelRoot && currentRoomDescriptor && currentRoomDescriptor.model_url) {
    _ensureActiveRoomModel({ preserveCamera: true }).then(function () {
      _restoreCameraState(cameraState);
    });
  }
  _restoreCameraState(cameraState);
  return true;
}

/**
 * Поднимается по parent-цепочке mesh до первого узла, имя которого попадает
 * в `_classifyAhuRole` (kind != "other"). Это нужно, потому что GLB после
 * экспорта из Blender может оставлять у самих Mesh пустые имена, а семантика
 * хранится у родительского Object3D (например, "pvu.fan.blade_1" — это Group,
 * а её child Mesh без имени).
 */
function _classifyMeshContext(mesh) {
  var current = mesh;
  while (current) {
    var role = _classifyAhuRole(current.name);
    if (role.kind !== "other") return role;
    if (current === modelRoot || current === roomModelRoot || current === scene) break;
    current = current.parent;
  }
  return { kind: "other", section: null };
}

function _applyMaterialForMode(material, base, role, mode, accentColor) {
  var sectionColor = role.section ? SECTION_PALETTE[role.section] : null;
  var isEnclosure = ENCLOSURE_KINDS[role.kind] === true;
  var isFlow = role.kind === "flow";

  if (mode === "xray") {
    if (isFlow) {
      // Потоки управляются applySignals/animateFlow, в xray не трогаем.
      material.transparent = base.transparent;
      material.opacity = base.opacity;
      material.depthWrite = base.depthWrite;
      material.color.copy(base.color);
      material.emissive.copy(base.emissive);
      material.emissiveIntensity = base.emissiveIntensity;
      material.roughness = base.roughness;
      material.metalness = base.metalness;
    } else if (role.kind === "enclosure_shell" || role.kind === "enclosure_door") {
      // Корпус и двери — почти невидимый контур, чтобы открыть внутренние секции.
      material.transparent = true;
      material.opacity = 0.05;
      material.depthWrite = false;
      material.color.copy(base.color).lerp(SECTION_PALETTE.enclosure, 0.45);
      material.emissive.setHex(0x000000);
      material.emissiveIntensity = 0;
      material.roughness = 0.55;
      material.metalness = 0.18;
    } else if (role.kind === "enclosure_handle" || role.kind === "base" || role.kind === "outdoor_stack") {
      material.transparent = true;
      material.opacity = 0.45;
      material.depthWrite = true;
      material.color.copy(base.color).lerp(SECTION_PALETTE.frame, 0.18);
      material.emissive.setHex(0x000000);
      material.emissiveIntensity = 0;
      material.roughness = base.roughness;
      material.metalness = base.metalness;
    } else if (role.kind === "building") {
      // Стены/полы помещения — едва заметные, чтобы не перекрывали ПВУ.
      material.transparent = true;
      material.opacity = 0.06;
      material.depthWrite = false;
      material.color.copy(base.color).lerp(new THREE.Color(0xe2e8f0), 0.5);
      material.emissive.setHex(0x000000);
      material.emissiveIntensity = 0;
      material.roughness = 0.95;
      material.metalness = 0;
    } else if (sectionColor) {
      // Внутренние секции ПВУ: яркие, с эмиссией цвета секции.
      material.transparent = base.transparent;
      material.opacity = Math.max(base.opacity, 0.94);
      material.depthWrite = true;
      material.color.copy(base.color).lerp(sectionColor, 0.55);
      material.emissive.copy(sectionColor).multiplyScalar(0.45);
      material.emissiveIntensity = 0.7;
      material.roughness = 0.32;
      material.metalness = 0.22;
    } else {
      material.transparent = true;
      material.opacity = Math.max(0.18, base.opacity * 0.32);
      material.depthWrite = false;
      material.color.copy(base.color).lerp(accentColor, 0.22);
      material.emissive.copy(accentColor).multiplyScalar(0.1);
      material.emissiveIntensity = 0.2;
      material.roughness = 0.4;
      material.metalness = 0.1;
    }
  } else if (mode === "schematic") {
    if (isFlow) {
      material.transparent = base.transparent;
      material.opacity = base.opacity;
      material.depthWrite = base.depthWrite;
      material.color.copy(base.color);
      material.emissive.copy(base.emissive);
      material.emissiveIntensity = base.emissiveIntensity;
      material.roughness = base.roughness;
      material.metalness = base.metalness;
    } else if (isEnclosure) {
      // Корпус превращается в едва видимый контур.
      material.transparent = true;
      material.opacity = 0.04;
      material.depthWrite = false;
      material.color.set(0xe2e8f0);
      material.emissive.setHex(0x000000);
      material.emissiveIntensity = 0;
      material.roughness = 0.95;
      material.metalness = 0;
    } else if (role.kind === "building") {
      material.transparent = true;
      material.opacity = 0.05;
      material.depthWrite = false;
      material.color.set(0xf1f5f9);
      material.emissive.setHex(0x000000);
      material.emissiveIntensity = 0;
      material.roughness = 0.98;
      material.metalness = 0;
    } else if (sectionColor) {
      // Внутренние секции отрисовываются плоским цветом по семантике.
      material.transparent = false;
      material.opacity = 1;
      material.depthWrite = true;
      material.color.copy(sectionColor);
      material.emissive.copy(sectionColor).multiplyScalar(0.18);
      material.emissiveIntensity = 0.28;
      material.roughness = 0.78;
      material.metalness = 0;
    } else {
      material.transparent = true;
      material.opacity = Math.max(0.16, base.opacity * 0.22);
      material.depthWrite = false;
      material.color.copy(base.color).lerp(new THREE.Color(0xe2e8f0), 0.6);
      material.emissive.setHex(0x000000);
      material.emissiveIntensity = 0;
      material.roughness = 0.95;
      material.metalness = 0;
    }
  } else {
    // studio: реалистичный вид с цветовой семантикой секций.
    material.transparent = base.transparent;
    material.opacity = base.opacity;
    material.depthWrite = base.depthWrite;
    if (sectionColor && !isEnclosure && !isFlow) {
      material.color.copy(base.color).lerp(sectionColor, 0.32);
      material.emissive.copy(sectionColor).multiplyScalar(0.05);
      material.emissiveIntensity = Math.max(base.emissiveIntensity, 0.08);
      material.roughness = Math.min(base.roughness, 0.6);
      material.metalness = Math.max(base.metalness, 0.18);
    } else if (isEnclosure) {
      material.color.copy(base.color).lerp(SECTION_PALETTE.enclosure, 0.18);
      material.emissive.copy(base.emissive);
      material.emissiveIntensity = Math.max(base.emissiveIntensity, 0.04);
      material.roughness = Math.min(base.roughness, 0.55);
      material.metalness = Math.max(base.metalness, 0.18);
    } else {
      material.color.copy(base.color).lerp(accentColor, 0.08);
      material.emissive.copy(base.emissive);
      material.emissiveIntensity = Math.max(base.emissiveIntensity, 0.04);
      material.roughness = Math.min(base.roughness, 0.62);
      material.metalness = Math.max(base.metalness, 0.16);
    }
  }
  material.needsUpdate = true;
}

function _applyDisplayModeToRoot(root, mode, accentColor) {
  if (!root) return;
  root.traverse(function (child) {
    if (!child.isMesh || !child.material) return;
    var role = _classifyMeshContext(child);
    _materialArray(child.material).forEach(function (material) {
      var base = _ensureModelMaterialState(material);
      _applyMaterialForMode(material, base, role, mode, accentColor);
    });
  });
}

function _applyDisplayModeToModel(mode, accent) {
  var accentColor = _colorFromHex(accent || DEFAULT_MODEL_ACCENT);
  _applyDisplayModeToRoot(modelRoot, mode, accentColor);
  _applyDisplayModeToRoot(roomModelRoot, mode, accentColor);
}

function _applyDisplayModeLighting(mode) {
  if (!ambientLight || !keyLight || !rimLight || !fillLight) return;
  if (mode === "xray") {
    // Равномерный мягкий свет, чтобы внутренние секции читались сквозь корпус.
    ambientLight.intensity = 1.45;
    keyLight.intensity = 1.05;
    rimLight.intensity = 1.4;
    fillLight.intensity = 0.45;
    if (renderer) renderer.toneMappingExposure = 1.18;
  } else if (mode === "schematic") {
    // Плоский образовательный вид без сильной светотени.
    ambientLight.intensity = 1.6;
    keyLight.intensity = 0.55;
    rimLight.intensity = 0.4;
    fillLight.intensity = 0.4;
    if (renderer) renderer.toneMappingExposure = 1.0;
  } else {
    // studio: контрастная светотень, металл/стекло читаемы.
    ambientLight.intensity = 0.95;
    keyLight.intensity = 2.15;
    rimLight.intensity = 1.05;
    fillLight.intensity = 0.65;
    if (renderer) renderer.toneMappingExposure = 1.05;
  }
}

function _applyDisplayModeToOverlays(mode, accent) {
  var accentColor = _colorFromHex(accent || DEFAULT_MODEL_ACCENT);
  Object.keys(nodeMap).forEach(function (key) {
    var node = nodeMap[key];
    if (!node || node.userData.__displayProcessed) return;
    node.userData.__displayProcessed = true;
    var colorMaterials = node.userData.colorMaterials || [];
    colorMaterials.forEach(function (material) {
      if (!material || !material.color) return;
      if (mode === "schematic") {
        material.opacity = Math.min(0.95, (material.opacity || 1) * 1.08);
        material.color.lerp(accentColor, 0.25);
      } else if (mode === "xray") {
        material.opacity = Math.min(0.9, Math.max(material.opacity || 1, 0.34));
        material.color.lerp(accentColor, 0.18);
      }
    });
  });
  Object.keys(nodeMap).forEach(function (key) {
    if (nodeMap[key]) nodeMap[key].userData.__displayProcessed = false;
  });
}

function setDisplayMode(mode, options) {
  currentDisplayMode = mode || "studio";
  var accent =
    options && options.accent
      ? options.accent
      : (currentModelDescriptor && currentModelDescriptor.accent) || DEFAULT_MODEL_ACCENT;
  _applyDisplayModeToModel(currentDisplayMode, accent);
  _applyDisplayModeToOverlays(currentDisplayMode, accent);
  _applyDisplayModeLighting(currentDisplayMode);
  return true;
}

function _applyNodeSignal(node, signal, kind, colorHex) {
  if (!node) return;
  node.userData.pvuSignal = signal;
  node.userData.pvuBinding = bindingByVisualId[signal.visual_id] || null;
  node.userData.pvuState = signal.state || "normal";

  var statusColor = _colorFromHex(colorHex);
  var emissiveStrength = signal.state === "alarm" ? 1.45 : signal.state === "warning" ? 0.72 : 0.48;

  // Температурный цвет: только для ВП с числовым °C value. Если получилось
  // извлечь температуру — используем её для color materials; status
  // остаётся через emissive glow (alarm/warning остаются читаемыми).
  var isTempVisual = TEMPERATURE_VISUAL_IDS[signal.visual_id] === true;
  var tempColor = null;
  if (isTempVisual) {
    var celsius = _parseNumericValue(signal && signal.value);
    if (celsius === null && signal && signal.detail) {
      // У supply_duct value = airflow, а температура притока в detail
      // («Приток 19.0 °C»). Пробуем detail как fallback.
      celsius = _parseNumericValue(signal.detail);
    }
    tempColor = _temperatureColor(celsius);
  }

  var materialColor = tempColor || statusColor;
  node.userData.pvuTempColor = tempColor;

  // Давление на фильтре: если state != normal, усиливаем pulse через
  // дополнительный emissiveIntensity boost. Это используется в
  // _animateFilterPressureCue для гало-кольца вокруг фильтра.
  if (FILTER_PRESSURE_VISUAL_IDS[signal.visual_id] === true) {
    node.userData.pvuPressureIntensity = typeof signal.intensity === "number"
      ? signal.intensity
      : (signal.state === "alarm" ? 0.95 : signal.state === "warning" ? 0.65 : 0.28);
  }

  var materials = node.userData.colorMaterials || [];
  var glowMaterials = node.userData.glowMaterials || [];
  materials.forEach(function (material) {
    if (material.color) material.color.copy(materialColor);
    if (typeof material.opacity === "number") {
      if (kind === "flow") {
        material.opacity = signal.active === false ? 0.08 : 0.24 + (signal.intensity || 0.55) * 0.62;
      } else if (node.userData.overlayKind === "room") {
        material.opacity = 0.14 + (signal.state === "alarm" ? 0.08 : signal.state === "warning" ? 0.04 : 0.0);
      }
    }
  });
  glowMaterials.forEach(function (material) {
    if (material.emissive) {
      material.emissive.copy(statusColor);
      material.emissiveIntensity = emissiveStrength;
    }
  });

  if (kind === "flow") {
    node.visible = signal.active !== false;
    node.userData.flowIntensity = signal.intensity || 0.55;
  }
}

function _applySceneMood(signals) {
  if (!signals || !ambientLight || !floorGlow) return;
  var atmosphereProfile = _scenarioAtmosphereProfile(signals);
  var roomAirQuality = signals.room_sensors && signals.room_sensors.sensor_room_air_quality;
  var effectiveStatus = signals.status;
  if (roomAirQuality && roomAirQuality.state === "alarm") {
    effectiveStatus = "alarm";
  } else if (
    roomAirQuality &&
    roomAirQuality.state === "warning" &&
    effectiveStatus !== "alarm"
  ) {
    effectiveStatus = "warning";
  }
  var outdoorTemp = _parseNumericValue(
    signals.nodes && signals.nodes.outdoor_air && signals.nodes.outdoor_air.value
  );
  var blend = outdoorTemp === null ? 0.5 : _clamp((outdoorTemp + 30) / 70, 0, 1);
  var mood = COLD_COLOR.clone().lerp(WARM_COLOR, blend);
  if (effectiveStatus === "alarm") {
    mood.lerp(new THREE.Color(0xef4444), 0.62);
  } else if (effectiveStatus === "warning") {
    mood.lerp(new THREE.Color(0xf59e0b), 0.35);
  } else {
    mood.lerp(NEUTRAL_COLOR, 0.18);
  }

  mood.lerp(_colorFromHex(atmosphereProfile.moodColor), atmosphereProfile.moodBlend);

  floorGlow.material.color.copy(mood);
  floorGlow.material.opacity = (effectiveStatus === "alarm" ? 0.34 : 0.2) + atmosphereProfile.auraPulse * 0.25;
  ambientLight.color.copy(new THREE.Color(0xe8f6ff).lerp(mood, 0.12));
  keyLight.color.copy(new THREE.Color(0xffffff).lerp(mood, 0.16));
  rimLight.color.copy(mood);
  fillLight.color.copy(new THREE.Color(0xfef3c7).lerp(mood, 0.25));
  if (floorBase && floorBase.material && floorBase.material.color) {
    floorBase.material.color.copy(_colorFromHex(atmosphereProfile.floorColor));
  }
  if (farRing && farRing.material && farRing.material.color) {
    farRing.material.color.copy(_colorFromHex(atmosphereProfile.farRingColor));
  }
  if (stageBackdrop && stageBackdrop.material) {
    stageBackdrop.material.opacity = atmosphereProfile.backdropOpacity;
    if (stageBackdrop.material.color) {
      stageBackdrop.material.color.copy(_colorFromHex(atmosphereProfile.floorColor));
    }
  }
  if (atmosphereParticles && atmosphereParticles.material) {
    atmosphereParticles.material.color.copy(_colorFromHex(atmosphereProfile.particleColor));
    atmosphereParticles.material.opacity = atmosphereProfile.particleOpacity;
    atmosphereParticles.material.size = atmosphereProfile.particleSize;
  }
  if (seasonAura && seasonAura.material) {
    seasonAura.material.color.copy(_colorFromHex(atmosphereProfile.auraColor));
    seasonAura.material.opacity = 0.06 + atmosphereProfile.auraPulse * 0.35;
  }
  renderer.toneMappingExposure = effectiveStatus === "alarm" ? 1.15 : 1.05;
}

function applySignals(signals) {
  if (!signals || !isInitialized) return;
  currentSignals = signals;
  _applySceneMood(signals);

  var statusColors = sceneMeta.status_colors || STATUS_COLORS;
  ["nodes", "sensors", "flows", "room_sensors"].forEach(function (section) {
    var items = signals[section] || {};
    Object.keys(items).forEach(function (visualId) {
      var signal = items[visualId];
      var binding = bindingByVisualId[visualId];
      if (!binding) return;
      var node = _getNode(binding.scene_node);
      if (!node) return;
      var colorHex = _statusToColor(signal.state, statusColors);
      _applyNodeSignal(node, signal, binding.kind, colorHex);
    });
  });
}

function _resolveSignalPath(path) {
  if (!currentSignals || !path) return null;
  return path.split(".").reduce(function (acc, key) {
    if (acc && Object.prototype.hasOwnProperty.call(acc, key)) {
      return acc[key];
    }
    return null;
  }, currentSignals);
}

function _animateFlowNodes(time) {
  // Early exit: не сканируем nodeMap когда визуализация потока выключена
  if (!flowFieldEnabled) return;
  Object.keys(nodeMap).forEach(function (key) {
    var node = nodeMap[key];
    if (!node || node.userData.__flowAnimated || node.userData.overlayKind !== "flow") return;
    node.userData.__flowAnimated = true;
    // Расширенный диапазон intensity: отображаем разницу между
    // сниженным расходом (dirty filter, 0.2-0.4) и нормой (0.8+).
    var intensity = _clamp(node.userData.flowIntensity || 0.55, 0.08, 1.2);
    var pulse = 0.5 + 0.5 * Math.sin(time * (1.0 + intensity * 3.2));
    var materials = node.userData.colorMaterials || [];
    materials.forEach(function (material) {
      if (!material) return;
      if (typeof material.opacity === "number") {
        material.opacity = 0.14 + intensity * 0.66 + pulse * 0.1;
      }
      if (material.emissiveIntensity !== undefined) {
        material.emissiveIntensity = 0.34 + intensity * 1.05 + pulse * 0.18;
      }
    });
    // Скорость частиц сильнее зависит от intensity: при малом расходе
    // частицы почти стоят (имитация перекрытого тракта), при полной
    // нагрузке — быстрый поток.
    var progressSpeed = 0.06 + intensity * 0.48;
    var particleOpacity = 0.22 + intensity * 0.68;
    var particleScale = 0.7 + intensity * 0.55 + pulse * 0.25;
    (node.userData.flowParticles || []).forEach(function (particle) {
      var progress = (time * progressSpeed + particle.userData.flowOffset) % 1;
      var point = node.userData.flowCurve.getPointAt(progress);
      particle.position.copy(point);
      particle.scale.setScalar(particleScale);
      particle.material.opacity = particleOpacity;
    });
  });
  Object.keys(nodeMap).forEach(function (key) {
    if (nodeMap[key]) nodeMap[key].userData.__flowAnimated = false;
  });
}

function _animateFan(dt) {
  var fanRule = sceneMeta.animation_rules && sceneMeta.animation_rules.fan_rotation;
  if (!fanRule) return;
  var fanNode = _getNode(fanRule.target_node);
  if (!fanNode) return;

  // Initialize fan animation state
  if (!fanNode.userData.fanState) {
    fanNode.userData.fanState = {
      currentRpm: 0,
      targetRpm: 0,
      blurIntensity: 0,
    };
  }

  var speedSignal = _resolveSignalPath(fanRule.speed_signal);
  var speed = typeof speedSignal === "number" ? speedSignal : 0.55;
  var targetRpm = (fanRule.max_rpm || 3.0) * _clamp(speed, 0.1, 1.2);

  var state = fanNode.userData.fanState;
  state.targetRpm = targetRpm;

  // Smooth acceleration/deceleration with easing
  var acceleration = fanRule.acceleration || 2.5; // RPM per second
  var rpmDiff = state.targetRpm - state.currentRpm;
  var maxChange = acceleration * dt;

  if (Math.abs(rpmDiff) < maxChange) {
    state.currentRpm = state.targetRpm;
  } else {
    // Ease-in-out curve for smooth acceleration
    var easing = 1 - Math.pow(1 - Math.min(Math.abs(rpmDiff) / targetRpm, 1), 2);
    state.currentRpm += Math.sign(rpmDiff) * maxChange * (0.5 + easing * 0.5);
  }

  // Apply rotation
  var axis = fanRule.axis.toLowerCase();
  fanNode.rotation[axis] += dt * state.currentRpm * Math.PI * 2;

  // Motion blur effect at high speeds
  var blurThreshold = (fanRule.max_rpm || 3.0) * 0.6;
  if (state.currentRpm > blurThreshold) {
    var blurFactor = (state.currentRpm - blurThreshold) / (fanRule.max_rpm - blurThreshold);
    state.blurIntensity = _clamp(blurFactor, 0, 1);
  } else {
    state.blurIntensity = 0;
  }

  // Apply blur effect to fan materials
  if (state.blurIntensity > 0.1 && fanNode.userData.fanBlades) {
    fanNode.userData.fanBlades.forEach(function (blade) {
      if (blade.material && blade.material.opacity !== undefined) {
        // Reduce opacity for motion blur effect
        var baseOpacity = blade.userData.baseOpacity || 1.0;
        blade.material.opacity = baseOpacity * (1 - state.blurIntensity * 0.4);
        blade.material.transparent = true;
      }
    });
  } else if (fanNode.userData.fanBlades) {
    // Restore full opacity when not blurring
    fanNode.userData.fanBlades.forEach(function (blade) {
      if (blade.material && blade.material.opacity !== undefined) {
        var baseOpacity = blade.userData.baseOpacity || 1.0;
        blade.material.opacity = baseOpacity;
      }
    });
  }
}

function _animateDamperPosition(dt) {
  var rule = sceneMeta.animation_rules && sceneMeta.animation_rules.damper_position;
  if (!rule) return;
  var openness = _resolveSignalPath(rule.driver_signal);
  var mixTarget = typeof openness === "number" ? _clamp(openness, 0, 1) : 0.72;
  var closed = THREE.MathUtils.degToRad(rule.closed_angle_deg || -58);
  var opened = THREE.MathUtils.degToRad(rule.open_angle_deg || 8);
  var axisName = (rule.axis || "z").toLowerCase();
  (rule.target_nodes || []).forEach(function (nodeName) {
    var node = _getNode(nodeName);
    if (!node || !node.children.length) return;
    if (!node.userData.baseRotation) {
      node.userData.baseRotation = node.rotation.clone();
    }
    var baseRotation = node.userData.baseRotation[axisName];
    var target = baseRotation + THREE.MathUtils.lerp(closed, opened, mixTarget);
    node.rotation[axisName] = THREE.MathUtils.lerp(
      node.rotation[axisName],
      target,
      Math.min(1, dt * (rule.response || 3.2))
    );
  });
}

function _animateSensorPulse(time) {
  var rule = sceneMeta.animation_rules && sceneMeta.animation_rules.sensor_pulse;
  if (!rule) return;
  var pulse =
    0.5 + 0.5 * Math.sin(time * (rule.pulse_speed || 1.6) * Math.PI * 2);
  (rule.target_nodes || []).forEach(function (nodeName) {
    var node = _getNode(nodeName);
    if (!node || node.userData.overlayKind !== "sensor") return;
    if (!node.userData.baseScale) {
      node.userData.baseScale = node.scale.clone();
    }
    var scale = THREE.MathUtils.lerp(
      rule.min_scale || 0.94,
      rule.max_scale || 1.14,
      pulse
    );
    node.scale.copy(node.userData.baseScale).multiplyScalar(scale);
    (node.userData.glowMaterials || []).forEach(function (material) {
      if (material.emissiveIntensity !== undefined) {
        material.emissiveIntensity =
          (rule.emissive_strength || 1.0) * (0.35 + pulse * 0.85);
      }
    });
  });
}

function _animatePlumePulse(time) {
  var rule = sceneMeta.animation_rules && sceneMeta.animation_rules.plume_pulse;
  if (!rule) return;
  var driver = _resolveSignalPath(rule.driver_signal);
  var intensity = typeof driver === "number" ? _clamp(driver, 0.2, 1.0) : 0.65;
  var pulse =
    0.5 + 0.5 * Math.sin(time * (rule.pulse_speed || 1.15) * Math.PI * 2);
  (rule.target_nodes || []).forEach(function (nodeName) {
    var node = _getNode(nodeName);
    if (!node || node.userData.overlayKind !== "plume") return;
    if (!node.userData.baseScale) {
      node.userData.baseScale = node.scale.clone();
    }
    var scale = THREE.MathUtils.lerp(
      rule.min_scale || 0.88,
      rule.max_scale || 1.22,
      pulse * intensity
    );
    node.scale.copy(node.userData.baseScale).multiplyScalar(scale);
    (node.userData.colorMaterials || []).forEach(function (material, index) {
      material.opacity =
        (rule.min_opacity || 0.12) +
        (rule.max_opacity || 0.48) *
          pulse *
          intensity *
          (1 - index * 0.08);
    });
  });
}

function _animateProcessEffects(time) {
  if (!currentSignals) return;
  var atmosphereProfile = _scenarioAtmosphereProfile(currentSignals);
  var heaterBoost = atmosphereProfile.heaterBoost || 1;
  var dustBoost = atmosphereProfile.dustBoost || 1;

  var outdoorTemp = _parseNumericValue(
    currentSignals.nodes &&
      currentSignals.nodes.outdoor_air &&
      currentSignals.nodes.outdoor_air.value
  );
  var heaterPower = _parseNumericValue(
    currentSignals.nodes &&
      currentSignals.nodes.heater_coil &&
      currentSignals.nodes.heater_coil.value
  );
  var filterLoad = _parseNumericValue(
    currentSignals.nodes &&
      currentSignals.nodes.filter_bank &&
      currentSignals.nodes.filter_bank.detail
  );

  var intakeAura = _getNode("pvu.effect.intake_aura");
  if (intakeAura) {
    var thermalBlend = outdoorTemp === null ? 0.5 : _clamp((outdoorTemp + 30) / 70, 0, 1);
    var thermalColor = COLD_COLOR.clone().lerp(WARM_COLOR, thermalBlend);
    var pulse = 0.5 + 0.5 * Math.sin(time * (2.4 + atmosphereProfile.auraPulse * 2));
    intakeAura.rotation[viewMetrics.verticalAxis] += 0.004 + atmosphereProfile.auraSpin * 0.02;
    intakeAura.scale.setScalar(0.9 + pulse * (0.14 + atmosphereProfile.auraPulse * 0.12));
    (intakeAura.userData.colorMaterials || []).forEach(function (material, index) {
      if (material.color) material.color.copy(thermalColor);
      if (material.emissive) material.emissive.copy(thermalColor);
      material.opacity = 0.08 + pulse * 0.08 * (1 - index * 0.16);
      if (material.emissiveIntensity !== undefined) {
        material.emissiveIntensity = 0.2 + pulse * 0.45;
      }
    });
  }

  var dustField = _getNode("pvu.effect.filter_dust");
  if (dustField) {
    var contamination = filterLoad === null ? 0.2 : _clamp(filterLoad / 100, 0, 1);
    contamination = _clamp(contamination * dustBoost, 0, 1.4);
    dustField.rotation[viewMetrics.verticalAxis] += 0.002 + contamination * 0.01;
    dustField.children.forEach(function (child, index) {
      if (!child.material) return;
      var drift = time * (0.8 + index * 0.07) + (child.userData.phase || 0);
      if (child.userData.basePosition) {
        child.position.copy(child.userData.basePosition);
        child.position[viewMetrics.verticalAxis] += Math.sin(drift) * viewMetrics.markerSize * 0.08;
      }
      child.material.opacity = 0.02 + contamination * 0.28;
      if (child.material.color) {
        child.material.color.copy(new THREE.Color(0xf8fafc).lerp(new THREE.Color(0xfacc15), contamination * 0.55));
      }
    });
  }

  // Маркер ΔP на фильтре. Пульсация растёт при повышении давления:
  // normal → практически невидим, warning → заметное оранжевое пульсирующее
  // кольцо, alarm → яркое красное кольцо с быстрым pulse.
  var pressureCue = _getNode("pvu.effect.filter_pressure_cue");
  var filterBankNode = _getNode("pvu.filter.bank");
  var sensorPressureNode = _getNode("pvu.sensors.filter_pressure");
  if (pressureCue) {
    var rawIntensity = 0;
    if (sensorPressureNode && typeof sensorPressureNode.userData.pvuPressureIntensity === "number") {
      rawIntensity = sensorPressureNode.userData.pvuPressureIntensity;
    } else if (filterBankNode && typeof filterBankNode.userData.pvuPressureIntensity === "number") {
      rawIntensity = filterBankNode.userData.pvuPressureIntensity;
    }
    var filterState = sensorPressureNode ? sensorPressureNode.userData.pvuState : (
      filterBankNode ? filterBankNode.userData.pvuState : "normal"
    );
    var cueColor = filterState === "alarm"
      ? new THREE.Color(0xef4444)
      : filterState === "warning"
        ? new THREE.Color(0xf59e0b)
        : new THREE.Color(0xfacc15);
    var visibleLevel = filterState === "alarm" ? 0.95 : filterState === "warning" ? 0.55 : 0.0;
    var cuePulse = 0.5 + 0.5 * Math.sin(time * (2.2 + rawIntensity * 3.0));
    pressureCue.visible = visibleLevel > 0.05;
    pressureCue.scale.setScalar(0.88 + cuePulse * (0.22 + visibleLevel * 0.18));
    pressureCue.rotation[viewMetrics.verticalAxis] += 0.012;
    (pressureCue.userData.colorMaterials || []).forEach(function (material, index) {
      if (!material) return;
      if (material.color) material.color.copy(cueColor);
      if (material.emissive) material.emissive.copy(cueColor);
      material.opacity = (0.06 + cuePulse * 0.22) * visibleLevel * (1 - index * 0.18);
      if (material.emissiveIntensity !== undefined) {
        material.emissiveIntensity = 0.45 + cuePulse * 0.9 * visibleLevel;
      }
    });
  }

  var heaterField = _getNode("pvu.effect.heater_field");
  if (heaterField) {
    var heatRatio = heaterPower === null ? 0.25 : _clamp(heaterPower / 40, 0, 1.2);
    heatRatio = _clamp(heatRatio * heaterBoost, 0, 1.35);
    var heatPulse = 0.5 + 0.5 * Math.sin(time * (2.0 + heatRatio * 1.4));
    heaterField.scale.setScalar(0.9 + heatRatio * 0.32 + heatPulse * 0.08);
    heaterField.rotation[viewMetrics.verticalAxis] -= 0.01;
    (heaterField.userData.colorMaterials || []).forEach(function (material, index) {
      if (material.color) {
        material.color.copy(new THREE.Color(0xfb923c).lerp(new THREE.Color(0xfacc15), Math.min(heatRatio, 1)));
      }
      material.opacity = 0.08 + heatRatio * 0.18 + heatPulse * 0.06 * (1 - index * 0.18);
      if (material.emissive) {
        material.emissive.copy(new THREE.Color(0xfb923c));
      }
      if (material.emissiveIntensity !== undefined) {
        material.emissiveIntensity = 0.18 + heatRatio * 0.82 + heatPulse * 0.18;
      }
    });
  }
}

function _animateRoomEffects(time) {
  if (!currentSignals) return;
  var atmosphereProfile = _scenarioAtmosphereProfile(currentSignals);
  var humidityBoost = atmosphereProfile.humidityBoost || 1;
  var roomSensors = currentSignals.room_sensors || {};
  var co2Value = _parseNumericValue(
    roomSensors.sensor_room_co2 && roomSensors.sensor_room_co2.value
  );
  var humidityValue = _parseNumericValue(
    roomSensors.sensor_room_humidity && roomSensors.sensor_room_humidity.value
  );
  var occupancyPeople = _parseNumericValue(
    roomSensors.sensor_room_occupancy && roomSensors.sensor_room_occupancy.value
  );
  var occupancyRatio = currentRoomDescriptor && currentRoomDescriptor.design_occupancy_people
    ? (occupancyPeople || 0) / currentRoomDescriptor.design_occupancy_people
    : 0.35;
  var supplySignal = currentSignals.flows && currentSignals.flows.flow_fan_to_room;

  var roomSupplyFlow = _getNode("building.flow.room_supply_context");
  if (roomSupplyFlow) {
    roomSupplyFlow.visible = !supplySignal || supplySignal.active !== false;
    roomSupplyFlow.userData.flowIntensity = _clamp(
      (supplySignal && supplySignal.intensity) || 0.58,
      0.15,
      1.12
    );
  }

  var airQualityAura = _getNode("room.effect.air_quality");
  if (airQualityAura) {
    var co2Ratio = co2Value === null ? 0.18 : _clamp((co2Value - 450) / 850, 0.08, 1.0);
    var pulse = 0.5 + 0.5 * Math.sin(time * (1.1 + co2Ratio * 2.4));
    var airColor = new THREE.Color(0xfacc15).lerp(new THREE.Color(0xef4444), co2Ratio);
    airQualityAura.scale.setScalar(0.88 + co2Ratio * 0.44 + pulse * 0.08);
    airQualityAura.rotation[viewMetrics.verticalAxis] += 0.008 + co2Ratio * 0.012;
    (airQualityAura.userData.colorMaterials || []).forEach(function (material, index) {
      if (material.color) material.color.copy(airColor);
      if (material.emissive) material.emissive.copy(airColor);
      material.opacity = 0.08 + co2Ratio * 0.22 + pulse * 0.05 * (1 - index * 0.12);
      if (material.emissiveIntensity !== undefined) {
        material.emissiveIntensity = 0.18 + co2Ratio * 0.74 + pulse * 0.12;
      }
    });
  }

  var humidityCloud = _getNode("room.effect.humidity_cloud");
  if (humidityCloud) {
    var humidityRatio = humidityValue === null ? 0.22 : _clamp((humidityValue - 35) / 30, 0.08, 1.0);
    humidityRatio = _clamp(humidityRatio * humidityBoost, 0.08, 1.2);
    var humidityPulse = 0.5 + 0.5 * Math.sin(time * (0.9 + humidityRatio * 1.4));
    humidityCloud.scale.setScalar(0.9 + humidityRatio * 0.3 + humidityPulse * 0.1);
    (humidityCloud.userData.colorMaterials || []).forEach(function (material, index) {
      if (material.color) {
        material.color.copy(new THREE.Color(0x67e8f9).lerp(new THREE.Color(0x0ea5e9), humidityRatio));
      }
      material.opacity = 0.08 + humidityRatio * 0.18 + humidityPulse * 0.05 * (1 - index * 0.16);
    });
  }

  var occupancyOrbit = _getNode("room.effect.occupancy_orbit");
  if (occupancyOrbit) {
    var crowdRatio = _clamp(occupancyRatio || 0.0, 0.05, 1.25);
    var occupancyPulse = 0.5 + 0.5 * Math.sin(time * (1.4 + crowdRatio * 1.8));
    occupancyOrbit.scale.setScalar(0.82 + crowdRatio * 0.34 + occupancyPulse * 0.06);
    occupancyOrbit.rotation[viewMetrics.verticalAxis] -= 0.006 + crowdRatio * 0.012;
    (occupancyOrbit.userData.colorMaterials || []).forEach(function (material, index) {
      if (material.color) {
        material.color.copy(new THREE.Color(0x38bdf8).lerp(new THREE.Color(0x06b6d4), crowdRatio));
      }
      if (material.emissive) {
        material.emissive.copy(new THREE.Color(0x38bdf8));
      }
      material.opacity = 0.08 + crowdRatio * 0.18 + occupancyPulse * 0.04 * (1 - index * 0.1);
      if (material.emissiveIntensity !== undefined) {
        material.emissiveIntensity = 0.12 + crowdRatio * 0.5;
      }
    });
  }
}

function _animateSeasonalEnvironment(time) {
  if (!currentSignals || !atmosphereParticles || !atmosphereParticles.geometry) {
    return;
  }
  var profile = _scenarioAtmosphereProfile(currentSignals);
  var positions = atmosphereParticles.geometry.getAttribute("position");
  if (!positions) {
    return;
  }

  var mode = profile.particleMode || "ambient";
  var speed = profile.particleSpeed || 0.45;
  for (var i = 0; i < atmosphereParticleMotion.length; i += 1) {
    var motion = atmosphereParticleMotion[i];
    var ix = i * 3;
    var wobble = Math.sin(time * speed * motion.sway + motion.phase);
    var drift = Math.cos(time * speed * 0.7 + motion.phase) * 0.4;
    var x = motion.baseX + wobble * 0.45;
    var z = motion.baseZ + drift * 0.35;
    var y = motion.baseY;

    if (mode === "snow") {
      motion.currentY -= speed * 0.07 * motion.drift;
      if (motion.currentY < 0.35) {
        motion.currentY = 8.4 + Math.random() * 2.2;
      }
      y = motion.currentY;
      x += Math.sin(time * 0.8 + motion.phase) * 0.65;
      z += Math.cos(time * 0.72 + motion.phase) * 0.48;
    } else if (mode === "haze") {
      y = motion.baseY * 0.45 + 0.4 + Math.sin(time * speed * 0.45 + motion.phase) * 0.24;
      x += Math.cos(time * 0.35 + motion.phase) * 0.28;
      z += Math.sin(time * 0.38 + motion.phase) * 0.24;
    } else if (mode === "turbulence") {
      y = motion.baseY * 0.64 + 0.6 + Math.sin(time * speed * 1.4 + motion.phase) * 0.58;
      x += Math.sin(time * 1.8 + motion.phase) * 0.82;
      z += Math.cos(time * 1.55 + motion.phase) * 0.74;
    } else {
      y = motion.baseY + Math.sin(time * speed + motion.phase) * 0.28;
    }

    positions.array[ix] = x;
    positions.array[ix + 1] = y;
    positions.array[ix + 2] = z;
  }
  positions.needsUpdate = true;

  if (seasonAura) {
    seasonAura.rotation.z = time * (0.02 + profile.auraSpin * 0.25);
    seasonAura.scale.setScalar(0.96 + Math.sin(time * (0.8 + profile.auraPulse * 1.6)) * profile.auraPulse);
  }
}

function _animateAlarmFlash(time) {
  Object.keys(nodeMap).forEach(function (key) {
    var node = nodeMap[key];
    if (!node || node.userData.__alarmAnimated) return;
    node.userData.__alarmAnimated = true;
    var signal = node.userData.pvuSignal;
    if (!signal) return;
    var glow = node.userData.glowMaterials || [];
    if (signal.state === "alarm") {
      var flashHex = Math.sin(time * 10) > 0 ? ALARM_FLASH_A : ALARM_FLASH_B;
      glow.forEach(function (material) {
        if (material.emissive) {
          material.emissive.setHex(flashHex);
          material.emissiveIntensity = 1.55;
        }
      });
    } else if (signal.state === "warning") {
      glow.forEach(function (material) {
        if (material.emissive) {
          material.emissive.setHex(_statusToColor("warning", STATUS_COLORS));
          material.emissiveIntensity = 0.86;
        }
      });
    }
  });
  Object.keys(nodeMap).forEach(function (key) {
    if (nodeMap[key]) nodeMap[key].userData.__alarmAnimated = false;
  });
}

// Константы производительности
var TARGET_FPS = 30;
var FRAME_INTERVAL_MS = 1000 / TARGET_FPS;

// Статистика последнего отрисованного кадра. renderer.info.autoReset выключен:
// composer сбрасывал бы счётчики на каждом пассе, снаружи был бы виден только
// fullscreen-треугольник OutputPass. Сбрасываем вручную раз за кадр.
var lastFrameStats = { triangles: 0, drawCalls: 0 };

function _startAnimation() {
  if (animationId !== null) return;
  var lastFrameTime = 0;
  function loop(timestamp) {
    animationId = requestAnimationFrame(loop);
    // Кеп 30 FPS — пропускаем кадр если интервал не вышел
    if (timestamp - lastFrameTime < FRAME_INTERVAL_MS) return;
    lastFrameTime = timestamp;
    if (renderer) renderer.info.reset();

    var dt = Math.min(clock.getDelta(), 0.1);  // clamp для предотвращения спирали смерти
    var time = clock.getElapsedTime();
    if (controls) controls.update();
    _animateFan(dt);
    _animateDamperPosition(dt);
    _animateFlowNodes(time);
    _animateSensorPulse(time);
    _animatePlumePulse(time);
    _animateProcessEffects(time);
    _animateRoomEffects(time);
    _animateSeasonalEnvironment(time);
    _animateAlarmFlash(time);
    _updateHeatmapAnimation();
    _updateLOD();
    _updateFlowFieldAnimation(dt);
    if (floorGlow) {
      floorGlow.rotation.z = time * 0.045;
    }

    // Sync cameras in comparison mode when enabled
    if (comparisonMode && comparisonSyncCameras) {
      _syncCameras();
    }

    // Render: split-screen mode or normal mode
    if (comparisonMode) {
      _renderSplitScreen();
    } else {
      // Используем composer для рендеринга с post-processing эффектами
      if (composer) {
        composer.render();
      } else {
        renderer.render(scene, camera);
      }
    }
    if (renderer) {
      lastFrameStats.triangles = renderer.info.render.triangles;
      lastFrameStats.drawCalls = renderer.info.render.calls;
    }

    _updateLabels();
    // Overlay callouts обновляются в главном цикле вместо отдельного RAF
    if (window.concept03Overlay && window.concept03Overlay.requestOverlayUpdate) {
      window.concept03Overlay.requestOverlayUpdate();
    }
  }
  requestAnimationFrame(loop);
}

/**
 * Рендеринг в split-screen режиме.
 * @private
 */
function _renderSplitScreen() {
  if (!renderer || !camera || !scene) return;

  const width = renderer.domElement.width;
  const height = renderer.domElement.height;

  // Enable scissor test for viewport clipping
  renderer.setScissorTest(true);
  renderer.autoClear = false;
  renderer.clear();

  if (comparisonOrientation === "vertical") {
    // Vertical split (left/right)
    const leftWidth = Math.floor(width * comparisonSplit);
    const rightWidth = width - leftWidth;

    // Render left viewport ("before" state - main scene)
    renderer.setViewport(0, 0, leftWidth, height);
    renderer.setScissor(0, 0, leftWidth, height);
    camera.aspect = leftWidth / height;
    camera.updateProjectionMatrix();

    if (composer) {
      composer.render();
    } else {
      renderer.render(scene, camera);
    }

    // Render right viewport ("after" state - comparison scene)
    if (comparisonSceneAfter) {
      renderer.setViewport(leftWidth, 0, rightWidth, height);
      renderer.setScissor(leftWidth, 0, rightWidth, height);

      // Use synced camera or separate camera
      const activeCamera = comparisonSyncCameras ? camera : (comparisonCameraAfter || camera);
      activeCamera.aspect = rightWidth / height;
      activeCamera.updateProjectionMatrix();

      // Render "after" scene (no composer for comparison scene to keep it simple)
      renderer.render(comparisonSceneAfter, activeCamera);
    }

    // Draw divider line
    _drawSplitDivider(leftWidth, 0, 2, height);
  } else {
    // Horizontal split (top/bottom)
    const topHeight = Math.floor(height * comparisonSplit);
    const bottomHeight = height - topHeight;

    // Render top viewport ("before" state - main scene)
    renderer.setViewport(0, bottomHeight, width, topHeight);
    renderer.setScissor(0, bottomHeight, width, topHeight);
    camera.aspect = width / topHeight;
    camera.updateProjectionMatrix();

    if (composer) {
      composer.render();
    } else {
      renderer.render(scene, camera);
    }

    // Render bottom viewport ("after" state - comparison scene)
    if (comparisonSceneAfter) {
      renderer.setViewport(0, 0, width, bottomHeight);
      renderer.setScissor(0, 0, width, bottomHeight);

      // Use synced camera or separate camera
      const activeCamera = comparisonSyncCameras ? camera : (comparisonCameraAfter || camera);
      activeCamera.aspect = width / bottomHeight;
      activeCamera.updateProjectionMatrix();

      // Render "after" scene
      renderer.render(comparisonSceneAfter, activeCamera);
    }

    // Draw divider line
    _drawSplitDivider(0, bottomHeight, width, 2);
  }

  // Restore full viewport
  renderer.setScissorTest(false);
  renderer.autoClear = true;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

/**
 * Нарисовать линию-разделитель между viewport.
 * @private
 */
function _drawSplitDivider(x, y, w, h) {
  if (!renderer) return;

  // Create or update divider overlay
  let divider = document.getElementById('pvu3d-comparison-divider');
  if (!divider) {
    divider = document.createElement('div');
    divider.id = 'pvu3d-comparison-divider';
    divider.style.position = 'absolute';
    divider.style.backgroundColor = 'rgba(255, 255, 255, 0.3)';
    divider.style.pointerEvents = 'none';
    divider.style.zIndex = '1000';
    divider.style.boxShadow = '0 0 8px rgba(255, 255, 255, 0.5)';
    renderer.domElement.parentElement.appendChild(divider);
  }

  // Update divider position and size
  const canvas = renderer.domElement;
  const rect = canvas.getBoundingClientRect();
  divider.style.left = x + 'px';
  divider.style.top = y + 'px';
  divider.style.width = w + 'px';
  divider.style.height = h + 'px';
  divider.style.display = 'block';
}

/**
 * Создать или обновить labels для comparison mode.
 * @private
 */
function _updateComparisonLabels() {
  if (!comparisonMode || !renderer) {
    // Remove labels if comparison mode is off
    const beforeLabel = document.getElementById('pvu3d-comparison-label-before');
    const afterLabel = document.getElementById('pvu3d-comparison-label-after');
    if (beforeLabel) beforeLabel.remove();
    if (afterLabel) afterLabel.remove();
    return;
  }

  const canvas = renderer.domElement;
  const width = canvas.width;
  const height = canvas.height;

  // Create or update "Before" label
  let beforeLabel = document.getElementById('pvu3d-comparison-label-before');
  if (!beforeLabel) {
    beforeLabel = document.createElement('div');
    beforeLabel.id = 'pvu3d-comparison-label-before';
    beforeLabel.style.position = 'absolute';
    beforeLabel.style.padding = '8px 16px';
    beforeLabel.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    beforeLabel.style.color = 'white';
    beforeLabel.style.fontSize = '14px';
    beforeLabel.style.fontWeight = 'bold';
    beforeLabel.style.borderRadius = '4px';
    beforeLabel.style.pointerEvents = 'none';
    beforeLabel.style.zIndex = '1001';
    beforeLabel.style.fontFamily = 'system-ui, -apple-system, sans-serif';
    canvas.parentElement.appendChild(beforeLabel);
  }

  // Create or update "After" label
  let afterLabel = document.getElementById('pvu3d-comparison-label-after');
  if (!afterLabel) {
    afterLabel = document.createElement('div');
    afterLabel.id = 'pvu3d-comparison-label-after';
    afterLabel.style.position = 'absolute';
    afterLabel.style.padding = '8px 16px';
    afterLabel.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    afterLabel.style.color = 'white';
    afterLabel.style.fontSize = '14px';
    afterLabel.style.fontWeight = 'bold';
    afterLabel.style.borderRadius = '4px';
    afterLabel.style.pointerEvents = 'none';
    afterLabel.style.zIndex = '1001';
    afterLabel.style.fontFamily = 'system-ui, -apple-system, sans-serif';
    canvas.parentElement.appendChild(afterLabel);
  }

  // Update label text
  const beforeText = comparisonBeforeData ? comparisonBeforeData.display_label : 'До';
  const afterText = comparisonAfterData ? comparisonAfterData.display_label : 'После';
  beforeLabel.textContent = beforeText;
  afterLabel.textContent = afterText;

  // Position labels based on orientation
  if (comparisonOrientation === 'vertical') {
    const leftWidth = Math.floor(width * comparisonSplit);
    beforeLabel.style.left = '16px';
    beforeLabel.style.top = '16px';
    afterLabel.style.left = (leftWidth + 16) + 'px';
    afterLabel.style.top = '16px';
  } else {
    const topHeight = Math.floor(height * comparisonSplit);
    beforeLabel.style.left = '16px';
    beforeLabel.style.top = '16px';
    afterLabel.style.left = '16px';
    afterLabel.style.top = (topHeight + 16) + 'px';
  }

  beforeLabel.style.display = 'block';
  afterLabel.style.display = 'block';
}

function _stopAnimation() {
  if (animationId !== null) {
    cancelAnimationFrame(animationId);
    animationId = null;
  }
}

function _findInteractiveOwner(object) {
  var current = object;
  while (current) {
    if (current.userData && current.userData.pvuSignal) return current;
    if (current.userData && current.userData.interactiveOwner) {
      return current.userData.interactiveOwner;
    }
    current = current.parent;
  }
  return null;
}

function _setNodeEmissive(node, hex, intensity) {
  if (!node) return;
  (node.userData.glowMaterials || []).forEach(function (material) {
    if (material.emissive) {
      material.emissive.setHex(hex);
      material.emissiveIntensity = intensity;
    }
  });
}

function _onMouseMove(event) {
  if (!renderer || !camera) return;
  var rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  var intersects = raycaster.intersectObjects(interactiveObjects, true);

  if (hoveredObject && hoveredObject !== selectedObject) {
    var signal = hoveredObject.userData && hoveredObject.userData.pvuSignal;
    _setNodeEmissive(
      hoveredObject,
      signal ? _statusToColor(signal.state, STATUS_COLORS) : STATUS_COLORS.inactive,
      signal && signal.state === "alarm" ? 1.2 : 0.66
    );
    hoveredObject = null;
  }

  if (intersects.length > 0) {
    var owner = _findInteractiveOwner(intersects[0].object);
    if (owner && owner !== selectedObject) {
      hoveredObject = owner;
      _setNodeEmissive(owner, EMISSIVE_HOVER, 1.0);
      _showInfoCard(owner, event.clientX, event.clientY);
      renderer.domElement.style.cursor = "pointer";
      return;
    }
  }

  renderer.domElement.style.cursor = "default";
  if (!selectedObject) _hideInfoCard();
}

function _onClick(event) {
  if (!renderer || !camera) return;
  var rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);

  // Режим измерения: добавляем точки и создаём линии/углы
  if (measurementMode) {
    var intersects = raycaster.intersectObjects(scene.children, true);
    if (intersects.length > 0) {
      var point = intersects[0].point;

      if (measurementType === "angle") {
        _addAnglePoint(point);
      } else {
        _createMeasurementPoint(point);

        // Если есть предыдущая точка, создаём линию
        if (measurementPoints.length >= 2) {
          var p1 = measurementPoints[measurementPoints.length - 2];
          var p2 = measurementPoints[measurementPoints.length - 1];
          var distance = p1.position.distanceTo(p2.position);
          _createMeasurementLine(p1, p2, distance);
        }
        _persistMeasurements();
      }
    }
    return;
  }

  // Обычный режим: выбор объектов
  var intersects = raycaster.intersectObjects(interactiveObjects, true);

  if (selectedObject) {
    var previousSignal = selectedObject.userData && selectedObject.userData.pvuSignal;
    _setNodeEmissive(
      selectedObject,
      previousSignal ? _statusToColor(previousSignal.state, STATUS_COLORS) : STATUS_COLORS.inactive,
      previousSignal && previousSignal.state === "alarm" ? 1.15 : 0.66
    );
    selectedObject = null;
  }

  if (!intersects.length) {
    _hideInfoCard();
    return;
  }

  selectedObject = _findInteractiveOwner(intersects[0].object);
  if (!selectedObject) return;
  _setNodeEmissive(selectedObject, EMISSIVE_SELECTED, 1.2);
  _showInfoCard(selectedObject, event.clientX, event.clientY);
}

function _activateModelEntry(entry) {
  if (!entry || !entry.root) {
    return false;
  }
  _clearLoadedModel();
  _clearLoadedRoom();
  modelRoot = entry.root;
  if (scene && modelRoot.parent !== scene) {
    scene.add(modelRoot);
  }
  modelRoot.visible = true;
  _applyModelTransformTuning();
  viewMetrics = _computeViewMetrics(modelRoot);
  _applyThemeToEnvironment();
  _buildSyntheticScene();
  _ensureActiveRoomModel();
  setDisplayMode(currentDisplayMode, currentModelDescriptor || {});
  setCameraPreset(currentCameraPreset);
  if (currentSignals) {
    applySignals(currentSignals);
  }
  _removeOverlay();
  _startAnimation();
  return true;
}

function _activateRoomEntry(entry) {
  if (!entry || !entry.root) {
    return false;
  }
  _clearLoadedRoom();
  roomModelRoot = entry.root;
  if (scene && roomModelRoot.parent !== scene) {
    scene.add(roomModelRoot);
  }
  roomModelRoot.visible = true;
  return true;
}

function _cacheRoomEntry(modelUrl, roomDescriptor, showProgress) {
  var roomKey = _roomDescriptorKey(roomDescriptor);
  if (cachedRoomEntries[roomKey]) {
    return Promise.resolve(cachedRoomEntries[roomKey]);
  }
  if (pendingRoomEntries[roomKey]) {
    return pendingRoomEntries[roomKey];
  }

  pendingRoomEntries[roomKey] = new Promise(function (resolve, reject) {
    if (!sharedLoader) {
      sharedLoader = _createGltfLoader();
    }
    sharedLoader.load(
      modelUrl,
      function (gltf) {
        try {
          var entry = {
            key: roomKey,
            descriptor: roomDescriptor || null,
            root: _normalizeRoomModel(gltf.scene, roomDescriptor),
          };
          entry.root.visible = false;
          if (scene) {
            scene.add(entry.root);
          }
          cachedRoomEntries[roomKey] = entry;
          delete pendingRoomEntries[roomKey];
          resolve(entry);
        } catch (err) {
          delete pendingRoomEntries[roomKey];
          reject(err);
        }
      },
      function (progress) {
        if (!showProgress) {
          return;
        }
        if (progress.total > 0) {
          var percent = Math.round((progress.loaded / progress.total) * 100);
          _updateLoading("Загрузка room-модели: " + percent + "%");
        }
      },
      function (error) {
        delete pendingRoomEntries[roomKey];
        reject(error);
      }
    );
  });

  return pendingRoomEntries[roomKey];
}

function _ensureActiveRoomModel(options) {
  if (!currentRoomDescriptor || !currentRoomDescriptor.model_url || !viewMetrics) {
    _clearLoadedRoom();
    if (modelRoot && viewMetrics) {
      _rebuildSyntheticScene(options);
    }
    return Promise.resolve(null);
  }

  return _cacheRoomEntry(
    currentRoomDescriptor.model_url,
    currentRoomDescriptor,
    false
  ).then(function (entry) {
    _activateRoomEntry(entry);
    _rebuildSyntheticScene(options);
    return entry;
  }).catch(function (error) {
    console.warn("[PVU3D] room model load failed", error);
    return null;
  });
}

function _cacheModelEntry(modelUrl, modelDescriptor, showProgress) {
  var modelKey = _descriptorKey(modelDescriptor, modelUrl);
  if (cachedModelEntries[modelKey]) {
    return Promise.resolve(cachedModelEntries[modelKey]);
  }
  if (pendingModelEntries[modelKey]) {
    return pendingModelEntries[modelKey];
  }

  pendingModelEntries[modelKey] = new Promise(function (resolve, reject) {
    if (!sharedLoader) {
      sharedLoader = _createGltfLoader();
    }
    sharedLoader.load(
      modelUrl,
      function (gltf) {
        try {
          var entry = {
            key: modelKey,
            descriptor: modelDescriptor || null,
            root: _normalizeLoadedModel(
              gltf.scene,
              (modelDescriptor && modelDescriptor.profile) || {},
              modelDescriptor
            ),
          };
          entry.root.visible = false;
          if (scene) {
            scene.add(entry.root);
          }
          entry.viewMetrics = _computeViewMetrics(entry.root);
          cachedModelEntries[modelKey] = entry;
          delete pendingModelEntries[modelKey];
          resolve(entry);
        } catch (err) {
          delete pendingModelEntries[modelKey];
          reject(err);
        }
      },
      function (progress) {
        if (!showProgress) {
          return;
        }
        if (progress.total > 0) {
          var percent = Math.round((progress.loaded / progress.total) * 100);
          _updateLoading("Загрузка 3D-модели: " + percent + "%");
        } else {
          _updateLoading("Загрузка 3D-модели…");
        }
      },
      function (error) {
        delete pendingModelEntries[modelKey];
        reject(error);
      }
    );
  });

  return pendingModelEntries[modelKey];
}

function prefetchModel(modelUrl, modelDescriptor) {
  return _cacheModelEntry(modelUrl, modelDescriptor, false).catch(function (error) {
    console.warn("[PVU3D] prefetchModel failed", error);
    throw error;
  });
}

function loadModel(modelUrl, bindings, modelDescriptor) {
  if (!isInitialized) {
    return Promise.reject(new Error("Viewer is not initialized"));
  }
  currentModelDescriptor = modelDescriptor || null;
  currentSceneProfile = (modelDescriptor && modelDescriptor.profile) || {};
  bindingMap = {};
  bindingByVisualId = {};
  (bindings || []).forEach(function (binding) {
    bindingMap[binding.scene_node] = binding;
    bindingMap[_normalizeSceneNodeId(binding.scene_node)] = binding;
    bindingByVisualId[binding.visual_id] = binding;
  });
  var modelKey = _descriptorKey(modelDescriptor, modelUrl);
  if (cachedModelEntries[modelKey]) {
    _showLoading("Подготовка сцены…");
    _activateModelEntry(cachedModelEntries[modelKey]);
    return Promise.resolve();
  }

  _showLoading("Загрузка 3D-модели…");
  return _cacheModelEntry(modelUrl, modelDescriptor, true)
    .then(function (entry) {
      _activateModelEntry(entry);
    })
    .catch(function (error) {
      console.error("[PVU3D] loadModel failed", error);
      _showError("Не удалось загрузить GLB-модель: " + (error.message || error));
      throw error;
    });
}

function dispose() {
  _stopAnimation();
  if (renderer && renderer.domElement) {
    renderer.domElement.removeEventListener("mousemove", _onMouseMove);
    renderer.domElement.removeEventListener("click", _onClick);
    renderer.domElement.removeEventListener("webglcontextlost", _onContextLost);
    renderer.domElement.removeEventListener("webglcontextrestored", _onContextRestored);
  }
  window.removeEventListener("resize", _onResize);
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  _clearLoadedModel();
  _clearLoadedRoom();
  _disposeCachedModels();
  _disposeCachedRooms();
  _disposeComparisonSceneAfter();
  if (scene) {
    scene.remove(environmentRoot);
    scene.remove(atmosphereRoot);
    _disposeObject(environmentRoot);
    _disposeObject(atmosphereRoot);
    scene.environment = null;
  }
  if (environmentTexture) {
    environmentTexture.dispose();
    environmentTexture = null;
  }
  if (pmremGenerator) {
    pmremGenerator.dispose();
    pmremGenerator = null;
  }
  shadowCatcher = null;
  if (ssaoPass) {
    if (typeof ssaoPass.dispose === "function") {
      ssaoPass.dispose();
    }
    ssaoPass = null;
  }
  if (controls) {
    controls.dispose();
    controls = null;
  }
  if (renderer) {
    renderer.dispose();
    if (renderer.domElement && renderer.domElement.parentNode) {
      renderer.domElement.parentNode.removeChild(renderer.domElement);
    }
  }
  if (infoCard && infoCard.parentNode) {
    infoCard.parentNode.removeChild(infoCard);
  }
  _removeLabelLayer();
  _removeLegendOverlay();
  renderer = null;
  scene = null;
  camera = null;
  clock = null;
  overlayRoot = null;
  environmentRoot = null;
  atmosphereRoot = null;
  atmosphereParticles = null;
  atmosphereParticleMotion = [];
  floorBase = null;
  farRing = null;
  stageBackdrop = null;
  seasonAura = null;
  floorGlow = null;
  ambientLight = null;
  keyLight = null;
  rimLight = null;
  fillLight = null;
  nodeMap = {};
  bindingMap = {};
  bindingByVisualId = {};
  interactiveObjects = [];
  hoveredObject = null;
  selectedObject = null;
  currentSignals = null;
  currentModelDescriptor = null;
  currentSceneProfile = null;
  currentRoomDescriptor = null;
  roomModelRoot = null;
  viewMetrics = null;
  infoCard = null;
  generatedTextureCache = {};
  sharedLoader = null;
  isInitialized = false;
  _removeOverlay();
}

function _projectNode(nodeName) {
  if (!camera || !container) return null;
  var node = _getNode(nodeName);
  if (!node) return null;
  var target = new THREE.Vector3();
  node.getWorldPosition(target);
  var projected = target.project(camera);
  return {
    name: nodeName,
    x: ((projected.x + 1) / 2) * container.clientWidth,
    y: ((-projected.y + 1) / 2) * container.clientHeight,
  };
}

function captureViews(requestedViews, options) {
  if (!renderer || !scene || !camera || !controls) {
    return Promise.reject(new Error("viewer is not initialized"));
  }
  var views = Array.isArray(requestedViews) && requestedViews.length
    ? requestedViews
    : [{ preset: currentCameraPreset || "hero", label: "Current view" }];
  var previousPreset = currentCameraPreset;
  var previousCamera = _captureCameraState();
  var captures = [];
  try {
    views.forEach(function (view) {
      var preset = typeof view === "string" ? view : view.preset;
      preset = preset || currentCameraPreset || "hero";
      setCameraPreset(preset);
      controls.update();
      // Используем composer если доступен
      if (composer) {
        composer.render();
      } else {
        renderer.render(scene, camera);
      }
      captures.push({
        preset: preset,
        label: typeof view === "string" ? preset : (view.label || preset),
        capturedAt: new Date().toISOString(),
        mimeType: (options && options.mimeType) || "image/png",
        width: renderer.domElement.width,
        height: renderer.domElement.height,
        camera: camera.position.toArray(),
        target: controls.target.toArray(),
        dataUrl: renderer.domElement.toDataURL((options && options.mimeType) || "image/png"),
      });
    });
  } finally {
    currentCameraPreset = previousPreset || currentCameraPreset;
    _restoreCameraState(previousCamera);
    if (composer) {
      composer.render();
    } else {
      renderer.render(scene, camera);
    }
  }
  return Promise.resolve({
    schemaVersion: "pvu-3d-capture.v1",
    generatedAt: new Date().toISOString(),
    captures: captures,
  });
}

function setBloomEnabled(enabled) {
  if (!bloomPass) return false;
  bloomPass.enabled = enabled === true;
  return true;
}

function setBloomParams(params) {
  if (!bloomPass) return false;
  if (params.strength !== undefined) {
    bloomPass.strength = _clamp(params.strength, 0, 3);
  }
  if (params.radius !== undefined) {
    bloomPass.radius = _clamp(params.radius, 0, 1);
  }
  if (params.threshold !== undefined) {
    bloomPass.threshold = _clamp(params.threshold, 0, 1);
  }
  return true;
}

function getBloomParams() {
  if (!bloomPass) return null;
  return {
    enabled: bloomPass.enabled,
    strength: bloomPass.strength,
    radius: bloomPass.radius,
    threshold: bloomPass.threshold,
  };
}

function setSSAOEnabled(enabled) {
  if (!ssaoPass) return false;
  ssaoPass.enabled = enabled === true;
  return true;
}

function setSSAOParams(params) {
  if (!ssaoPass || !params) return false;
  if (params.kernelRadius !== undefined) {
    ssaoPass.kernelRadius = _clamp(params.kernelRadius, 0, 4);
  }
  if (params.minDistance !== undefined) {
    ssaoPass.minDistance = _clamp(params.minDistance, 0, 0.1);
  }
  if (params.maxDistance !== undefined) {
    ssaoPass.maxDistance = _clamp(params.maxDistance, 0, 1);
  }
  return true;
}

function getSSAOParams() {
  if (!ssaoPass) return null;
  return {
    enabled: ssaoPass.enabled,
    kernelRadius: ssaoPass.kernelRadius,
    minDistance: ssaoPass.minDistance,
    maxDistance: ssaoPass.maxDistance,
  };
}

window.pvu3d = {
  init: init,
  loadModel: loadModel,
  prefetchModel: prefetchModel,
  applySignals: applySignals,
  setDisplayMode: setDisplayMode,
  setCameraPreset: setCameraPreset,
  captureViews: captureViews,
  setRoomTemplate: setRoomTemplate,
  setScaleTuning: setScaleTuning,
  setBloomEnabled: setBloomEnabled,
  setBloomParams: setBloomParams,
  getBloomParams: getBloomParams,
  setSSAOEnabled: setSSAOEnabled,
  setSSAOParams: setSSAOParams,
  getSSAOParams: getSSAOParams,
  setMeasurementMode: setMeasurementMode,
  setMeasurementType: setMeasurementType,
  getMeasurements: getMeasurements,
  getMeasurementAngles: getMeasurementAngles,
  getAllMeasurements: getAllMeasurements,
  clearMeasurements: clearMeasurements,
  saveMeasurementsToSession: saveMeasurementsToSession,
  loadMeasurementsFromSession: loadMeasurementsFromSession,
  restoreMeasurementsFromSession: restoreMeasurementsFromSession,
  exportMeasurements: exportMeasurements,
  captureScreenshot: captureScreenshot,
  downloadScreenshot: downloadScreenshot,
  setHeatmapMode: setHeatmapMode,
  updateHeatmapData: updateHeatmapData,
  getHeatmapData: getHeatmapData,
  setClippingMode: setClippingMode,
  addClippingPlane: addClippingPlane,
  updateClippingPlane: updateClippingPlane,
  removeClippingPlane: removeClippingPlane,
  getClippingPlanes: getClippingPlanes,
  clearClippingPlanes: clearClippingPlanes,
  applyClippingPreset: applyClippingPreset,
  setLODMode: setLODMode,
  getLODStats: getLODStats,
  applyLODPreset: applyLODPreset,
  loadFlowFieldData: loadFlowFieldData,
  setFlowFieldMode: setFlowFieldMode,
  getFlowFieldStats: getFlowFieldStats,
  loadComparisonData: loadComparisonData,
  setComparisonMode: setComparisonMode,
  getComparisonStats: getComparisonStats,
  updateComparisonDiffMode: updateComparisonDiffMode,
  dispose: dispose,
  isInitialized: function () { return isInitialized; },
  hasFallback: function () { return window.__pvu3d_fallback === true; },
  clearFallback: function () { window.__pvu3d_fallback = false; },
  getDebugState: function () {
    var modelMetrics = null;
    if (modelRoot) {
      var modelBox = new THREE.Box3().setFromObject(modelRoot);
      if (!modelBox.isEmpty()) {
        var modelSize = modelBox.getSize(new THREE.Vector3());
        var modelCenter = modelBox.getCenter(new THREE.Vector3());
        modelMetrics = {
          size: modelSize.toArray(),
          center: modelCenter.toArray(),
          scale: modelRoot.scale.toArray(),
          box: {
            min: modelBox.min.toArray(),
            max: modelBox.max.toArray(),
          },
        };
      }
    }

    var roomMetrics = null;
    if (roomModelRoot) {
      var roomBox = new THREE.Box3().setFromObject(roomModelRoot);
      if (!roomBox.isEmpty()) {
        var roomSize = roomBox.getSize(new THREE.Vector3());
        var roomCenter = roomBox.getCenter(new THREE.Vector3());
        roomMetrics = {
          size: roomSize.toArray(),
          center: roomCenter.toArray(),
          scale: roomModelRoot.scale.toArray(),
          box: {
            min: roomBox.min.toArray(),
            max: roomBox.max.toArray(),
          },
          placementRuntime: roomModelRoot.userData
            ? roomModelRoot.userData.placementRuntime || null
            : null,
          separation: _roomPlacementRuntimeMetrics(),
        };
      }
    }
    return {
      camera: camera ? camera.position.toArray() : null,
      target: controls ? controls.target.toArray() : null,
      displayMode: currentDisplayMode,
      cameraPreset: currentCameraPreset,
      activeModel: currentModelDescriptor,
      activeRoom: currentRoomDescriptor,
      scaleTuning: Object.assign({}, currentScaleTuning),
      modelMetrics: modelMetrics,
      roomMetrics: roomMetrics,
      viewMetrics: viewMetrics
        ? {
            center: viewMetrics.center.toArray(),
            size: viewMetrics.size.toArray(),
            longAxis: viewMetrics.longAxis,
            sideAxis: viewMetrics.sideAxis,
            verticalAxis: viewMetrics.verticalAxis,
            markerSize: viewMetrics.markerSize,
            flowRadius: viewMetrics.flowRadius,
            connectorScale: viewMetrics.connectorScale,
            effectScale: viewMetrics.effectScale,
          }
        : null,
      seasonalProfile: _scenarioAtmosphereProfile(currentSignals || {}).id,
      nodeNames: Object.keys(nodeMap).sort(),
      rendering: {
        shadowsEnabled: shadowsEnabled,
        shadowMapEnabled: renderer ? renderer.shadowMap.enabled : null,
        keyLightCastsShadow: keyLight ? keyLight.castShadow === true : null,
        environmentApplied: scene ? scene.environment !== null && scene.environment !== undefined : null,
        toneMappingExposure: renderer ? renderer.toneMappingExposure : null,
        shadowCatcher: shadowCatcher !== null,
        ssaoSupported: ssaoPass !== null,
        ssaoEnabled: ssaoPass ? ssaoPass.enabled : null,
        ssaoKernelRadius: ssaoPass ? ssaoPass.kernelRadius : null,
        rendererInfo: renderer
          ? {
              triangles: lastFrameStats.triangles,
              drawCalls: lastFrameStats.drawCalls,
              geometries: renderer.info.memory.geometries,
              textures: renderer.info.memory.textures,
            }
          : null,
      },
    };
  },
  getProjectedNode: function (nodeName) {
    return _projectNode(nodeName);
  },
  /**
   * Debug-only: вернуть классификацию всех mesh в загруженных моделях.
   * Используется для отладки display mode правил.
   */
  getMeshRoles: function () {
    var entries = [];
    var visit = function (root, label) {
      if (!root) return;
      root.traverse(function (child) {
        if (!child.isMesh) return;
        var role = _classifyMeshContext(child);
        entries.push({
          source: label,
          name: child.name || "",
          parent: child.parent ? child.parent.name || "" : "",
          kind: role.kind,
          section: role.section,
        });
      });
    };
    visit(modelRoot, "modelRoot");
    visit(roomModelRoot, "roomModelRoot");
    return entries;
  },
};
