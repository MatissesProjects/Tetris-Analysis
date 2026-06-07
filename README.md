# Aegis-Tetris Analyzer

Aegis-Tetris Analyzer is an offline-first, full-stack training ecosystem and real-time spatial diagnostics platform for Tetr.io. The system consists of a high-performance Python FastAPI backend that processes replay data, vectorizes board states, tracks scoring history in SQLite, and serves a cyber-glow drag-and-drop dashboard, coupled with a Manifest V3 Chrome Extension that injects a resizable lookahead mask and real-time coach alerts directly onto the Tetr.io canvas.

---

## System Architecture

The project is structured into three main components:
1. **Python FastAPI Backend:** Runs a deterministic replay parser, reconstructs the game state from the RNG seed, builds a SciPy KDTree matching index on top of historical Grandmaster plays, queries local Ollama instances, and stores historical score runs in a local SQLite database.
2. **HUD Replay Analyzer Frontend:** Served directly at the root `http://localhost:8000/`. Provides a gorgeous glassmorphic dashboard to upload `.ttr` replay files and view immediate, prioritized training suggestions, planning/execution latency diagnostics, KPT-based finesse metrics, and a copyable raw JSON viewer.
3. **Chrome Extension (Manifest V3):** Injects a click-through resizable Shadow DOM overlay on top of the Tetr.io grid. Relays keyboard inputs over WebSockets to synchronize telemetry and receives spotting recommendations or peek-heuristic flashes.

---

## Directory Map

```
Tetris-Analysis/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── endpoints.py        # HTTP routes for replay parsing, training suggestions, and score history
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Project settings, database paths, and CORS configurations
│   │   │   ├── rng.py              # MINSTD Lehmer PRNG and 7-bag queue generator
│   │   │   ├── vectorizer.py       # 20-dimensional playfield topology vectorizer
│   │   │   ├── ollama_client.py    # Local Ollama client with resilient rule-based failovers
│   │   │   ├── training.py         # Dynamic training suggester and rule engine
│   │   │   ├── attack.py           # Tetris attack power and combo calculations
│   │   │   ├── pacing.py           # Speed-pacing diagnostic evaluators
│   │   │   └── openings.py         # Classic openers matcher
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── database.py         # SQLite database schema and helper functions
│   │   ├── index/
│   │   │   ├── __init__.py
│   │   │   ├── kdtree_index.py     # Sub-millisecond SciPy KDTree grounding index
│   │   │   └── kaggle_tetrio_top_500.csv # Local cached pro dataset
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   └── ttr_parser.py       # Resilient .ttr / .ttrm replay data traverser
│   │   ├── static/
│   │   │   └── index.html          # Cyber-glow replay analyzer HUD web application
│   │   ├── __init__.py
│   │   └── main.py                 # FastAPI application, startup DB initializer, and index route
│   ├── requirements.txt            # Python dependencies (websockets, sqlite3, etc.)
│   └── run.py                      # Development server launch helper
├── extension/
│   ├── assets/
│   │   └── logo.png                # Cyber-glow esports brand emblem icon
│   ├── manifest.json               # Manifest V3 browser extension mapping
│   ├── popup.html                  # Sleek glassmorphic settings dashboard
│   ├── popup.css                   # Custom neon HUD theme stylesheet
│   ├── popup.js                    # Storage persistence controller
│   ├── content.js                  # Shadow DOM resizable playfield overlay and keycapturer
│   └── background.js               # Service worker tunnel bridging inputs to backend WebSockets
├── tests/
│   ├── __init__.py
│   ├── test_rng.py                 # RNG Lehmer MINSTD and 7-bag invariant tests
│   ├── test_parser.py              # Replay JSON parser test suite
│   ├── test_vectorizer.py          # Column heights and downstack hole extraction tests
│   └── test_ollama.py              # Prompter and fallback tests
└── README.md                       # Systems manual
```

---

## Backend Installation and Running

### Prerequisites
* Python 3.10 or higher
* Local Ollama instance running the gemma:26b model

### Setup Virtual Environment
Create and activate an isolated virtual environment at the project root:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
Install all package requirements:
```bash
pip install -r backend/requirements.txt
```

### Run the Development Server
Launch the FastAPI uvicorn server:
```bash
PYTHONPATH=backend python backend/run.py
```
The server will start up on `http://localhost:8000`. On startup, it automatically creates the local SQLite database and builds the cached Grandmaster matching KDTree index.

---

## Browser Extension Installation

1. Open Google Chrome or any Chromium-based browser.
2. Navigate to `chrome://extensions/`.
3. Enable **Developer mode** in the top-right corner.
4. Click **Load unpacked** in the top-left corner.
5. Select the `extension/` directory from this project workspace.
6. Open `https://tetr.io/` in your browser.
7. Click the Aegis extension icon, click **Calibrate Grid** to drag/resize the lookahead overlay frame perfectly over the gameplay board, click **Lock Grid Mask**, and connect the engine.

---

## API Endpoints

### 1. Replay HUD Dashboard
* **URL:** `/`
* **Method:** `GET`
* **Response:** Interactive HTML/CSS HUD dashboard for uploading and parsing `.ttr` files, showing execution diagnostics and training recommendations.

### 2. Suggest Trainings from Replay File
* **URL:** `/api/v1/trainings/suggest-from-replay`
* **Method:** `POST`
* **Request:** Multipart Form-Data with a `.ttr`, `.ttrm`, or `.json` file.
* **Response:**
  * Auto-saves the run stats (score, APM, PPS, finesse, lines, pieces) into the SQLite database.
  * Calculates key-based finesse rate: $\text{Finesse Rate} = \frac{\text{KPT} - \text{finesse\_faults}}{\text{KPT}}$ where $\text{KPT} = \text{KPP} \times \text{pieces\_placed}$.
  * Returns metadata, event-parsed statistics, and prioritized training suggestions.

### 3. Score History (GET)
* **URL:** `/api/v1/scores`
* **Method:** `GET`
* **Response:** List of all stored score records ordered chronologically.

### 4. Add Score Record (POST)
* **URL:** `/api/v1/scores`
* **Method:** `POST`
* **Request JSON Body:** Manual score payload (`username`, `score`, `pps`, `apm`, `finesse_faults`, `finesse_rate`, `pieces_placed`, `lines_cleared`).
* **Response:** Success status and the newly created entry ID.

### 5. Delete Score Entry (DELETE)
* **URL:** `/api/v1/scores/{score_id}`
* **Method:** `DELETE`
* **Response:** Success status and confirm message.

### 6. Clear Score History (DELETE)
* **URL:** `/api/v1/scores/clear`
* **Method:** `DELETE`
* **Response:** Success status clearing the database table.

### 7. Live Telemetry WebSockets
* **URL:** `/api/v1/ws/telemetry`
* **Protocol:** `WS`
* **Functionality:** Relays live keystroke streams. Triggers lookahead unmask flashes every 3 pieces and alerts users on double-tap rotation faults.

---

## Execution of Automated Tests

To run the complete mathematical and API integration test suite, execute pytest:
```bash
PYTHONPATH=backend venv/bin/pytest tests/
```
Tests check MINSTD Lehmer behavior, the 7-bag invariant, resilient JSON parsing paths, spatial vector heights/holes, prompt layout compilation, and mocked/offline Ollama timeouts.
