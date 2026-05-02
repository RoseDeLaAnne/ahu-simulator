(function () {
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

  function renderMnemonic(signals) {
    if (!signals) {
      return window.dash_clientside.no_update;
    }

    const objectElement = document.getElementById("mnemonic-svg-object");
    if (!objectElement) {
      return window.dash_clientside.no_update;
    }

    const apply = function () {
      if (objectElement.contentDocument) {
        renderIntoSvg(objectElement.contentDocument, signals);
      }
    };

    if (objectElement.contentDocument && objectElement.contentDocument.documentElement) {
      apply();
      return signals.summary;
    }

    const onLoad = function () {
      apply();
      objectElement.removeEventListener("load", onLoad);
    };
    objectElement.addEventListener("load", onLoad, { once: true });
    return "mnemonic-pending";
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    pvuVisualization: {
      renderMnemonic: renderMnemonic,
    },
  });
})();
