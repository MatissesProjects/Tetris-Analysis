document.addEventListener("DOMContentLoaded", () => {
  // UI Elements
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");
  const btnConnect = document.getElementById("btnConnect");
  
  const chkMask = document.getElementById("chkMask");
  const btnGhost = document.getElementById("btnGhost");
  const btnBlind = document.getElementById("btnBlind");
  const chkHeuristic = document.getElementById("chkHeuristic");
  const btnCalibrate = document.getElementById("btnCalibrate");

  let currentMode = "ghost";
  let isCalibrating = false;

  // Load saved configurations
  chrome.storage.local.get(
    ["maskEnabled", "maskMode", "heuristicEnabled", "wsConnected", "isCalibrating"],
    (result) => {
      // Default configurations if not set
      const maskEnabled = result.maskEnabled !== undefined ? result.maskEnabled : false;
      currentMode = result.maskMode || "ghost";
      const heuristicEnabled = result.heuristicEnabled !== undefined ? result.heuristicEnabled : true;
      const wsConnected = result.wsConnected !== undefined ? result.wsConnected : false;
      isCalibrating = result.isCalibrating !== undefined ? result.isCalibrating : false;

      // Update UI elements
      chkMask.checked = maskEnabled;
      chkHeuristic.checked = heuristicEnabled;
      updateModeButtons(currentMode);
      updateConnectionStatus(wsConnected);
      updateCalibrationButton(isCalibrating);
    }
  );

  // Sync WebSocket Status dynamically
  chrome.runtime.onMessage.addListener((message) => {
    if (message.action === "updateConnectionStatus") {
      updateConnectionStatus(message.connected);
    }
  });

  // Toggle Lookahead Mask
  chkMask.addEventListener("change", () => {
    const enabled = chkMask.checked;
    chrome.storage.local.set({ maskEnabled: enabled });
    broadcastSettingsChange({ maskEnabled: enabled });
  });

  // Switch to Ghost Mode
  btnGhost.addEventListener("click", () => {
    currentMode = "ghost";
    updateModeButtons("ghost");
    chrome.storage.local.set({ maskMode: "ghost" });
    broadcastSettingsChange({ maskMode: "ghost" });
  });

  // Switch to Blind Mode
  btnBlind.addEventListener("click", () => {
    currentMode = "blind";
    updateModeButtons("blind");
    chrome.storage.local.set({ maskMode: "blind" });
    broadcastSettingsChange({ maskMode: "blind" });
  });

  // Toggle 3-Bag Heuristic
  chkHeuristic.addEventListener("change", () => {
    const enabled = chkHeuristic.checked;
    chrome.storage.local.set({ heuristicEnabled: enabled });
    broadcastSettingsChange({ heuristicEnabled: enabled });
  });

  // Toggle Overlay Calibration
  btnCalibrate.addEventListener("click", () => {
    isCalibrating = !isCalibrating;
    updateCalibrationButton(isCalibrating);
    chrome.storage.local.set({ isCalibrating: isCalibrating });
    broadcastSettingsChange({ isCalibrating: isCalibrating });
    
    // Close popup to let user interact with the calibration overlay directly
    if (isCalibrating) {
      window.close();
    }
  });

  // Manual Engine Connection Request
  btnConnect.addEventListener("click", () => {
    chrome.runtime.sendMessage({ action: "toggleEngineConnection" });
  });

  // Helper functions
  function updateModeButtons(mode) {
    if (mode === "ghost") {
      btnGhost.classList.add("active");
      btnBlind.classList.remove("active");
    } else {
      btnBlind.classList.add("active");
      btnGhost.classList.remove("active");
    }
  }

  function updateConnectionStatus(connected) {
    if (connected) {
      statusDot.className = "status-dot connected";
      statusText.innerText = "ONLINE (WS)";
      btnConnect.innerText = "DISCONNECT ENGINE";
      btnConnect.style.background = "#ef4444"; // red button when connected to disconnect
    } else {
      statusDot.className = "status-dot disconnected";
      statusText.innerText = "OFFLINE (WS)";
      btnConnect.innerText = "CONNECT ENGINE";
      btnConnect.style.background = "#8b5cf6"; // purple when disconnected
    }
  }

  function updateCalibrationButton(calibrating) {
    if (calibrating) {
      btnCalibrate.innerText = "LOCK GRID MASK";
      btnCalibrate.classList.add("active");
    } else {
      btnCalibrate.innerText = "CALIBRATE GRID";
      btnCalibrate.classList.remove("active");
    }
  }

  function broadcastSettingsChange(settings) {
    // Send message to active tabs running content.js
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, {
          action: "updateSettings",
          settings: settings
        }).catch(() => {
          // Ignore failures when scripts are not injected
        });
      }
    });
  }
});
