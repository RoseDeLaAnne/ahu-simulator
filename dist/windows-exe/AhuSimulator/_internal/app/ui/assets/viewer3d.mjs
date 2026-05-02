import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.mjs";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.mjs";

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

let renderer = null;
let scene = null;
let camera = null;
let controls = null;
let animationId = null;
let clock = null;
let container = null;
let infoCard = null;
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
  mesh.castShadow = false;
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

function _showInfoCard(target, x, y) {
  if (!infoCard || !target || !target.userData || !target.userData.pvuSignal) return;
  var signal = target.userData.pvuSignal;
  var alarmText = signal.alarm_text
    ? '<div class="viewer3d-info-alarm">ALARM: ' + signal.alarm_text + "</div>"
    : "";
  infoCard.innerHTML =
    '<div class="viewer3d-info-label">' + (signal.label || target.name || "Signal") + "</div>" +
    '<div class="viewer3d-info-value">' + (signal.value || "") + "</div>" +
    (signal.detail ? '<div class="viewer3d-info-detail">' + signal.detail + "</div>" : "") +
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

function _createSceneScaffold() {
  scene = new THREE.Scene();
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
  scene.add(ambientLight);
  scene.add(keyLight);
  scene.add(rimLight);
  scene.add(fillLight);

  _buildEnvironmentDecor();
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
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
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
    sharedLoader = new GLTFLoader();
    renderer = new THREE.WebGLRenderer({
      antialias: ((sceneMeta.performance_budget || {}).antialias !== false),
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(container.clientWidth || 800, container.clientHeight || 540);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
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
    controls.maxDistance = 30;
    controls.minPolarAngle = 0.12;
    controls.maxPolarAngle = Math.PI * 0.48;
    controls.target.set(0, 0.6, 0);
    controls.update();

    raycaster = new THREE.Raycaster();
    clock = new THREE.Clock();
    _createSceneScaffold();
    _createInfoCard();
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
  return wrapper;
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
      long_delta: placement.long_delta || 0,
      vertical_delta: placement.vertical_delta || 0,
      side_delta: placement.side_delta || 0,
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
  var tunedScale = _withDefault(placement.scale_multiplier, 1);
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
  roomRoot.rotation.set(0, THREE.MathUtils.degToRad(placement.rotation_deg_y || 0), 0);
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

  var coreGeometry = options.kind === "sensor"
    ? new THREE.SphereGeometry(radius * 0.72, 24, 24)
    : new THREE.OctahedronGeometry(radius * 0.82, 0);
  var core = new THREE.Mesh(
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

  group.userData.colorMaterials.push(ring.material, core.material, halo.material);
  group.userData.glowMaterials.push(ring.material, core.material);
  if (group.children[3] && group.children[3].material) {
    group.userData.colorMaterials.push(group.children[3].material);
  }
  _registerNode(sceneNode, group, true);
  overlayRoot.add(group);
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

  for (var i = 0; i < 10; i += 1) {
    var particle = new THREE.Mesh(
      new THREE.SphereGeometry(viewMetrics.flowRadius * 0.74, 16, 16),
      new THREE.MeshBasicMaterial({
        color: colorHex,
        transparent: true,
        opacity: 0.82,
        depthWrite: false,
      })
    );
    particle.userData.flowOffset = i / 10;
    group.userData.flowParticles.push(particle);
    group.add(particle);
  }

  group.userData.colorMaterials = [tube.material, auraTube.material];
  group.userData.glowMaterials = [tube.material];
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
    heater: _resolvePointFromSpec(anchorsProfile.heater, null, { long: 0.46, vertical: 0.74, side: 0.0 }),
    fan: _resolvePointFromSpec(anchorsProfile.fan, null, { long: 0.68, vertical: 0.74, side: 0.14 }),
    duct: _resolvePointFromSpec(anchorsProfile.duct, null, { long: 0.88, vertical: 0.72, side: 0.24 }),
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

  _createStageMarker("pvu.intake.outdoor_air", anchors.outdoor, { kind: "node", scale: 1.18 });
  _createStageMarker("pvu.filter.bank", anchors.filter, { kind: "node", scale: 1.14 });
  _createStageMarker("pvu.heater.coil", anchors.heater, { kind: "node", scale: 1.14 });
  _createStageMarker("pvu.fan.supply", anchors.fan, { kind: "node", scale: 1.14 });
  _createStageMarker("pvu.duct.supply", anchors.duct, { kind: "node", scale: 1.1 });
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
  controls.maxDistance = viewMetrics.maxDim * _withDefault(activeProfile.max_distance, 5.0);
  controls.update();
  return true;
}

function _rebuildSyntheticScene() {
  _hideInfoCard();
  hoveredObject = null;
  selectedObject = null;
  _clearOverlayRoot();
  nodeMap = {};
  interactiveObjects = [];
  if (!viewMetrics) return false;
  _buildSyntheticScene();
  setDisplayMode(currentDisplayMode, currentModelDescriptor || {});
  setCameraPreset(currentCameraPreset);
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

function _applyDisplayModeToRoot(root, mode, accentColor) {
  if (!root) return;
  root.traverse(function (child) {
    if (!child.isMesh || !child.material) return;
    _materialArray(child.material).forEach(function (material) {
      var base = _ensureModelMaterialState(material);
      if (mode === "xray") {
        material.transparent = true;
        material.opacity = Math.max(0.18, base.opacity * 0.24);
        material.depthWrite = false;
        material.color.copy(base.color).lerp(accentColor, 0.32);
        material.emissive.copy(accentColor).multiplyScalar(0.12);
        material.emissiveIntensity = 0.26;
        material.roughness = 0.12;
        material.metalness = 0.06;
      } else if (mode === "schematic") {
        material.transparent = true;
        material.opacity = Math.max(0.08, base.opacity * 0.12);
        material.depthWrite = false;
        material.color.copy(base.color).lerp(new THREE.Color(0xe2e8f0), 0.78);
        material.emissive.setHex(0x000000);
        material.emissiveIntensity = 0;
        material.roughness = 0.95;
        material.metalness = 0.0;
      } else {
        material.transparent = base.transparent;
        material.opacity = base.opacity;
        material.depthWrite = base.depthWrite;
        material.color.copy(base.color).lerp(accentColor, 0.08);
        material.emissive.copy(base.emissive);
        material.emissiveIntensity = Math.max(base.emissiveIntensity, 0.04);
        material.roughness = Math.min(base.roughness, 0.62);
        material.metalness = Math.max(base.metalness, 0.16);
      }
      material.needsUpdate = true;
    });
  });
}

function _applyDisplayModeToModel(mode, accent) {
  var accentColor = _colorFromHex(accent || DEFAULT_MODEL_ACCENT);
  _applyDisplayModeToRoot(modelRoot, mode, accentColor);
  _applyDisplayModeToRoot(roomModelRoot, mode, accentColor);
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
  return true;
}

function _applyNodeSignal(node, signal, kind, colorHex) {
  if (!node) return;
  node.userData.pvuSignal = signal;
  node.userData.pvuBinding = bindingByVisualId[signal.visual_id] || null;
  node.userData.pvuState = signal.state || "normal";

  var color = _colorFromHex(colorHex);
  var emissiveStrength = signal.state === "alarm" ? 1.45 : signal.state === "warning" ? 0.72 : 0.48;
  var materials = node.userData.colorMaterials || [];
  var glowMaterials = node.userData.glowMaterials || [];
  materials.forEach(function (material) {
    if (material.color) material.color.copy(color);
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
      material.emissive.copy(color);
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
  Object.keys(nodeMap).forEach(function (key) {
    var node = nodeMap[key];
    if (!node || node.userData.__flowAnimated || node.userData.overlayKind !== "flow") return;
    node.userData.__flowAnimated = true;
    var intensity = _clamp(node.userData.flowIntensity || 0.55, 0.12, 1.15);
    var pulse = 0.5 + 0.5 * Math.sin(time * (1.2 + intensity * 2.8));
    var materials = node.userData.colorMaterials || [];
    materials.forEach(function (material) {
      if (!material) return;
      if (typeof material.opacity === "number") {
        material.opacity = 0.16 + intensity * 0.6 + pulse * 0.08;
      }
      if (material.emissiveIntensity !== undefined) {
        material.emissiveIntensity = 0.42 + intensity * 0.85 + pulse * 0.15;
      }
    });
    (node.userData.flowParticles || []).forEach(function (particle) {
      var progress =
        (time * (0.14 + intensity * 0.26) + particle.userData.flowOffset) % 1;
      var point = node.userData.flowCurve.getPointAt(progress);
      particle.position.copy(point);
      particle.scale.setScalar(0.8 + pulse * 0.45);
      particle.material.opacity = 0.3 + intensity * 0.6;
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
  var speedSignal = _resolveSignalPath(fanRule.speed_signal);
  var speed = typeof speedSignal === "number" ? speedSignal : 0.55;
  var rpm = (fanRule.max_rpm || 3.0) * _clamp(speed, 0.1, 1.2);
  fanNode.rotation[fanRule.axis.toLowerCase()] += dt * rpm * Math.PI * 2;
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

function _startAnimation() {
  if (animationId !== null) return;
  function loop() {
    animationId = requestAnimationFrame(loop);
    var dt = clock.getDelta();
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
    if (floorGlow) {
      floorGlow.rotation.z = time * 0.045;
    }
    renderer.render(scene, camera);
  }
  loop();
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
  viewMetrics = entry.viewMetrics || _computeViewMetrics(modelRoot);
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
      sharedLoader = new GLTFLoader();
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

function _ensureActiveRoomModel() {
  if (!currentRoomDescriptor || !currentRoomDescriptor.model_url || !viewMetrics) {
    _clearLoadedRoom();
    if (modelRoot && viewMetrics) {
      _rebuildSyntheticScene();
    }
    return Promise.resolve(null);
  }

  return _cacheRoomEntry(
    currentRoomDescriptor.model_url,
    currentRoomDescriptor,
    false
  ).then(function (entry) {
    _activateRoomEntry(entry);
    _rebuildSyntheticScene();
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
      sharedLoader = new GLTFLoader();
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
  if (scene) {
    scene.remove(environmentRoot);
    scene.remove(atmosphereRoot);
    _disposeObject(environmentRoot);
    _disposeObject(atmosphereRoot);
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

window.pvu3d = {
  init: init,
  loadModel: loadModel,
  prefetchModel: prefetchModel,
  applySignals: applySignals,
  setDisplayMode: setDisplayMode,
  setCameraPreset: setCameraPreset,
  setRoomTemplate: setRoomTemplate,
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
    };
  },
  getProjectedNode: function (nodeName) {
    return _projectNode(nodeName);
  },
};
