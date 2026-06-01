let socket = null;
let wsConnected = false;

// Initialize on extension startup
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    maskEnabled: false,
    maskMode: "ghost",
    heuristicEnabled: true,
    wsConnected: false,
    isCalibrating: false
  });
});

// Listener for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "toggleEngineConnection") {
    if (wsConnected) {
      disconnectFromBackend();
    } else {
      connectToBackend();
    }
    sendResponse({ success: true });
  } else if (message.action === "relayGameEvent") {
    // Forward keystroke events to the WebSocket server
    if (wsConnected && socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message.event));
    }
    sendResponse({ delivered: wsConnected });
  }
  return true;
});

function connectToBackend() {
  if (socket) {
    disconnectFromBackend();
  }

  const wsUrl = "ws://localhost:8000/api/v1/ws/telemetry";
  console.log(`Connecting to backend WebSocket: ${wsUrl}`);
  
  try {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("WebSocket connection established successfully!");
      wsConnected = true;
      chrome.storage.local.set({ wsConnected: true });
      broadcastConnectionStatus(true);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Received data from engine:", data);
        
        // Handle trigger events from Python server
        if (data.action === "flash_unmask") {
          // Trigger a 3-bag peek flash
          chrome.tabs.query({ active: true }, (tabs) => {
            for (let tab of tabs) {
              chrome.tabs.sendMessage(tab.id, { action: "triggerFlash" }).catch(() => {});
            }
          });
        } else if (data.action === "intervention") {
          // Show Gemma explanation and unmask the board
          chrome.tabs.query({ active: true }, (tabs) => {
            for (let tab of tabs) {
              chrome.tabs.sendMessage(tab.id, { 
                action: "triggerIntervention", 
                message: data.message 
              }).catch(() => {});
            }
          });
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    socket.onerror = (error) => {
      console.error("WebSocket error observed:", error);
      disconnectFromBackend();
    };

    socket.onclose = () => {
      console.log("WebSocket connection closed.");
      disconnectFromBackend();
    };

  } catch (error) {
    console.error("Error creating WebSocket connection:", error);
    disconnectFromBackend();
  }
}

function disconnectFromBackend() {
  if (socket) {
    try {
      socket.close();
    } catch (e) {}
    socket = null;
  }
  wsConnected = false;
  chrome.storage.local.set({ wsConnected: false });
  broadcastConnectionStatus(false);
}

function broadcastConnectionStatus(connected) {
  // Update popup if it's open
  chrome.runtime.sendMessage({
    action: "updateConnectionStatus",
    connected: connected
  }).catch(() => {
    // Ignore when popup is closed
  });
}
