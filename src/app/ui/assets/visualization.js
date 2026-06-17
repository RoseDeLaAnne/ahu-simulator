(function () {
  // Все <object> с мнемосхемой в разных лейаутах: legacy 2D, вкладка «Схема»
  // concept03 и 2D-fallback внутри 3D-вьюпорта. ID должны совпадать с
  // render_modes/scene2d.py, concept03/central_canvas.py и
  // concept03/scene3d_overlay.py (есть pytest-гард).
  var MNEMONIC_OBJECT_IDS = [
    "mnemonic-svg-object",
    "concept03-mnemonic-svg-object",
    "concept03-fallback-mnemonic-object",
  ];

  // Chromium не грузит <object data=svg> внутри display:none — документ
  // появляется только при первом показе вкладки «Схема». Храним последние
  // сигналы и доигрываем их на событии load каждого объекта.
  var lastSignals = null;

  function setText(svgDocument, elementId, value) {
    const element = svgDocument.getElementById(elementId);
    if (element) {
      element.textContent = value || "";
    }
  }

  function applySignal(svgDocument, signal) {
    const group = svgDocument.getElementById(signal.visual_id);
    if (!group) {
      return;
    }

    group.setAttribute("data-state", signal.state || "normal");
    group.style.setProperty("--signal-intensity", String(signal.intensity || 0.65));
    group.classList.toggle("is-active", Boolean(signal.active));

    setText(svgDocument, signal.visual_id + "__value", signal.value);
    setText(svgDocument, signal.visual_id + "__detail", signal.detail);
    setText(svgDocument, signal.visual_id + "__alarm_text", signal.alarm_text);

    const alarmBadge = svgDocument.getElementById(signal.visual_id + "__alarm");
    if (alarmBadge) {
      alarmBadge.style.opacity = signal.alarm_text ? "1" : "0";
    }
  }

  function renderIntoSvg(svgDocument, signals) {
    ["nodes", "sensors", "flows"].forEach(function (sectionName) {
      const section = signals[sectionName] || {};
      Object.keys(section).forEach(function (signalId) {
        applySignal(svgDocument, section[signalId]);
      });
    });

    svgDocument.documentElement.setAttribute("data-status", signals.status || "normal");
    setText(svgDocument, "scene-summary", signals.summary);
    setText(
      svgDocument,
      "scene-status",
      "Статус: " + (signals.status || "normal").toUpperCase()
    );
    setText(
      svgDocument,
      "scene-bindings-version",
      "bindings v" + String(signals.bindings_version || 1)
    );
  }

  function applyToObject(objectElement) {
    if (!lastSignals || !objectElement) {
      return false;
    }
    const doc = objectElement.contentDocument;
    if (doc && doc.documentElement && doc.getElementById("scene-summary")) {
      renderIntoSvg(doc, lastSignals);
      return true;
    }
    return false;
  }

  function watchObject(objectElement) {
    if (objectElement.dataset.mnemonicWatched === "1") {
      return;
    }
    objectElement.dataset.mnemonicWatched = "1";
    objectElement.addEventListener("load", function () {
      applyToObject(objectElement);
    });
  }

  function renderMnemonic(signals) {
    if (!signals) {
      return window.dash_clientside.no_update;
    }
    lastSignals = signals;

    var appliedCount = 0;
    MNEMONIC_OBJECT_IDS.forEach(function (objectId) {
      const objectElement = document.getElementById(objectId);
      if (!objectElement) {
        return;
      }
      watchObject(objectElement);
      if (applyToObject(objectElement)) {
        appliedCount += 1;
      }
    });

    if (appliedCount === 0) {
      return "mnemonic-pending";
    }
    return signals.summary;
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    pvuVisualization: {
      renderMnemonic: renderMnemonic,
    },
  });
})();
