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

  var BLOOM_CONTROL_SPECS = [
    { key: "bloom_strength", inputId: "scene3d-bloom-strength", sliderId: "scene3d-bloom-strength-slider", defaultValue: 1.2, min: 0, max: 3, step: 0.1 },
    { key: "bloom_radius", inputId: "scene3d-bloom-radius", sliderId: "scene3d-bloom-radius-slider", defaultValue: 0.4, min: 0, max: 1, step: 0.05 },
    { key: "bloom_threshold", inputId: "scene3d-bloom-threshold", sliderId: "scene3d-bloom-threshold-slider", defaultValue: 0.85, min: 0, max: 1, step: 0.05 },
  ];

  var SSAO_CONTROL_SPECS = [
    { key: "ssao_kernel_radius", param: "kernelRadius", inputId: "scene3d-ssao-kernel_radius", sliderId: "scene3d-ssao-kernel_radius-slider", defaultValue: 0.5, min: 0, max: 2, step: 0.05 },
    { key: "ssao_min_distance", param: "minDistance", inputId: "scene3d-ssao-min_distance", sliderId: "scene3d-ssao-min_distance-slider", defaultValue: 0.002, min: 0, max: 0.05, step: 0.001 },
    { key: "ssao_max_distance", param: "maxDistance", inputId: "scene3d-ssao-max_distance", sliderId: "scene3d-ssao-max_distance-slider", defaultValue: 0.06, min: 0, max: 0.3, step: 0.005 },
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

  function syncBloomControls() {
    var args = Array.prototype.slice.call(arguments);
    var triggeredId = _triggeredId();
    var outputValues = [];

    // Последний аргумент - это checkbox enabled
    var enabledCheckbox = args[args.length - 1];
    var isEnabled = Array.isArray(enabledCheckbox) && enabledCheckbox.indexOf("enabled") !== -1;

    BLOOM_CONTROL_SPECS.forEach(function (spec, index) {
      var inputValue = args[index * 2];
      var sliderValue = args[index * 2 + 1];
      var preferredValue = _preferredTransformValue(
        spec,
        triggeredId,
        inputValue,
        sliderValue
      );
      var value = _sanitizeTransformValue(preferredValue, spec);
      outputValues.push(value);
      outputValues.push(value);
    });

    // Применяем параметры Bloom к viewer3d
    if (window.pvu3d && window.pvu3d.isInitialized()) {
      if (window.pvu3d.setBloomEnabled) {
        window.pvu3d.setBloomEnabled(isEnabled);
      }
      if (window.pvu3d.setBloomParams && isEnabled) {
        var params = {};
        BLOOM_CONTROL_SPECS.forEach(function (spec, index) {
          var value = outputValues[index * 2]; // Берем значение из outputValues
          var paramKey = spec.key.replace("bloom_", "");
          params[paramKey] = value;
        });
        window.pvu3d.setBloomParams(params);
      }
    }

    return outputValues;
  }

  function syncSSAOControls() {
    var args = Array.prototype.slice.call(arguments);
    var triggeredId = _triggeredId();
    var outputValues = [];

    // Последний аргумент - это checkbox enabled
    var enabledCheckbox = args[args.length - 1];
    var isEnabled = Array.isArray(enabledCheckbox) && enabledCheckbox.indexOf("enabled") !== -1;

    SSAO_CONTROL_SPECS.forEach(function (spec, index) {
      var inputValue = args[index * 2];
      var sliderValue = args[index * 2 + 1];
      var preferredValue = _preferredTransformValue(
        spec,
        triggeredId,
        inputValue,
        sliderValue
      );
      var value = _sanitizeTransformValue(preferredValue, spec);
      outputValues.push(value);
      outputValues.push(value);
    });

    // Применяем параметры SSAO к viewer3d
    if (window.pvu3d && window.pvu3d.isInitialized()) {
      if (window.pvu3d.setSSAOEnabled) {
        window.pvu3d.setSSAOEnabled(isEnabled);
      }
      if (window.pvu3d.setSSAOParams && isEnabled) {
        var params = {};
        SSAO_CONTROL_SPECS.forEach(function (spec, index) {
          params[spec.param] = outputValues[index * 2];
        });
        window.pvu3d.setSSAOParams(params);
      }
    }

    return outputValues;
  }

  function _measurementListHtml(distances, angles) {
    distances = distances || [];
    angles = angles || [];
    if (distances.length === 0 && angles.length === 0) {
      return "";
    }
    var html = "<ul>";
    distances.forEach(function (m, index) {
      html += "<li>Расстояние " + (index + 1) + ": " + m.distance.toFixed(2) + " м</li>";
    });
    angles.forEach(function (g, index) {
      html += "<li>Угол " + (index + 1) + ": " + g.angle.toFixed(1) + "°</li>";
    });
    html += "</ul>";
    return html;
  }

  function _renderMeasurementList() {
    if (!window.pvu3d) {
      return "";
    }
    if (window.pvu3d.getAllMeasurements) {
      var all = window.pvu3d.getAllMeasurements();
      return _measurementListHtml(all.distances, all.angles);
    }
    var distances = window.pvu3d.getMeasurements ? window.pvu3d.getMeasurements() : [];
    return _measurementListHtml(distances, []);
  }

  function syncMeasurementMode(
    modeCheckbox,
    clearClicks,
    measureType,
    saveClicks,
    restoreClicks,
    exportJsonClicks,
    exportCsvClicks
  ) {
    var triggeredId = _triggeredId();
    var isEnabled = Array.isArray(modeCheckbox) && modeCheckbox.indexOf("enabled") !== -1;
    var noUpdate = window.dash_clientside.no_update;

    if (!(window.pvu3d && window.pvu3d.isInitialized())) {
      return [modeCheckbox, noUpdate, noUpdate];
    }

    if (triggeredId === "scene3d-measurement-clear") {
      if (window.pvu3d.clearMeasurements) {
        window.pvu3d.clearMeasurements();
      }
      return [modeCheckbox, _renderMeasurementList(), "Измерения очищены"];
    }

    if (triggeredId === "scene3d-measurement-type") {
      if (window.pvu3d.setMeasurementType) {
        window.pvu3d.setMeasurementType(measureType);
      }
      return [modeCheckbox, _renderMeasurementList(), noUpdate];
    }

    if (triggeredId === "scene3d-measurement-save") {
      var saved = window.pvu3d.saveMeasurementsToSession
        ? window.pvu3d.saveMeasurementsToSession()
        : false;
      return [
        modeCheckbox,
        _renderMeasurementList(),
        saved ? "Сохранено в сессии" : "Не удалось сохранить",
      ];
    }

    if (triggeredId === "scene3d-measurement-restore") {
      var restored = window.pvu3d.restoreMeasurementsFromSession
        ? window.pvu3d.restoreMeasurementsFromSession()
        : false;
      return [
        modeCheckbox,
        _renderMeasurementList(),
        restored ? "Восстановлено из сессии" : "Нет сохранённых измерений",
      ];
    }

    if (triggeredId === "scene3d-measurement-export-json") {
      var jsonResult = window.pvu3d.exportMeasurements
        ? window.pvu3d.exportMeasurements("json")
        : null;
      return [
        modeCheckbox,
        _renderMeasurementList(),
        jsonResult
          ? "Экспорт JSON: " + (jsonResult.distances + jsonResult.angles) + " измерений"
          : "Нет измерений для экспорта",
      ];
    }

    if (triggeredId === "scene3d-measurement-export-csv") {
      var csvResult = window.pvu3d.exportMeasurements
        ? window.pvu3d.exportMeasurements("csv")
        : null;
      return [
        modeCheckbox,
        _renderMeasurementList(),
        csvResult
          ? "Экспорт CSV: " + (csvResult.distances + csvResult.angles) + " измерений"
          : "Нет измерений для экспорта",
      ];
    }

    // Переключение режима измерения (или начальный вызов)
    if (window.pvu3d.setMeasurementMode) {
      window.pvu3d.setMeasurementMode(isEnabled);
    }
    if (window.pvu3d.setMeasurementType && measureType) {
      window.pvu3d.setMeasurementType(measureType);
    }

    return [modeCheckbox, _renderMeasurementList(), noUpdate];
  }

  function captureScreenshotAction(captureClicks, scale, format, metadataCheckbox) {
    var triggeredId = _triggeredId();

    if (triggeredId !== "scene3d-screenshot-capture") {
      return window.dash_clientside.no_update;
    }

    if (!window.pvu3d || !window.pvu3d.isInitialized()) {
      return "Ошибка: 3D-сцена не инициализирована";
    }

    if (!window.pvu3d.captureScreenshot) {
      return "Ошибка: функция захвата недоступна";
    }

    var includeMetadata = Array.isArray(metadataCheckbox) && metadataCheckbox.indexOf("enabled") !== -1;

    var options = {
      scale: scale || 2,
      format: format || "png",
      includeMetadata: includeMetadata,
    };

    window.pvu3d.captureScreenshot(options)
      .then(function (screenshotData) {
        if (window.pvu3d.downloadScreenshot) {
          window.pvu3d.downloadScreenshot(screenshotData);
        }
      })
      .catch(function (error) {
        console.error("[Screenshot] Capture failed:", error);
      });

    var timestamp = new Date().toLocaleTimeString("ru-RU");
    return "✓ Скриншот сохранён (" + timestamp + ")";
  }

  function syncHeatmapMode(enabledCheckbox, minTemp, maxTemp, signals) {
    var isEnabled = Array.isArray(enabledCheckbox) && enabledCheckbox.indexOf("enabled") !== -1;

    if (!window.pvu3d || !window.pvu3d.isInitialized()) {
      return enabledCheckbox;
    }

    if (!isEnabled) {
      if (window.pvu3d.setHeatmapMode) {
        window.pvu3d.setHeatmapMode(false);
      }
      return enabledCheckbox;
    }

    // Извлекаем температурные данные из signals
    var dataPoints = [];
    if (signals && signals.nodes) {
      var nodes = signals.nodes;

      // Собираем точки с температурными данными
      var temperatureNodes = [
        { id: "outdoor_air", x: -2, y: 1.5, z: 0 },
        { id: "supply_duct", x: 2, y: 1.5, z: 0 },
        { id: "heater_coil", x: 0, y: 1.5, z: 0 },
        { id: "filter_bank", x: -1, y: 1.5, z: 0 },
      ];

      temperatureNodes.forEach(function (node) {
        var signal = nodes[node.id];
        if (signal && signal.value) {
          var temp = parseFloat(signal.value);
          if (!isNaN(temp)) {
            dataPoints.push({
              x: node.x,
              y: node.y,
              z: node.z,
              temperature: temp,
            });
          }
        }
      });
    }

    // Если нет данных, создаём тестовые точки
    if (dataPoints.length === 0) {
      dataPoints = [
        { x: -2, y: 1.5, z: 0, temperature: -5 },
        { x: -1, y: 1.5, z: 0, temperature: 10 },
        { x: 0, y: 1.5, z: 0, temperature: 25 },
        { x: 1, y: 1.5, z: 0, temperature: 22 },
        { x: 2, y: 1.5, z: 0, temperature: 20 },
      ];
    }

    var options = {
      minTemp: minTemp || -10,
      maxTemp: maxTemp || 40,
      animate: true,
      animationDuration: 1000,
    };

    // Проверяем, включена ли уже тепловая карта
    var currentData = window.pvu3d.getHeatmapData ? window.pvu3d.getHeatmapData() : null;

    if (currentData && currentData.enabled) {
      // Тепловая карта уже включена - обновляем данные с анимацией
      if (window.pvu3d.updateHeatmapData) {
        window.pvu3d.updateHeatmapData(dataPoints, options);
      }
    } else {
      // Включаем тепловую карту впервые
      if (window.pvu3d.setHeatmapMode) {
        window.pvu3d.setHeatmapMode(true, dataPoints, options);
      }
    }

    return enabledCheckbox;
  }

  function syncClippingMode(
    enabledCheckbox,
    presetXClicks,
    presetYClicks,
    presetZClicks,
    presetDiagonalClicks,
    presetCrossClicks,
    planeIndex,
    normalX,
    normalY,
    normalZ,
    constant,
    invertedCheckbox,
    addClicks,
    removeClicks,
    clearClicks
  ) {
    var triggeredId = _triggeredId();
    var isEnabled = Array.isArray(enabledCheckbox) && enabledCheckbox.indexOf("enabled") !== -1;

    if (!window.pvu3d || !window.pvu3d.isInitialized()) {
      return [enabledCheckbox, [], normalX, normalY, normalZ, constant, invertedCheckbox];
    }

    // Обработка пресетов
    if (triggeredId === "scene3d-clipping-preset-x") {
      if (window.pvu3d.applyClippingPreset) {
        window.pvu3d.applyClippingPreset("x");
      }
      return _updateClippingOutputs(["enabled"], planeIndex);
    }

    if (triggeredId === "scene3d-clipping-preset-y") {
      if (window.pvu3d.applyClippingPreset) {
        window.pvu3d.applyClippingPreset("y");
      }
      return _updateClippingOutputs(["enabled"], planeIndex);
    }

    if (triggeredId === "scene3d-clipping-preset-z") {
      if (window.pvu3d.applyClippingPreset) {
        window.pvu3d.applyClippingPreset("z");
      }
      return _updateClippingOutputs(["enabled"], planeIndex);
    }

    if (triggeredId === "scene3d-clipping-preset-diagonal") {
      if (window.pvu3d.applyClippingPreset) {
        window.pvu3d.applyClippingPreset("diagonal");
      }
      return _updateClippingOutputs(["enabled"], planeIndex);
    }

    if (triggeredId === "scene3d-clipping-preset-cross") {
      if (window.pvu3d.applyClippingPreset) {
        window.pvu3d.applyClippingPreset("cross");
      }
      return _updateClippingOutputs(["enabled"], planeIndex);
    }

    // Обработка действий с плоскостями
    if (triggeredId === "scene3d-clipping-add") {
      if (window.pvu3d.addClippingPlane) {
        var isInverted = Array.isArray(invertedCheckbox) && invertedCheckbox.indexOf("inverted") !== -1;
        window.pvu3d.addClippingPlane({
          normal: [normalX || 0, normalY || 1, normalZ || 0],
          constant: constant || 0,
          enabled: true,
          inverted: isInverted,
        });
      }
      return _updateClippingOutputs(["enabled"], null);
    }

    if (triggeredId === "scene3d-clipping-remove") {
      if (window.pvu3d.removeClippingPlane && planeIndex !== null && planeIndex !== undefined) {
        window.pvu3d.removeClippingPlane(planeIndex);
      }
      return _updateClippingOutputs(["enabled"], null);
    }

    if (triggeredId === "scene3d-clipping-clear") {
      if (window.pvu3d.clearClippingPlanes) {
        window.pvu3d.clearClippingPlanes();
      }
      return _updateClippingOutputs(["enabled"], null);
    }

    // Обработка изменения параметров плоскости
    if (
      planeIndex !== null &&
      planeIndex !== undefined &&
      (triggeredId === "scene3d-clipping-normal-x" ||
        triggeredId === "scene3d-clipping-normal-y" ||
        triggeredId === "scene3d-clipping-normal-z" ||
        triggeredId === "scene3d-clipping-constant" ||
        triggeredId === "scene3d-clipping-inverted")
    ) {
      if (window.pvu3d.updateClippingPlane) {
        var isInverted = Array.isArray(invertedCheckbox) && invertedCheckbox.indexOf("inverted") !== -1;
        window.pvu3d.updateClippingPlane(planeIndex, {
          normal: [normalX || 0, normalY || 1, normalZ || 0],
          constant: constant || 0,
          inverted: isInverted,
        });
      }
      return _updateClippingOutputs(enabledCheckbox, planeIndex);
    }

    // Обработка выбора плоскости из dropdown
    if (triggeredId === "scene3d-clipping-plane-index" && planeIndex !== null && planeIndex !== undefined) {
      return _updateClippingOutputs(enabledCheckbox, planeIndex);
    }

    // Включение/выключение режима
    if (triggeredId === "scene3d-clipping-enabled") {
      if (window.pvu3d.setClippingMode) {
        window.pvu3d.setClippingMode(isEnabled);
      }
      return _updateClippingOutputs(enabledCheckbox, planeIndex);
    }

    return _updateClippingOutputs(enabledCheckbox, planeIndex);
  }

  function _updateClippingOutputs(enabledCheckbox, selectedIndex) {
    if (!window.pvu3d || !window.pvu3d.getClippingPlanes) {
      return [enabledCheckbox, [], 0, 1, 0, 0, []];
    }

    var data = window.pvu3d.getClippingPlanes();
    var planes = data.planes || [];

    // Создаём опции для dropdown
    var dropdownOptions = planes.map(function (plane, index) {
      return {
        label: "Плоскость " + (index + 1) + " (" + plane.normal.join(", ") + ")",
        value: index,
      };
    });

    // Если плоскость выбрана, возвращаем её параметры
    if (selectedIndex !== null && selectedIndex !== undefined && planes[selectedIndex]) {
      var selectedPlane = planes[selectedIndex];
      return [
        enabledCheckbox,
        dropdownOptions,
        selectedPlane.normal[0],
        selectedPlane.normal[1],
        selectedPlane.normal[2],
        selectedPlane.constant,
        selectedPlane.inverted ? ["inverted"] : [],
      ];
    }

    // Иначе возвращаем значения по умолчанию
    return [enabledCheckbox, dropdownOptions, 0, 1, 0, 0, []];
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

  /**
   * Синхронизация LOD режима.
   * Обрабатывает включение/выключение, пресеты, изменение дистанций.
   */
  function syncLODMode(
    enabledCheckbox,
    presetPerformanceClicks,
    presetBalancedClicks,
    presetQualityClicks,
    distanceHigh,
    distanceMedium,
    distanceLow
  ) {
    if (!window.pvu3d || !window.pvu3d.setLODMode) {
      return [enabledCheckbox, distanceMedium, distanceLow, "LOD недоступен"];
    }

    var triggeredId = _triggeredId();
    var enabled = Array.isArray(enabledCheckbox) && enabledCheckbox.includes("enabled");

    // Обработка пресетов
    if (triggeredId === "scene3d-lod-preset-performance") {
      window.pvu3d.applyLODPreset("performance");
      var stats = window.pvu3d.getLODStats();
      return [
        ["enabled"],
        stats.distances[1],
        stats.distances[2],
        _formatLODStats(stats),
      ];
    }

    if (triggeredId === "scene3d-lod-preset-balanced") {
      window.pvu3d.applyLODPreset("balanced");
      var stats = window.pvu3d.getLODStats();
      return [
        ["enabled"],
        stats.distances[1],
        stats.distances[2],
        _formatLODStats(stats),
      ];
    }

    if (triggeredId === "scene3d-lod-preset-quality") {
      window.pvu3d.applyLODPreset("quality");
      var stats = window.pvu3d.getLODStats();
      return [
        ["enabled"],
        stats.distances[1],
        stats.distances[2],
        _formatLODStats(stats),
      ];
    }

    // Обработка включения/выключения или изменения дистанций
    if (triggeredId === "scene3d-lod-enabled" ||
        triggeredId === "scene3d-lod-distance-medium" ||
        triggeredId === "scene3d-lod-distance-low") {

      var distances = [
        0,
        Number(distanceMedium) || 15,
        Number(distanceLow) || 30,
      ];

      window.pvu3d.setLODMode(enabled, { distances: distances });
      var stats = window.pvu3d.getLODStats();

      return [
        enabled ? ["enabled"] : [],
        stats.distances[1],
        stats.distances[2],
        _formatLODStats(stats),
      ];
    }

    // Обновление статистики (вызывается периодически)
    var stats = window.pvu3d.getLODStats();
    return [
      stats.enabled ? ["enabled"] : [],
      stats.distances[1],
      stats.distances[2],
      _formatLODStats(stats),
    ];
  }

  function _formatLODStats(stats) {
    if (!stats.enabled) {
      return "LOD выключен";
    }

    var total = stats.totalObjects;
    var levels = stats.currentLevels;

    if (total === 0) {
      return "Нет LOD объектов (модель слишком простая)";
    }

    return (
      "Объектов: " + total + " | " +
      "Высокая: " + levels.high + " | " +
      "Средняя: " + levels.medium + " | " +
      "Низкая: " + levels.low
    );
  }

  /**
   * Синхронизация режима визуализации векторного поля потоков.
   */
  function syncFlowField(
    enabledCheckbox,
    mode,
    density,
    animationSpeed,
    colorScheme
  ) {
    if (!window.pvu3d || !window.pvu3d.setFlowFieldMode) {
      return [
        enabledCheckbox,
        mode,
        density,
        animationSpeed,
        colorScheme,
        "Векторное поле недоступно"
      ];
    }

    var enabled = Array.isArray(enabledCheckbox) && enabledCheckbox.includes("enabled");

    if (!enabled) {
      window.pvu3d.setFlowFieldMode("off");
      return [
        [],
        mode,
        density,
        animationSpeed,
        colorScheme,
        "Потоки выключены"
      ];
    }

    // Включить режим с параметрами
    window.pvu3d.setFlowFieldMode(mode, {
      density: density / 100,
      animationSpeed: animationSpeed,
      colorScheme: colorScheme,
    });

    var stats = window.pvu3d.getFlowFieldStats();
    var statsText = _formatFlowFieldStats(stats);

    return [
      ["enabled"],
      mode,
      density,
      animationSpeed,
      colorScheme,
      statsText
    ];
  }

  function _formatFlowFieldStats(stats) {
    if (!stats.enabled) {
      return "Потоки выключены";
    }

    if (!stats.dataLoaded) {
      return "Данные векторного поля не загружены";
    }

    var modeNames = {
      arrows: "Стрелки",
      streamlines: "Линии тока",
      particles: "Частицы"
    };

    var modeName = modeNames[stats.mode] || stats.mode;
    var objectCount = stats.mode === "particles" ? stats.particleCount : stats.visibleObjects;

    return (
      "Режим: " + modeName + " | " +
      "Объектов: " + objectCount + " | " +
      "Векторов: " + stats.vectorCount
    );
  }

  function syncComparisonMode(
    enabledCheckbox,
    beforeSource,
    afterSource,
    split,
    orientation,
    syncCamerasCheckbox,
    diffMode
  ) {
    if (!window.pvu3d || !window.pvu3d.setComparisonMode) {
      return [
        enabledCheckbox,
        beforeSource,
        afterSource,
        split,
        orientation,
        syncCamerasCheckbox,
        diffMode,
        "Режим сравнения недоступен",
        ""
      ];
    }

    var enabled = Array.isArray(enabledCheckbox) && enabledCheckbox.includes("enabled");
    var syncCameras = Array.isArray(syncCamerasCheckbox) && syncCamerasCheckbox.includes("sync");

    if (!enabled) {
      window.pvu3d.setComparisonMode("off");
      return [
        [],
        beforeSource,
        afterSource,
        split,
        orientation,
        ["sync"],
        diffMode,
        "Режим сравнения выключен",
        ""
      ];
    }

    if (!beforeSource || !afterSource) {
      return [
        ["enabled"],
        beforeSource,
        afterSource,
        split,
        orientation,
        syncCameras ? ["sync"] : [],
        diffMode,
        "Выберите оба источника для сравнения",
        ""
      ];
    }

    if (beforeSource === afterSource) {
      return [
        ["enabled"],
        beforeSource,
        afterSource,
        split,
        orientation,
        syncCameras ? ["sync"] : [],
        diffMode,
        "⚠️ Выберите разные источники для сравнения",
        ""
      ];
    }

    // Check if diff mode changed
    var stats = window.pvu3d.getComparisonStats();
    if (stats.enabled && stats.diffMode !== diffMode && window.pvu3d.updateComparisonDiffMode) {
      // Update diff mode without reloading data
      window.pvu3d.updateComparisonDiffMode(diffMode);
    } else {
      // Load comparison data asynchronously
      window.pvu3d.loadComparisonData(beforeSource, afterSource)
        .then(function(comparison) {
          // Enable comparison mode
          window.pvu3d.setComparisonMode("split", {
            split: split,
            orientation: orientation,
            syncCameras: syncCameras,
            diffMode: diffMode
          });
        })
        .catch(function(error) {
          console.error("[PVU3D Bridge] Failed to load comparison data:", error);
        });
    }

    var compatibilityText = _formatCompatibility(stats.compatibility);
    var statsText = _formatComparisonStats(stats);

    return [
      ["enabled"],
      beforeSource,
      afterSource,
      split,
      orientation,
      syncCameras ? ["sync"] : [],
      diffMode,
      compatibilityText,
      statsText
    ];
  }

  function _formatCompatibility(compatibility) {
    if (!compatibility) {
      return "Загрузка данных сравнения...";
    }

    if (!compatibility.is_compatible) {
      return "⚠️ Несовместимо: " + compatibility.summary;
    }

    return "✓ Совместимо: " + compatibility.summary;
  }

  function _formatComparisonStats(stats) {
    if (!stats.enabled) {
      return "";
    }

    if (!stats.dataLoaded) {
      return "Загрузка данных...";
    }

    var orientationLabel = stats.orientation === "vertical" ? "Вертикальное" : "Горизонтальное";
    var splitPercent = Math.round(stats.split * 100);

    return (
      "До: " + (stats.beforeLabel || "—") + " | " +
      "После: " + (stats.afterLabel || "—") + " | " +
      "Разделение: " + splitPercent + "/" + (100 - splitPercent) + " | " +
      "Ориентация: " + orientationLabel
    );
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    pvu3dBridge: {
      switchRenderMode: switchRenderMode,
      updateViewer3d: updateViewer3d,
      syncTransformControls: syncTransformControls,
      syncBloomControls: syncBloomControls,
      syncSSAOControls: syncSSAOControls,
      syncMeasurementMode: syncMeasurementMode,
      captureScreenshotAction: captureScreenshotAction,
      syncHeatmapMode: syncHeatmapMode,
      syncClippingMode: syncClippingMode,
      syncLODMode: syncLODMode,
      syncFlowField: syncFlowField,
      syncComparisonMode: syncComparisonMode,
    },
  });
})();
