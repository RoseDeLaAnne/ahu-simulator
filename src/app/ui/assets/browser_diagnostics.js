(function () {
  function detectBrowserLabel() {
    if (navigator.userAgentData && Array.isArray(navigator.userAgentData.brands)) {
      const brands = navigator.userAgentData.brands
        .map(function (entry) {
          return [entry.brand, entry.version].filter(Boolean).join(" ");
        })
        .filter(Boolean);
      if (brands.length) {
        return brands.join(", ");
      }
    }
    return navigator.userAgent || "Unknown browser";
  }

  function detectPlatform() {
    if (navigator.userAgentData && navigator.userAgentData.platform) {
      return navigator.userAgentData.platform;
    }
    return navigator.platform || "Unknown platform";
  }

  function detectWebGL() {
    const webgl2Canvas = document.createElement("canvas");
    const webglCanvas = document.createElement("canvas");
    const webgl2 = webgl2Canvas.getContext("webgl2");
    const webgl =
      webgl2 ||
      webglCanvas.getContext("webgl") ||
      webglCanvas.getContext("experimental-webgl");
    const result = {
      webgl_supported: Boolean(webgl),
      webgl2_supported: Boolean(webgl2),
      renderer: null,
      vendor: null,
      debug_renderer_info: false,
      max_texture_size: null,
      max_viewport_width: null,
      max_viewport_height: null,
    };

    if (!webgl) {
      return result;
    }

    try {
      const debugInfo = webgl.getExtension("WEBGL_debug_renderer_info");
      if (debugInfo) {
        result.debug_renderer_info = true;
        result.renderer = webgl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        result.vendor = webgl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
      } else {
        result.renderer = webgl.getParameter(webgl.RENDERER);
        result.vendor = webgl.getParameter(webgl.VENDOR);
      }

      result.max_texture_size = webgl.getParameter(webgl.MAX_TEXTURE_SIZE);
      const viewport = webgl.getParameter(webgl.MAX_VIEWPORT_DIMS);
      if (viewport && viewport.length >= 2) {
        result.max_viewport_width = viewport[0];
        result.max_viewport_height = viewport[1];
      }
    } catch (error) {
      result.renderer = "detection-error";
      result.vendor = String(error);
    }

    return result;
  }

  function collectBrowserCapabilities() {
    const webgl = detectWebGL();
    return {
      browser_label: detectBrowserLabel(),
      platform: detectPlatform(),
      online: typeof navigator.onLine === "boolean" ? navigator.onLine : null,
      secure_context: Boolean(window.isSecureContext),
      hardware_concurrency: navigator.hardwareConcurrency || null,
      device_memory_gb: navigator.deviceMemory || null,
      device_pixel_ratio: window.devicePixelRatio || 1,
      viewport_width: window.innerWidth || null,
      viewport_height: window.innerHeight || null,
      screen_width: window.screen && window.screen.width ? window.screen.width : null,
      screen_height: window.screen && window.screen.height ? window.screen.height : null,
      diagnostics_timestamp: new Date().toISOString(),
      ...webgl,
    };
  }

  function getNonSearchableSelect(node) {
    if (!node || typeof node.closest !== "function") {
      return null;
    }

    const root = node.closest(".Select");
    if (!root) {
      return null;
    }

    const host = root.closest(
      [
        "#scenario-select",
        "#control-mode",
        "#scene3d-model-select",
        "#scene3d-display-mode",
        "#scene3d-camera-preset",
        "#scene3d-scenario-select",
        "#scene3d-room-select",
        "#scene3d-room-preset",
        "#scene3d-control-mode",
      ].join(",")
    );

    return host ? root : null;
  }

  function hardenDropdownInput(selectRoot) {
    if (!selectRoot) {
      return;
    }

    const input = selectRoot.querySelector("input");
    if (!input) {
      return;
    }

    input.setAttribute("readonly", "readonly");
    input.setAttribute("inputmode", "none");
    input.setAttribute("autocomplete", "off");
    input.setAttribute("autocorrect", "off");
    input.setAttribute("spellcheck", "false");
    input.setAttribute("tabindex", "-1");
  }

  function hardenAllDropdowns() {
    document
      .querySelectorAll(
        [
          "#scenario-select .Select",
          "#control-mode .Select",
          "#scene3d-model-select .Select",
          "#scene3d-display-mode .Select",
          "#scene3d-camera-preset .Select",
          "#scene3d-scenario-select .Select",
          "#scene3d-room-select .Select",
          "#scene3d-room-preset .Select",
          "#scene3d-control-mode .Select",
        ].join(",")
      )
      .forEach(hardenDropdownInput);
  }

  function blurDropdownInput(target) {
    const selectRoot = getNonSearchableSelect(target);
    if (!selectRoot) {
      return;
    }

    hardenDropdownInput(selectRoot);
    const input = selectRoot.querySelector("input");
    if (!input) {
      return;
    }

    [0, 40, 120].forEach(function (delay) {
      window.setTimeout(function () {
        hardenDropdownInput(selectRoot);
        if (document.activeElement === input) {
          input.blur();
        }
      }, delay);
    });
  }

  document.addEventListener("DOMContentLoaded", hardenAllDropdowns, {
    once: true,
  });

  document.addEventListener("focusin", function (event) {
    blurDropdownInput(event.target);
  });

  document.addEventListener(
    "touchstart",
    function (event) {
      blurDropdownInput(event.target);
    },
    { passive: true }
  );

  new MutationObserver(hardenAllDropdowns).observe(document.documentElement, {
    childList: true,
    subtree: true,
  });

  window.setInterval(hardenAllDropdowns, 500);

  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    pvuDiagnostics: {
      collectBrowserCapabilities: collectBrowserCapabilities,
    },
  });
})();
