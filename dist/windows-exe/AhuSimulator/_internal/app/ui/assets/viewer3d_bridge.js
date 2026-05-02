(function () {
  var _activeModelId = null;
  var _activeRoomSignature = null;
  var _loadingModelId = null;
  var _loadPromise = null;
  var _requestedState = null;
  var _prefetchStarted = false;

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
    if (window.pvu3d.setRoomTemplate && roomDescriptor && _activeRoomSignature !== roomSignature) {
      window.pvu3d.setRoomTemplate(Object.assign({}, roomDescriptor));
      _activeRoomSignature = roomSignature;
    }

    if (_activeModelId !== modelDescriptor.id) {
      if (_loadingModelId === modelDescriptor.id && _loadPromise) {
        return;
      }
      _loadingModelId = modelDescriptor.id;
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
    if (window.pvu3d.setCameraPreset) {
      window.pvu3d.setCameraPreset(_requestedState.cameraPreset);
    }
    if (_requestedState.signals) {
      window.pvu3d.applySignals(_requestedState.signals);
    }
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
    },
  });
})();
