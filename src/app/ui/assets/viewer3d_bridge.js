(function () {
  var _activeModelId = null;
  var _activeRoomSignature = null;
  var _activeCameraPreset = null;
  var _loadingModelId = null;
  var _loadPromise = null;
  var _requestedState = null;
  var _prefetchStarted = false;

  var TRANSFORM_CONTROL_SPECS = [
    { key: "model_scale", inputId: "scene3d-dev-model-scale", sliderId: "scene3d-dev-model-scale-slider", defaultValue: 1, min: 0.1, max: 12, step: 0.05 },
    { key: "model_long_scale", inputId: "scene3d-dev-model-long-scale", sliderId: "scene3d-dev-model-long-scale-slider", defaultValue: 1, min: 0.1, max: 5, step: 0.05 },
    { key: "model_side_scale", inputId: "scene3d-dev-model-side-scale", sliderId: "scene3d-dev-model-side-scale-slider", defaultValue: 1, min: 0.1, max: 5, step: 0.05 },
    { key: "model_vertical_scale", inputId: "scene3d-dev-model-vertical-scale", sliderId: "scene3d-dev-model-vertical-scale-slider", defaultValue: 1, min: 0.1, max: 5, step: 0.05 },
    { key: "model_long_delta", inputId: "scene3d-dev-model-long-delta", sliderId: "scene3d-dev-model-long-delta-slider", defaultValue: 0, min: -8, max: 8, step: 0.01 },
    { key: "model_side_delta", inputId: "scene3d-dev-model-side-delta", sliderId: "scene3d-dev-model-side-delta-slider", defaultValue: 0, min: -8, max: 8, step: 0.01 },
    { key: "model_vertical_delta", inputId: "scene3d-dev-model-vertical-delta", sliderId: "scene3d-dev-model-vertical-delta-slider", defaultValue: 0, min: -5, max: 5, step: 0.01 },
    { key: "model_rotation_delta_deg", inputId: "scene3d-dev-model-rotation-delta", sliderId: "scene3d-dev-model-rotation-delta-slider", defaultValue: 0, min: -360, max: 360, step: 1 },
    { key: "model_pitch_delta_deg", inputId: "scene3d-dev-model-pitch-delta", sliderId: "scene3d-dev-model-pitch-delta-slider", defaultValue: 0, min: -90, max: 90, step: 1 },
    { key: "model_roll_delta_deg", inputId: "scene3d-dev-model-roll-delta", sliderId: "scene3d-dev-model-roll-delta-slider", defaultValue: 0, min: -90, max: 90, step: 1 },
    { key: "room_scale", inputId: "scene3d-dev-room-scale", sliderId: "scene3d-dev-room-scale-slider", defaultValue: 1, min: 0.1, max: 16, step: 0.05 },
    { key: "room_long_delta", inputId: "scene3d-dev-room-long-delta", sliderId: "scene3d-dev-room-long-delta-slider", defaultValue: 0, min: -8, max: 8, step: 0.01 },
    { key: "room_side_delta", inputId: "scene3d-dev-room-side-delta", sliderId: "scene3d-dev-room-side-delta-slider", defaultValue: 0, min: -8, max: 8, step: 0.01 },
    { key: "room_vertical_delta", inputId: "scene3d-dev-room-vertical-delta", sliderId: "scene3d-dev-room-vertical-delta-slider", defaultValue: 0, min: -5, max: 5, step: 0.01 },
    { key: "room_rotation_delta_deg", inputId: "scene3d-dev-room-rotation-delta", sliderId: "scene3d-dev-room-rotation-delta-slider", defaultValue: 0, min: -360, max: 360, step: 1 },
  ];

  function switchRenderMode(n2d, n3d, currentMode, sceneMeta) {
    var triggered = window.dash_clientside.callback_context.triggered;
    var triggeredId = (triggered && triggered.length > 0)
      ? triggered[0].prop_id.split(".")[0]
      : null;

    var newMode = currentMode || "2d";
    if (triggeredId === "render-mode-3d") {
      newMode = "3d";
    } else if (triggeredId === "render-mode-2d") {
      newMode = "2d";
    }

    if (window.pvu3d && window.pvu3d.hasFallback()) {
      window.pvu3d.clearFallback();
      newMode = "2d";
    }

    if (newMode === "2d" && window.pvu3d && window.pvu3d.isInitialized()) {
      window.pvu3d.dispose();
      _activeModelId = null;
      _activeRoomSignature = null;
      _activeCameraPreset = null;
      _loadingModelId = null;
      _loadPromise = null;
      _prefetchStarted = false;
    }

    return [
      newMode,
      newMode === "2d" ? {} : { display: "none" },
      newMode === "3d" ? {} : { display: "none" },
      "render-mode-btn" + (newMode === "2d" ? " active" : ""),
      "render-mode-btn" + (newMode === "3d" ? " active" : ""),
      newMode === "2d" ? "2D-мнемосхема" : "Цифровой двойник 3D",
    ];
  }

  function updateViewer3d(
    signals,
    renderMode,
    modelId,
    displayMode,
    cameraPreset,
    roomConfig,
    scaleConfig,
    sceneMeta
  ) {
    if (renderMode !== "3d") {
      return window.dash_clientside.no_update;
    }
    if (!window.pvu3d) {
      console.warn("[pvu3dBridge] viewer3d.mjs not loaded yet");
      return "viewer-missing";
    }

    _requestedState = {
      signals: signals || null,
      modelId: modelId || null,
      displayMode: displayMode || "studio",
      cameraPreset: cameraPreset || "hero",
      roomConfig: roomConfig || null,
      scaleConfig: scaleConfig || null,
    };

    _flushPendingState(sceneMeta || {});
    return _loadPromise ? "3d-loading" : "3d-updated";
  }

  function _flushPendingState(sceneMeta) {
    if (!_requestedState) {
      return;
    }

    if (!window.pvu3d.isInitialized()) {
      var initOk = window.pvu3d.init("scene-3d-canvas", sceneMeta || {});
      if (!initOk) {
        window.__pvu3d_fallback = true;
        return;
      }
    }

    var modelDescriptor = _resolveModel(sceneMeta, _requestedState.modelId);
    var roomDescriptor = _resolveRoom(sceneMeta, _requestedState.roomConfig);
    if (!modelDescriptor) {
      console.warn("[pvu3dBridge] No scene model resolved");
      return;
    }

    var roomSignature = _roomSignature(roomDescriptor);
    if (window.pvu3d.setScaleTuning) {
      window.pvu3d.setScaleTuning(_requestedState.scaleConfig || {});
    }
    if (window.pvu3d.setRoomTemplate && roomDescriptor && _activeRoomSignature !== roomSignature) {
      window.pvu3d.setRoomTemplate(Object.assign({}, roomDescriptor));
      _activeRoomSignature = roomSignature;
    }

    if (_activeModelId !== modelDescriptor.id) {
      if (_loadingModelId === modelDescriptor.id && _loadPromise) {
        return;
      }
      _loadingModelId = modelDescriptor.id;
      _activeCameraPreset = null;
      _loadPromise = window.pvu3d.loadModel(
        modelDescriptor.model_url,
        (sceneMeta && sceneMeta.bindings) ? sceneMeta.bindings : [],
        Object.assign({}, modelDescriptor)
      ).then(function () {
        _activeModelId = modelDescriptor.id;
        _loadingModelId = null;
        _loadPromise = null;
        _schedulePrefetch(sceneMeta, modelDescriptor.id);
        _flushPendingState(sceneMeta);
      }).catch(function (err) {
        console.error("[pvu3dBridge] Model load failed:", err);
        _loadingModelId = null;
        _loadPromise = null;
      });
      return;
    }

    if (window.pvu3d.setDisplayMode) {
      window.pvu3d.setDisplayMode(_requestedState.displayMode, {
        accent: modelDescriptor.accent,
        tone: modelDescriptor.tone,
      });
    }
    if (
      window.pvu3d.setCameraPreset &&
      _activeCameraPreset !== _requestedState.cameraPreset
    ) {
      window.pvu3d.setCameraPreset(_requestedState.cameraPreset);
      _activeCameraPreset = _requestedState.cameraPreset;
    }
    if (_requestedState.signals) {
      window.pvu3d.applySignals(_requestedState.signals);
    }
  }

  function syncTransformControls() {
    var args = Array.prototype.slice.call(arguments);
    var triggeredId = _triggeredId();
    var payload = {};
    var outputValues = [];

    TRANSFORM_CONTROL_SPECS.forEach(function (spec, index) {
      var inputValue = args[index * 2];
      var sliderValue = args[index * 2 + 1];
      var preferredValue = _preferredTransformValue(
        spec,
        triggeredId,
        inputValue,
        sliderValue
      );
      if (triggeredId === "scene3d-dev-transform-reset") {
        preferredValue = spec.defaultValue;
      }
      var value = _sanitizeTransformValue(preferredValue, spec);
      payload[spec.key] = value;
      outputValues.push(value);
      outputValues.push(value);
    });

    return [payload].concat(outputValues);
  }

  function _triggeredId() {
    var context = window.dash_clientside && window.dash_clientside.callback_context;
    if (!context) {
      return null;
    }
    if (context.triggered_id) {
      return context.triggered_id;
    }
    var triggered = context.triggered;
    return triggered && triggered.length > 0
      ? triggered[0].prop_id.split(".")[0]
      : null;
  }

  function _preferredTransformValue(spec, triggeredId, inputValue, sliderValue) {
    if (triggeredId === spec.sliderId) {
      return sliderValue;
    }
    if (triggeredId === spec.inputId) {
      return inputValue;
    }
    if (_isFiniteNumber(inputValue)) {
      return inputValue;
    }
    if (_isFiniteNumber(sliderValue)) {
      return sliderValue;
    }
    return spec.defaultValue;
  }

  function _sanitizeTransformValue(value, spec) {
    var numericValue = Number(value);
    if (!Number.isFinite(numericValue)) {
      numericValue = spec.defaultValue;
    }
    numericValue = Math.min(spec.max, Math.max(spec.min, numericValue));
    return _roundToStep(numericValue, spec.step);
  }

  function _roundToStep(value, step) {
    if (!step || !Number.isFinite(step)) {
      return value;
    }
    var decimals = Math.max(0, (String(step).split(".")[1] || "").length);
    return Number((Math.round(value / step) * step).toFixed(decimals));
  }

  function _isFiniteNumber(value) {
    return value !== null && value !== "" && Number.isFinite(Number(value));
  }

  function _schedulePrefetch(sceneMeta, activeModelId) {
    if (_prefetchStarted || !window.pvu3d || !window.pvu3d.prefetchModel) {
      return;
    }
    _prefetchStarted = true;
    window.setTimeout(function () {
      var catalog = (sceneMeta && sceneMeta.model_catalog && sceneMeta.model_catalog.models) || [];
      catalog.forEach(function (modelDescriptor) {
        if (!modelDescriptor || modelDescriptor.id === activeModelId) {
          return;
        }
        window.pvu3d.prefetchModel(
          modelDescriptor.model_url,
          Object.assign({}, modelDescriptor)
        ).catch(function (err) {
          console.warn("[pvu3dBridge] Prefetch failed for", modelDescriptor.id, err);
        });
      });
    }, 900);
  }

  function _resolveModel(sceneMeta, modelId) {
    var catalog = (sceneMeta && sceneMeta.model_catalog) || {};
    var items = catalog.models || [];
    if (!items.length) {
      return null;
    }
    var targetId = modelId || catalog.default_model_id || items[0].id;
    for (var i = 0; i < items.length; i += 1) {
      if (items[i].id === targetId) {
        return items[i];
      }
    }
    return items[0];
  }

  function _resolveRoom(sceneMeta, roomConfig) {
    if (roomConfig && roomConfig.id) {
      return roomConfig;
    }
    var catalog = (sceneMeta && sceneMeta.room_catalog) || {};
    var items = catalog.rooms || [];
    if (!items.length) {
      return null;
    }
    var targetId = catalog.default_room_id || items[0].id;
    for (var i = 0; i < items.length; i += 1) {
      if (items[i].id === targetId) {
        return items[i];
      }
    }
    return items[0];
  }

  function _roomSignature(roomDescriptor) {
    if (!roomDescriptor) {
      return null;
    }
    return [
      roomDescriptor.id || "",
      roomDescriptor.active_preset_id || "",
      roomDescriptor.occupancy_people || "",
      roomDescriptor.local_humidity_percent || "",
    ].join(":");
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    pvu3dBridge: {
      switchRenderMode: switchRenderMode,
      updateViewer3d: updateViewer3d,
      syncTransformControls: syncTransformControls,
    },
  });
})();
