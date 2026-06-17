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
  var currentActiveTab = null;

  var PAGE_IDS = ["dashboard", "equipment", "control", "analytics", "library", "settings"];

  function pageFromHref(href) {
    if (!href) {
      return null;
    }
    var match = /[?&]page=([^&#]+)/.exec(href);
    if (!match) {
      return null;
    }
    var candidate = decodeURIComponent(match[1]).trim().toLowerCase();
    return PAGE_IDS.indexOf(candidate) !== -1 ? candidate : null;
  }

  function setShellActivePage(page) {
    var shell = document.getElementById("concept03-shell");
    if (shell) {
      shell.setAttribute("data-active-page", page);
    }
    document.querySelectorAll("[id^='footer-nav-']").forEach(function (link) {
      var pid = link.id.replace("footer-nav-", "");
      link.classList.toggle("c03-footer-nav__link--active", pid === page);
    });
    document.querySelectorAll(".c03-mobile-bottom-nav__link").forEach(function (link) {
      var pid = pageFromHref(link.getAttribute("href"));
      link.classList.toggle("c03-mobile-bottom-nav__link--active", pid === page);
    });
    document.querySelectorAll(".c03-mobile-offcanvas__link").forEach(function (link) {
      var pid = pageFromHref(link.getAttribute("href"));
      link.classList.toggle("c03-mobile-offcanvas__link--active", pid === page);
    });
  }

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
    currentActiveTab = activeTab;
    updateCentralTabAttr(activeTab);
    applyBottomStripState();
    applyFocusModeState();
    collapseAboutCardsOnMobile();
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

  function handleNavIntent(event) {
    // Перехват навигации на САМОЙ РАННЕЙ фазе (pointerdown, capture): ставим
    // data-active-page сразу при нажатии, не дожидаясь click/круга колбэков
    // Dash. Дашборд тут же скрывается (display:none) → RAF-гард 3D-сцены
    // прекращает рендер, освобождая главный поток. Так контент вкладок
    // меняется мгновенно даже когда 3D активно нагружает поток (замечание:
    // «задержка пару секунд при переключении вкладок»).
    var navLink = event.target.closest && event.target.closest("a[href*='page=']");
    if (!navLink) {
      return;
    }
    var navPage = pageFromHref(navLink.getAttribute("href"));
    if (navPage) {
      setShellActivePage(navPage);
      setMobileMenuOpen(false);
    }
  }

  function bindCameraControls() {
    if (controlsBound) {
      return;
    }
    controlsBound = true;
    // pointerdown (capture) — раньше click; мгновенно переключает страницу.
    document.addEventListener("pointerdown", handleNavIntent, true);
    document.addEventListener("click", function (event) {
      // Мгновенное переключение страниц: ставим data-active-page СИНХРОННО на клик,
      // не дожидаясь круга колбэков Dash. dcc.Link параллельно обновит URL без
      // перезагрузки, а серверные колбэки досинхронизируют подсветку/состояние в
      // фоне. Так контент вкладок (Дашборд/Оборудование/…) меняется сразу.
      var navLink = event.target.closest("a[href*='page=']");
      if (navLink) {
        var navPage = pageFromHref(navLink.getAttribute("href"));
        if (navPage) {
          setShellActivePage(navPage);
          setMobileMenuOpen(false);
        }
      }
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
      var stripToggle = event.target.closest("[data-strip-toggle]");
      if (stripToggle) {
        toggleBottomStrip();
        return;
      }
      var focusToggle = event.target.closest("[data-focus-toggle]");
      if (focusToggle) {
        toggleFocusMode();
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

  function collapseAboutCardsOnMobile() {
    // На телефоне раскрытая карточка «Об установке» закрывает почти весь
    // 3D-канвас — сворачиваем её один раз при первом sync, дальше пользователь
    // волен раскрыть её сам (флаг не даёт сворачивать повторно).
    if (!window.matchMedia || !window.matchMedia("(max-width: 780px)").matches) {
      return;
    }
    ["concept03-scene-about", "concept03-scene-about-2d"].forEach(function (id) {
      var card = document.getElementById(id);
      if (card && !card.hasAttribute("data-mobile-collapsed")) {
        card.removeAttribute("open");
        card.setAttribute("data-mobile-collapsed", "true");
      }
    });
  }

  function updateCentralTabAttr(activeTab) {
    var canvas = document.getElementById("central-canvas");
    if (canvas) {
      canvas.setAttribute("data-central-tab", activeTab || "");
    }
  }

  var STRIP_COLLAPSE_KEY = "concept03.bottomStrip.collapsed";

  function applyBottomStripState() {
    // Восстанавливаем свёрнутость нижней полосы из localStorage при каждом
    // sync — shell пересобирается навигацией Dash и теряет класс.
    var shell = document.getElementById("concept03-shell");
    if (!shell) {
      return;
    }
    var collapsed = false;
    try {
      collapsed = window.localStorage.getItem(STRIP_COLLAPSE_KEY) === "1";
    } catch (err) {
      collapsed = false;
    }
    shell.classList.toggle("c03-shell--strip-collapsed", collapsed);
    var button = document.getElementById("concept03-bottom-strip-toggle");
    if (button) {
      button.setAttribute("aria-expanded", collapsed ? "false" : "true");
    }
  }

  function toggleBottomStrip() {
    var shell = document.getElementById("concept03-shell");
    if (!shell) {
      return;
    }
    var collapsed = shell.classList.toggle("c03-shell--strip-collapsed");
    try {
      window.localStorage.setItem(STRIP_COLLAPSE_KEY, collapsed ? "1" : "0");
    } catch (err) {
      /* приватный режим — состояние живёт только в текущей сессии */
    }
    var button = document.getElementById("concept03-bottom-strip-toggle");
    if (button) {
      button.setAttribute("aria-expanded", collapsed ? "false" : "true");
    }
  }

  var FOCUS_MODE_KEY = "concept03.centralCanvas.focus";

  function applyFocusModeState() {
    // Восстанавливаем фокус-режим центральной области из localStorage при
    // каждом sync — shell пересобирается навигацией Dash и теряет класс.
    // По умолчанию (нет сохранённого выбора) фокус-режим ВКЛЮЧЕН: дашборд
    // открывается с развёрнутой центральной областью. Явное «Свернуть»
    // сохраняет "0" и отключает его до следующего «Развернуть».
    var shell = document.getElementById("concept03-shell");
    if (!shell) {
      return;
    }
    var focused = true;
    try {
      focused = window.localStorage.getItem(FOCUS_MODE_KEY) !== "0";
    } catch (err) {
      focused = true;
    }
    shell.classList.toggle("c03-shell--focus", focused);
    syncFocusToggleButton(focused);
  }

  function toggleFocusMode() {
    var shell = document.getElementById("concept03-shell");
    if (!shell) {
      return;
    }
    var focused = shell.classList.toggle("c03-shell--focus");
    try {
      window.localStorage.setItem(FOCUS_MODE_KEY, focused ? "1" : "0");
    } catch (err) {
      /* приватный режим — состояние живёт только в текущей сессии */
    }
    syncFocusToggleButton(focused);
    // 3D-вьювер слушает контейнер через ResizeObserver, но даём ему явный
    // пинок на случай, если переход размера произойдёт без ресайза элемента.
    if (window.requestAnimationFrame) {
      window.requestAnimationFrame(function () {
        window.dispatchEvent(new Event("resize"));
      });
    }
  }

  function syncFocusToggleButton(focused) {
    var button = document.getElementById("concept03-focus-toggle");
    if (button) {
      button.setAttribute("aria-pressed", focused ? "true" : "false");
    }
  }

  function handleCameraTool(toolId) {
    // Camera/fullscreen tools only act on the 3D sub-tab; they leak into the
    // always-present substrip on 2D/parameters/trends/alarms/docs otherwise.
    if (currentActiveTab !== "3d") {
      return;
    }
    if (toolId === "view-fullscreen") {
      var viewport = document.getElementById("concept03-scene-3d-viewport");
      if (viewport && viewport.requestFullscreen) {
        var request = viewport.requestFullscreen();
        if (request && typeof request.catch === "function") {
          request.catch(function (err) {
            console.warn("[concept03Overlay] fullscreen rejected:", err && err.message);
          });
        }
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

  function parseLenUnit(value, base, fallback) {
    if (!value) {
      return fallback;
    }
    var text = String(value).trim();
    if (text.charAt(text.length - 1) === "%") {
      return (parseFloat(text) / 100) * base;
    }
    var numeric = parseFloat(text);
    return Number.isFinite(numeric) ? numeric : fallback;
  }

  function fallbackAnchor(callout, layerW, layerH) {
    // Захватываем исходную (серверную) опорную точку выноски один раз: после
    // деклаттера мы перезаписываем --callout-x/y пикселями, и без кэша опорная
    // точка «уехала» бы каждый кадр. Dash при ререндере слоя создаёт новые
    // элементы со свежими процентами, так что захват срабатывает заново.
    if (!callout.dataset.calloutAnchorCaptured) {
      callout.dataset.calloutAnchorRawX = callout.style
        .getPropertyValue("--callout-x")
        .trim();
      callout.dataset.calloutAnchorRawY = callout.style
        .getPropertyValue("--callout-y")
        .trim();
      callout.dataset.calloutAnchorCaptured = "1";
    }
    return {
      x: parseLenUnit(callout.dataset.calloutAnchorRawX, layerW, layerW / 2),
      y: parseLenUnit(callout.dataset.calloutAnchorRawY, layerH, layerH / 2),
    };
  }

  function positionCallouts() {
    var layer = document.getElementById("concept03-callout-layer");
    if (!layer) {
      return;
    }
    if (window.pvu3d && window.pvu3d.hasFallback && window.pvu3d.hasFallback()) {
      setFallback(true);
      return;
    }
    var layerW = layer.clientWidth;
    var layerH = layer.clientHeight;
    if (layerW <= 0 || layerH <= 0) {
      return;
    }
    var canProject = window.pvu3d && window.pvu3d.getProjectedNode;
    var pad = 8;

    // 1. Собираем видимые выноски с опорной точкой (куда хочет встать) и
    //    измеренным размером карточки. Скрытые (defense-only в режиме оператора)
    //    имеют нулевой размер — пропускаем.
    var items = [];
    layer.querySelectorAll(".c03-callout").forEach(function (callout) {
      var rect = callout.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) {
        callout.removeAttribute("data-positioned");
        return;
      }
      var node = callout.getAttribute("data-scene-node");
      var anchorX = null;
      var anchorY = null;
      if (canProject && node) {
        var projected = window.pvu3d.getProjectedNode(node);
        if (projected) {
          anchorX = projected.x;
          anchorY = projected.y;
        }
      }
      if (anchorX === null) {
        var fallback = fallbackAnchor(callout, layerW, layerH);
        anchorX = fallback.x;
        anchorY = fallback.y;
      }
      items.push({
        el: callout,
        w: rect.width,
        h: rect.height,
        ax: anchorX,
        ay: anchorY,
        x: anchorX,
        y: anchorY,
      });
    });
    if (!items.length) {
      return;
    }

    // 1b. Препятствия — постоянные UI-элементы поверх сцены (карточка описания,
    //     компас, панель режима/модели, легенда 3D-вьювера). Выноски не должны
    //     их перекрывать.
    var layerRect = layer.getBoundingClientRect();
    var sceneRoot = layer.parentElement;
    var obstacleNodes = [];
    ["concept03-scene-about", "concept03-compass"].forEach(function (id) {
      var node = document.getElementById(id);
      if (node) {
        obstacleNodes.push(node);
      }
    });
    if (sceneRoot) {
      [".c03-scene-control-bar", ".viewer3d-legend"].forEach(function (selector) {
        var node = sceneRoot.querySelector(selector);
        if (node) {
          obstacleNodes.push(node);
        }
      });
    }
    var obstacleBoxes = obstacleNodes
      .map(function (node) {
        return node.getBoundingClientRect();
      })
      .filter(function (rect) {
        return rect.width > 0 && rect.height > 0;
      })
      .map(function (rect) {
        return {
          left: rect.left - layerRect.left,
          top: rect.top - layerRect.top,
          right: rect.right - layerRect.left,
          bottom: rect.bottom - layerRect.top,
        };
      });

    function pushOutOfObstacles(item) {
      var minX = item.w / 2 + pad;
      var maxX = layerW - item.w / 2 - pad;
      var minY = item.h / 2 + pad;
      var maxY = layerH - item.h / 2 - pad;
      obstacleBoxes.forEach(function (box) {
        var halfW = item.w / 2;
        var halfH = item.h / 2;
        var overlapX = Math.min(item.x + halfW, box.right) - Math.max(item.x - halfW, box.left);
        var overlapY = Math.min(item.y + halfH, box.bottom) - Math.max(item.y - halfH, box.top);
        if (overlapX <= 0 || overlapY <= 0) {
          return;
        }
        // Выбираем ближайший выход, который НЕ выводит карточку за пределы слоя.
        // Иначе препятствие у края слоя (большая карточка описания слева)
        // «прижимало» бы выноску к стене внутри себя.
        var candidates = [];
        var exitRight = box.right + halfW;
        if (exitRight <= maxX) {
          candidates.push({ axis: "x", value: exitRight, cost: exitRight - item.x });
        }
        var exitLeft = box.left - halfW;
        if (exitLeft >= minX) {
          candidates.push({ axis: "x", value: exitLeft, cost: item.x - exitLeft });
        }
        var exitDown = box.bottom + halfH;
        if (exitDown <= maxY) {
          candidates.push({ axis: "y", value: exitDown, cost: exitDown - item.y });
        }
        var exitUp = box.top - halfH;
        if (exitUp >= minY) {
          candidates.push({ axis: "y", value: exitUp, cost: item.y - exitUp });
        }
        if (!candidates.length) {
          return;
        }
        candidates.sort(function (left, right) {
          return left.cost - right.cost;
        });
        var chosen = candidates[0];
        if (chosen.axis === "x") {
          item.x = chosen.value;
        } else {
          item.y = chosen.value;
        }
      });
    }

    // 2. Засеваем сеткой вокруг опорных точек. Когда узлы компактной модели
    //    проецируются почти в одну точку, опорный «магнит» только сталкивал бы
    //    карточки обратно, поэтому притяжения нет: раскладываем карточки сеткой
    //    рядом с кластером и дальше только расталкиваем до отсутствия наложений.
    var columns = Math.max(1, Math.min(items.length, Math.floor(layerW / 172)));
    for (var s = 0; s < items.length; s += 1) {
      var col = s % columns;
      var row = Math.floor(s / columns);
      items[s].x = items[s].ax + (col - (columns - 1) / 2) * (items[s].w * 0.62);
      items[s].y = items[s].ay + (row - 1) * (items[s].h * 0.9);
    }

    // 3. Итеративное расталкивание перекрывающихся карточек, затем зажим в слой.
    var marginX = 5;
    var marginY = 4;
    for (var iter = 0; iter < 220; iter += 1) {
      // Сначала уводим карточки с препятствий, затем расталкиваем пары —
      // расталкивание идёт последним, поэтому именно отсутствие наложений
      // выносок друг на друга (главная жалоба) гарантируется в первую очередь.
      for (var o = 0; o < items.length; o += 1) {
        pushOutOfObstacles(items[o]);
      }
      for (var a = 0; a < items.length; a += 1) {
        for (var b = a + 1; b < items.length; b += 1) {
          var first = items[a];
          var second = items[b];
          var dx = second.x - first.x;
          var dy = second.y - first.y;
          var overlapX = (first.w + second.w) / 2 + marginX - Math.abs(dx);
          var overlapY = (first.h + second.h) / 2 + marginY - Math.abs(dy);
          if (overlapX > 0 && overlapY > 0) {
            if (overlapX < overlapY) {
              var dirX = dx === 0 ? (a % 2 ? 1 : -1) : dx > 0 ? 1 : -1;
              var pushX = (dirX * (overlapX / 2 + 0.5));
              first.x -= pushX;
              second.x += pushX;
            } else {
              var dirY = dy === 0 ? (a % 2 ? 1 : -1) : dy > 0 ? 1 : -1;
              var pushY = (dirY * (overlapY / 2 + 0.5));
              first.y -= pushY;
              second.y += pushY;
            }
          }
        }
      }
      for (var k = 0; k < items.length; k += 1) {
        var item = items[k];
        item.x = clamp(item.x, item.w / 2 + pad, layerW - item.w / 2 - pad);
        item.y = clamp(item.y, item.h / 2 + pad, layerH - item.h / 2 - pad);
      }
    }

    // 4. Применяем итоговые позиции.
    items.forEach(function (item) {
      item.el.style.setProperty("--callout-x", Math.round(item.x) + "px");
      item.el.style.setProperty("--callout-y", Math.round(item.y) + "px");
      item.el.setAttribute("data-positioned", "true");
    });

    // 5. Рисуем выносные линии: от края карточки к реальному узлу модели
    //    (ax, ay) + точка на узле. Без этого карточки «висят» по периметру и
    //    непонятно, что к чему относится (жалоба пользователя).
    drawLeaders(layer, layerW, layerH, items);
  }

  function ensureLeaderSvg(layer, layerW, layerH) {
    var svg = layer.querySelector(".c03-callout-leaders");
    if (!svg) {
      svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("class", "c03-callout-leaders");
      // Слой линий — первым ребёнком, чтобы оказаться ПОД карточками.
      layer.insertBefore(svg, layer.firstChild);
    }
    svg.setAttribute("width", layerW);
    svg.setAttribute("height", layerH);
    svg.setAttribute("viewBox", "0 0 " + layerW + " " + layerH);
    return svg;
  }

  // Точка пересечения отрезка центр-карточки→якорь с прямоугольной рамкой
  // карточки: линия выходит из ближайшего к узлу края, а не из центра.
  function edgePoint(item, towardX, towardY) {
    var dx = towardX - item.x;
    var dy = towardY - item.y;
    if (dx === 0 && dy === 0) {
      return { x: item.x, y: item.y };
    }
    var halfW = item.w / 2;
    var halfH = item.h / 2;
    var scale = Infinity;
    if (dx !== 0) {
      scale = Math.min(scale, halfW / Math.abs(dx));
    }
    if (dy !== 0) {
      scale = Math.min(scale, halfH / Math.abs(dy));
    }
    return { x: item.x + dx * scale, y: item.y + dy * scale };
  }

  function leaderStateSuffix(el) {
    var state = el.getAttribute("data-state");
    if (state === "warning") {
      return "--warn";
    }
    if (state === "alarm") {
      return "--alarm";
    }
    return "";
  }

  function drawLeaders(layer, layerW, layerH, items) {
    var svg = ensureLeaderSvg(layer, layerW, layerH);
    var ns = "http://www.w3.org/2000/svg";
    var frag = document.createDocumentFragment();
    items.forEach(function (item) {
      // Якорь зажимаем в слой, чтобы точка узла не уезжала за кадр.
      var anchorX = clamp(item.ax, 2, layerW - 2);
      var anchorY = clamp(item.ay, 2, layerH - 2);
      var start = edgePoint(item, anchorX, anchorY);
      var suffix = leaderStateSuffix(item.el);

      var line = document.createElementNS(ns, "line");
      line.setAttribute("class", "c03-callout-leaders__line c03-callout-leaders__line" + suffix);
      line.setAttribute("x1", Math.round(start.x));
      line.setAttribute("y1", Math.round(start.y));
      line.setAttribute("x2", Math.round(anchorX));
      line.setAttribute("y2", Math.round(anchorY));
      frag.appendChild(line);

      var dot = document.createElementNS(ns, "circle");
      dot.setAttribute("class", "c03-callout-leaders__dot c03-callout-leaders__dot" + suffix);
      dot.setAttribute("cx", Math.round(anchorX));
      dot.setAttribute("cy", Math.round(anchorY));
      dot.setAttribute("r", 3.5);
      frag.appendChild(dot);
    });
    // Полностью пересобираем содержимое: дешевле и без рассинхрона при
    // изменении числа видимых карточек (defense-only режим).
    while (svg.firstChild) {
      svg.removeChild(svg.firstChild);
    }
    svg.appendChild(frag);
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
