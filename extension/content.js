(function () {
  console.log("Aegis-Tetris Content Script Loaded.");

  let overlayContainer = null;
  let shadowRoot = null;
  
  // State configurations
  let settings = {
    maskEnabled: false,
    maskMode: "ghost",
    heuristicEnabled: true,
    isCalibrating: false
  };

  // Keyboard telemetry tracking
  let startFrame = 0;
  let currentKeyStates = {};

  // Initialize
  chrome.storage.local.get(["maskEnabled", "maskMode", "heuristicEnabled", "isCalibrating"], (result) => {
    settings.maskEnabled = result.maskEnabled !== undefined ? result.maskEnabled : false;
    settings.maskMode = result.maskMode || "ghost";
    settings.heuristicEnabled = result.heuristicEnabled !== undefined ? result.heuristicEnabled : true;
    settings.isCalibrating = result.isCalibrating !== undefined ? result.isCalibrating : false;

    createOverlay();
    applySettings();
  });

  // Listen to popup settings updates
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "updateSettings") {
      Object.assign(settings, message.settings);
      applySettings();
      sendResponse({ status: "applied" });
    } else if (message.action === "triggerFlash") {
      triggerHeuristicFlash();
      sendResponse({ status: "flashed" });
    } else if (message.action === "triggerIntervention") {
      showGemmaIntervention(message.message);
      sendResponse({ status: "intervened" });
    }
    return true;
  });

  // Main Overlay Creation using Shadow DOM
  function createOverlay() {
    if (overlayContainer) return;

    overlayContainer = document.createElement("div");
    overlayContainer.id = "aegis-overlay-root";
    // Place in fixed coordinates
    overlayContainer.style.position = "fixed";
    overlayContainer.style.top = "150px";
    overlayContainer.style.left = "40%";
    overlayContainer.style.width = "300px";
    overlayContainer.style.height = "600px";
    overlayContainer.style.zIndex = "999999";
    overlayContainer.style.display = "none";

    // Load saved bounds if they exist
    chrome.storage.local.get(["overlayBounds"], (result) => {
      if (result.overlayBounds) {
        const bounds = result.overlayBounds;
        overlayContainer.style.top = bounds.top || "150px";
        overlayContainer.style.left = bounds.left || "40%";
        overlayContainer.style.width = bounds.width || "300px";
        overlayContainer.style.height = bounds.height || "600px";
      }
    });

    shadowRoot = overlayContainer.attachShadow({ mode: "open" });

    // Styles for inside the Shadow DOM
    const style = document.createElement("style");
    style.textContent = `
      :host {
        display: block;
        box-sizing: border-box;
      }
      
      .aegis-mask {
        width: 100%;
        height: 100%;
        position: relative;
        border-radius: 8px;
        transition: background-color 0.15s ease, opacity 0.15s ease;
        box-sizing: border-box;
      }

      /* Mask Modes */
      .aegis-mask.ghost-mode {
        background-color: rgba(13, 9, 21, 0.85);
        border: 2px solid rgba(139, 92, 246, 0.2);
        box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.9);
      }

      .aegis-mask.blind-mode {
        background-color: rgb(13, 9, 21);
        border: 2px solid rgba(139, 92, 246, 0.4);
        box-shadow: inset 0 0 50px rgba(0, 0, 0, 1);
      }

      .aegis-mask.transparent-mode {
        background-color: rgba(0, 0, 0, 0) !important;
        border: 2px solid rgba(6, 182, 212, 0.6) !important;
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.3) !important;
      }

      /* Calibration Controls */
      .calibration-frame {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 2px dashed #06b6d4;
        background-color: rgba(6, 182, 212, 0.15);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border-radius: 8px;
        cursor: move;
        z-index: 10;
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.3);
      }

      .calibration-label {
        font-family: 'Outfit', sans-serif;
        color: #f3f4f6;
        background: #0d0915;
        border: 1px solid #06b6d4;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 1px;
        pointer-events: none;
        text-shadow: 0 0 5px rgba(6, 182, 212, 0.5);
      }

      .resize-handle {
        position: absolute;
        width: 16px;
        height: 16px;
        background-color: #06b6d4;
        bottom: 0;
        right: 0;
        cursor: se-resize;
        border-bottom-right-radius: 8px;
        clip-path: polygon(100% 0, 0 100%, 100% 100%);
      }

      /* Gemma Advice Intervention overlay */
      .gemma-alert {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 350px;
        background: rgba(13, 9, 21, 0.95);
        border: 2px solid #8b5cf6;
        box-shadow: 0 0 25px rgba(139, 92, 246, 0.5);
        border-radius: 12px;
        padding: 16px;
        font-family: 'Outfit', sans-serif;
        color: #f3f4f6;
        display: none;
        z-index: 9999999;
        animation: slideIn 0.3s ease-out;
      }

      .gemma-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(139, 92, 246, 0.2);
        padding-bottom: 6px;
      }

      .gemma-logo {
        width: 24px;
        height: 24px;
        border-radius: 4px;
        border: 1px solid #8b5cf6;
      }

      .gemma-title {
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #8b5cf6;
      }

      .gemma-content {
        font-size: 11px;
        line-height: 1.4;
        color: #d1d5db;
      }

      .gemma-close {
        position: absolute;
        top: 10px;
        right: 10px;
        background: transparent;
        color: #9ca3af;
        border: none;
        cursor: pointer;
        font-size: 14px;
      }

      @keyframes slideIn {
        from { transform: translateY(100px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
      }
    `;

    // Mask layout
    const mask = document.createElement("div");
    mask.className = "aegis-mask";
    mask.id = "aegisMask";

    // Calibration box
    const calibration = document.createElement("div");
    calibration.className = "calibration-frame";
    calibration.id = "calibrationFrame";
    calibration.innerHTML = `
      <div class="calibration-label">CALIBRATE OVERLAY</div>
      <div class="resize-handle" id="resizeHandle"></div>
    `;

    // Gemma alert box
    const gemmaAlert = document.createElement("div");
    gemmaAlert.className = "gemma-alert";
    gemmaAlert.id = "gemmaAlert";
    gemmaAlert.innerHTML = `
      <button class="gemma-close" id="gemmaClose">×</button>
      <div class="gemma-header">
        <div class="gemma-title">GEMMA TACTICAL SPOTTER</div>
      </div>
      <div class="gemma-content" id="gemmaContent">Evaluating board setup...</div>
    `;

    shadowRoot.appendChild(style);
    shadowRoot.appendChild(mask);
    shadowRoot.appendChild(calibration);
    shadowRoot.appendChild(gemmaAlert);
    
    document.body.appendChild(overlayContainer);

    // Setup interactive events for moving and resizing during calibration
    setupDragAndResize(calibration);

    // Setup gemma close click
    shadowRoot.getElementById("gemmaClose").addEventListener("click", () => {
      gemmaAlert.style.display = "none";
    });
  }

  // Handle Dragging and Resizing
  function setupDragAndResize(calibrationEl) {
    const mask = shadowRoot.getElementById("aegisMask");
    const handle = shadowRoot.getElementById("resizeHandle");
    
    let activeDrag = false;
    let activeResize = false;
    
    let startX, startY, startTop, startLeft, startWidth, startHeight;

    // Drag start
    calibrationEl.addEventListener("mousedown", (e) => {
      if (e.target === handle) return;
      activeDrag = true;
      startX = e.clientX;
      startY = e.clientY;
      startTop = parseInt(overlayContainer.style.top, 10);
      startLeft = parseInt(overlayContainer.style.left, 10);
      e.preventDefault();
    });

    // Resize start
    handle.addEventListener("mousedown", (e) => {
      activeResize = true;
      startX = e.clientX;
      startY = e.clientY;
      startWidth = parseInt(overlayContainer.style.width, 10);
      startHeight = parseInt(overlayContainer.style.height, 10);
      e.stopPropagation();
      e.preventDefault();
    });

    // Move & Resize process
    window.addEventListener("mousemove", (e) => {
      if (activeDrag) {
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        overlayContainer.style.top = `${startTop + dy}px`;
        overlayContainer.style.left = `${startLeft + dx}px`;
      } else if (activeResize) {
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        overlayContainer.style.width = `${Math.max(100, startWidth + dx)}px`;
        overlayContainer.style.height = `${Math.max(200, startHeight + dy)}px`;
      }
    });

    // Mouse release
    window.addEventListener("mouseup", () => {
      if (activeDrag || activeResize) {
        activeDrag = false;
        activeResize = false;
        
        // Cache coordinates
        chrome.storage.local.set({
          overlayBounds: {
            top: overlayContainer.style.top,
            left: overlayContainer.style.left,
            width: overlayContainer.style.width,
            height: overlayContainer.style.height
          }
        });
      }
    });
  }

  // Applying Settings to DOM elements
  function applySettings() {
    if (!overlayContainer) return;

    const mask = shadowRoot.getElementById("aegisMask");
    const calibration = shadowRoot.getElementById("calibrationFrame");

    // Mask display
    if (settings.maskEnabled) {
      overlayContainer.style.display = "block";
      
      // Select Mode Class
      mask.className = "aegis-mask";
      if (settings.maskMode === "ghost") {
        mask.classList.add("ghost-mode");
      } else {
        mask.classList.add("blind-mode");
      }

      // If locked (not calibrating), click events must go through to Tetr.io
      if (settings.isCalibrating) {
        overlayContainer.style.pointerEvents = "auto";
        calibration.style.display = "flex";
      } else {
        overlayContainer.style.pointerEvents = "none";
        calibration.style.display = "none";
      }
    } else {
      overlayContainer.style.display = "none";
    }
  }

  // 3-Bag Peek Heuristic: Momentarily flash mask transparent
  function triggerHeuristicFlash() {
    if (!settings.maskEnabled || !settings.heuristicEnabled) return;

    const mask = shadowRoot.getElementById("aegisMask");
    mask.classList.add("transparent-mode");

    // After 100 milliseconds, return to locked darkness
    setTimeout(() => {
      mask.classList.remove("transparent-mode");
    }, 100);
  }

  // Show Gemma Spatial Intervention popup on frontend
  function showGemmaIntervention(message) {
    const alertBox = shadowRoot.getElementById("gemmaAlert");
    const content = shadowRoot.getElementById("gemmaContent");
    
    content.innerText = message;
    alertBox.style.display = "block";
  }

  // Telemetry Keypress Hooking mapping
  const CONTROL_MAP = {
    "ArrowLeft": "moveLeft",
    "ArrowRight": "moveRight",
    "ArrowDown": "softDrop",
    "ArrowUp": "rotateCW",
    "Space": "hardDrop",
    "KeyZ": "rotateCCW",
    "KeyX": "rotateCW",
    "KeyC": "hold",
    "ShiftLeft": "hold",
    "KeyA": "rotate180"
  };

  // Keyboard capture event listeners
  window.addEventListener("keydown", (e) => {
    // If not enabled or calibrating, do not intercept inputs
    if (!settings.maskEnabled || settings.isCalibrating) return;

    const control = CONTROL_MAP[e.code] || CONTROL_MAP[e.key];
    if (control && !currentKeyStates[control]) {
      currentKeyStates[control] = true;
      sendTelemetryToBackground("keydown", control);
    }
  });

  window.addEventListener("keyup", (e) => {
    if (!settings.maskEnabled || settings.isCalibrating) return;

    const control = CONTROL_MAP[e.code] || CONTROL_MAP[e.key];
    if (control && currentKeyStates[control]) {
      currentKeyStates[control] = false;
      sendTelemetryToBackground("keyup", control);
    }
  });

  function sendTelemetryToBackground(type, key) {
    if (!startFrame) {
      startFrame = Date.now();
    }
    
    // Calculate simulated subframe frame timing (60 fps conversion)
    const elapsedMs = Date.now() - startFrame;
    const rawFrame = (elapsedMs / 1000) * 60;
    const frame = Math.floor(rawFrame);
    const subframe = parseFloat((rawFrame - frame).toFixed(2));

    const gameEvent = {
      frame: frame,
      type: type,
      data: {
        key: key,
        subframe: subframe
      }
    };

    chrome.runtime.sendMessage({
      action: "relayGameEvent",
      event: gameEvent
    }).catch(() => {
      // Ignore background communication silences
    });
  }
})();
