(function () {
  var activeModelId = null;
  var activeRoomSignature = null;
  var activeCameraPreset = "hero";
  var activeContainerId = null;
  var loadPromise = null;
  var modulePromise = null;
  var rafId = null;
  var controlsBound = false;
  var escapeBound = false;

  function syncOverlay(
    signals,
    activeTab,
    viewerSync,
    roomConfig,
    scaleConfig,
    selectedModelId,
    selectedSceneMode,
    sceneMeta
  ) {
    bindCameraControls();
    if (activeTab !== "3d") {
      stopPositionLoop();
      return "concept03-overlay-paused";
    }
    startPositionLoop();
    ensureViewerModule().then(function () {
      syncViewer(
        signals,
        roomConfig,
        scaleConfig,
        selectedModelId,
        selectedSceneMode,
        sceneMeta || {}
      );
      positionCallouts();
      updateCompass();
    }).catch(function (error) {
      console.warn("[concept03Overlay] viewer3d.mjs load failed", error);
      setFallback(true);
    });
    return "concept03-overlay-sync:" + String(Date.now());
  }

  function ensureViewerModule() {
    if (window.pvu3d) {
      return Promise.resolve(true);
    }
    if (!modulePromise) {
      modulePromise = import("./viewer3d.mjs").then(function () {
        return Boolean(window.pvu3d);
      });
    }
    return modulePromise;
  }

  function syncViewer(
    signals,
    roomConfig,
    scaleConfig,
    selectedModelId,
    selectedSceneMode,
    sceneMeta
  ) {
    if (!window.pvu3d) {
      return;
    }
    var containerId = "concept03-scene-3d-canvas";
    var container = document.getElementById(containerId);
    if (!container) {
      return;
    }
    if (activeContainerId && activeContainerId !== containerId && window.pvu3d.isInitialized()) {
      window.pvu3d.dispose();
      activeModelId = null;
      activeRoomSignature = null;
      loadPromise = null;
    }
    activeContainerId = containerId;

    if (!window.pvu3d.isInitialized()) {
      var initOk = window.pvu3d.init(containerId, sceneMeta || {});
      if (!initOk) {
        setFallback(true);
        return;
      }
    }
    if (window.pvu3d.hasFallback && window.pvu3d.hasFallback()) {
      setFallback(true);
      return;
    }
    var conceptSceneMode = resolveConceptSceneMode(selectedSceneMode);
    setFallback(false);
    setSceneMode(conceptSceneMode);

    var modelDescriptor = resolveModel(sceneMeta, selectedModelId);
    if (!modelDescriptor) {
      return;
    }
    var roomDescriptor = resolveRoom(sceneMeta, roomConfig);
    var roomSignature = signatureForRoom(roomDescriptor);
    if (
      window.pvu3d.setRoomTemplate &&
      roomDescriptor &&
      activeRoomSignature !== roomSignature
    ) {
      window.pvu3d.setRoomTemplate(Object.assign({}, roomDescriptor));
      activeRoomSignature = roomSignature;
    }
    if (window.pvu3d.setScaleTuning) {
      window.pvu3d.setScaleTuning(scaleConfig || {});
    }

    if (activeModelId !== modelDescriptor.id) {
      if (loadPromise) {
        return;
      }
      loadPromise = window.pvu3d.loadModel(
        modelDescriptor.model_url,
        (sceneMeta && sceneMeta.bindings) ? sceneMeta.bindings : [],
        Object.assign({}, modelDescriptor)
      ).then(function () {
        activeModelId = modelDescriptor.id;
        loadPromise = null;
        applySceneState(signals, modelDescriptor, conceptSceneMode);
      }).catch(function (error) {
        console.error("[concept03Overlay] Model load failed", error);
        loadPromise = null;
        setFallback(true);
      });
      return;
    }

    applySceneState(signals, modelDescriptor, conceptSceneMode);
  }

  function applySceneState(signals, modelDescriptor, conceptSceneMode) {
    if (!window.pvu3d) {
      return;
    }
    if (window.pvu3d.setDisplayMode) {
      window.pvu3d.setDisplayMode(resolveViewerDisplayMode(conceptSceneMode), {
        accent: modelDescriptor.accent,
        tone: modelDescriptor.tone,
      });
    }
    if (window.pvu3d.setCameraPreset) {
      window.pvu3d.setCameraPreset(activeCameraPreset || "hero");
    }
    if (signals && window.pvu3d.applySignals) {
      window.pvu3d.applySignals(signals);
    }
  }

  function resolveModel(sceneMeta, selectedModelId) {
    var catalog = (sceneMeta && sceneMeta.model_catalog) || {};
    var models = catalog.models || [];
    if (!models.length) {
      return null;
    }
    var targetId = selectedModelId || catalog.default_model_id || models[0].id;
    for (var i = 0; i < models.length; i += 1) {
      if (models[i].id === targetId) {
        return models[i];
      }
    }
    return models[0];
  }

  function resolveConceptSceneMode(mode) {
    var allowed = {
      catalog: true,
      digital_twin: true,
      xray: true,
      schematic: true,
    };
    return allowed[mode] ? mode : "catalog";
  }

  function resolveViewerDisplayMode(conceptSceneMode) {
    if (conceptSceneMode === "xray" || conceptSceneMode === "schematic") {
      return conceptSceneMode;
    }
    return "studio";
  }

  function setSceneMode(conceptSceneMode) {
    var viewport = document.getElementById("concept03-scene-3d-viewport");
    if (!viewport) {
      return;
    }
    viewport.setAttribute("data-concept03-scene-mode", conceptSceneMode);
  }

  function resolveRoom(sceneMeta, roomConfig) {
    if (roomConfig && roomConfig.id) {
      return roomConfig;
    }
    var catalog = (sceneMeta && sceneMeta.room_catalog) || {};
    var rooms = catalog.rooms || [];
    if (!rooms.length) {
      return null;
    }
    var targetId = catalog.default_room_id || rooms[0].id;
    for (var i = 0; i < rooms.length; i += 1) {
      if (rooms[i].id === targetId) {
        return rooms[i];
      }
    }
    return rooms[0];
  }

  function signatureForRoom(roomDescriptor) {
    if (!roomDescriptor) {
      return "";
    }
    return [
      roomDescriptor.id || "",
      roomDescriptor.active_preset_id || "",
      roomDescriptor.occupancy_people || "",
      roomDescriptor.local_humidity_percent || "",
    ].join(":");
  }

  function bindCameraControls() {
    if (controlsBound) {
      return;
    }
    controlsBound = true;
    document.addEventListener("click", function (event) {
      var opener = event.target.closest("[data-mobile-menu-open]");
      if (opener) {
        setMobileMenuOpen(true);
        return;
      }
      var closer = event.target.closest("[data-mobile-menu-close]");
      if (closer) {
        setMobileMenuOpen(false);
        return;
      }
      var tool = event.target.closest("[data-camera-tool]");
      if (tool) {
        handleCameraTool(tool.getAttribute("data-camera-tool"));
        return;
      }
      var dot = event.target.closest("[data-camera-preset]");
      if (dot) {
        setCameraPreset(dot.getAttribute("data-camera-preset"));
      }
    });
    if (!escapeBound) {
      escapeBound = true;
      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          setMobileMenuOpen(false);
        }
      });
    }
  }

  function setMobileMenuOpen(open) {
    var menu = document.getElementById("mobile-offcanvas");
    if (!menu) {
      return;
    }
    var isOpen = Boolean(open);
    menu.classList.toggle("c03-mobile-offcanvas--open", isOpen);
    menu.setAttribute("data-mobile-menu-state", isOpen ? "open" : "closed");
    document.body.classList.toggle("c03-mobile-menu-open", isOpen);
    document.querySelectorAll("[data-mobile-menu-open]").forEach(function (button) {
      button.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
  }

  function handleCameraTool(toolId) {
    if (toolId === "view-fullscreen") {
      var viewport = document.getElementById("concept03-scene-3d-viewport");
      if (viewport && viewport.requestFullscreen) {
        viewport.requestFullscreen();
      }
      return;
    }
    if (toolId === "capture-png") {
      captureDefenseView();
      return;
    }
    setCameraPreset(cameraPresetForTool(toolId));
    if (window.pvu3d && window.pvu3d.setDisplayMode) {
      if (toolId === "view-section") {
        window.pvu3d.setDisplayMode("xray");
      } else if (toolId === "view-layers") {
        window.pvu3d.setDisplayMode("schematic");
      }
    }
  }

  function cameraPresetForTool(toolId) {
    var presets = {
      "view-orbit": "service",
      "view-fit": "hero",
      "view-front": "front",
      "view-section": "service",
      "view-split": "top",
      "view-layers": "hero",
    };
    return presets[toolId] || "hero";
  }

  function captureDefenseView() {
    updateCaptureStatus("3D PNG: формируется...");
    ensureViewerModule().then(function () {
      if (!window.pvu3d || !window.pvu3d.captureViews) {
        throw new Error("captureViews is not available");
      }
      return window.pvu3d.captureViews([
        {
          preset: activeCameraPreset || "hero",
          label: "Активный вид",
        },
      ]);
    }).then(function (payload) {
      var capture = payload && payload.captures && payload.captures[0];
      if (!capture || !capture.dataUrl) {
        throw new Error("capture payload is empty");
      }
      window.__concept03LastCapture = payload;
      downloadDataUrl(
        capture.dataUrl,
        "concept03-3d-" + sanitizeFilePart(capture.preset || "view") + "-" + timestampSlug() + ".png"
      );
      updateCaptureStatus("3D PNG: снимок готов");
    }).catch(function () {
      updateCaptureStatus("3D PNG: снимок недоступен");
    });
  }

  function updateCaptureStatus(text) {
    var status = document.getElementById("concept03-camera-capture-status");
    if (status) {
      status.textContent = text;
    }
  }

  function downloadDataUrl(dataUrl, filename) {
    var anchor = document.createElement("a");
    anchor.href = dataUrl;
    anchor.download = filename;
    anchor.style.display = "none";
    document.body.appendChild(anchor);
    anchor.click();
    window.setTimeout(function () {
      if (anchor.parentNode) {
        anchor.parentNode.removeChild(anchor);
      }
    }, 0);
  }

  function sanitizeFilePart(value) {
    return String(value || "view").toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "") || "view";
  }

  function timestampSlug() {
    return new Date().toISOString().replace(/[-:]/g, "").replace(/\..+$/, "").replace("T", "-");
  }

  function setCameraPreset(preset) {
    activeCameraPreset = preset || "hero";
    if (window.pvu3d && window.pvu3d.setCameraPreset) {
      window.pvu3d.setCameraPreset(activeCameraPreset);
    }
    document.querySelectorAll(".c03-canvas-dot").forEach(function (dot) {
      dot.classList.toggle(
        "c03-canvas-dot--active",
        dot.getAttribute("data-camera-preset") === activeCameraPreset
      );
    });
    positionCallouts();
    updateCompass();
  }

  // Overlay-обновления теперь в главном рендер-цикле viewer3d.mjs (один RAF вместо двух).
  // startPositionLoop/stopPositionLoop оставлены заглушками для обратной совместимости.
  function requestOverlayUpdate() {
    positionCallouts();
    updateCompass();
  }
  function startPositionLoop() { /* no-op: overlay теперь в главном цикле */ }
  function stopPositionLoop()  { /* no-op */ }
  // Экспорт для вызова из viewer3d.mjs
  window.concept03Overlay = { requestOverlayUpdate: requestOverlayUpdate };

  function positionCallouts() {
    var layer = document.getElementById("concept03-callout-layer");
    if (!layer) {
      return;
    }
    if (window.pvu3d && window.pvu3d.hasFallback && window.pvu3d.hasFallback()) {
      setFallback(true);
      return;
    }
    var canProject = window.pvu3d && window.pvu3d.getProjectedNode;
    layer.querySelectorAll("[data-scene-node]").forEach(function (callout) {
      if (!canProject) {
        callout.removeAttribute("data-positioned");
        return;
      }
      var projected = window.pvu3d.getProjectedNode(
        callout.getAttribute("data-scene-node")
      );
      if (!projected) {
        callout.removeAttribute("data-positioned");
        return;
      }
      var x = clamp(projected.x, 22, layer.clientWidth - 22);
      var y = clamp(projected.y, 22, layer.clientHeight - 22);
      callout.style.setProperty("--callout-x", x + "px");
      callout.style.setProperty("--callout-y", y + "px");
      callout.setAttribute("data-positioned", "true");
    });
  }

  function updateCompass() {
    var needle = document.getElementById("concept03-compass-needle");
    if (!needle || !window.pvu3d || !window.pvu3d.getDebugState) {
      return;
    }
    var debugState = window.pvu3d.getDebugState();
    if (!debugState || !debugState.camera || !debugState.target) {
      return;
    }
    var dx = debugState.camera[0] - debugState.target[0];
    var dz = debugState.camera[2] - debugState.target[2];
    var headingDeg = Math.atan2(dx, dz) * 180 / Math.PI;
    needle.style.transform = "translate(-50%, -50%) rotate(" + headingDeg + "deg)";
  }

  function setFallback(enabled) {
    var viewport = document.getElementById("concept03-scene-3d-viewport");
    if (!viewport) {
      return;
    }
    viewport.classList.toggle("c03-scene-viewport--fallback", Boolean(enabled));
  }

  function clamp(value, min, max) {
    if (!Number.isFinite(value)) {
      return min;
    }
    return Math.max(min, Math.min(max, value));
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    concept03Overlay: {
      syncOverlay: syncOverlay,
    },
  });
})();
