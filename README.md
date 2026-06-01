# Aegis-Tetris Analyzer

Aegis-Tetris Analyzer is an offline-first, full-stack training ecosystem and real-time spatial diagnostics platform for Tetr.io. The system consists of a high-performance Python FastAPI backend that processes replay data and vectorizes board states, coupled with a Manifest V3 Chrome Extension that injects a resizable lookahead mask and real-time coach alerts directly onto the Tetr.io canvas.

---

## System Architecture

The project is structured into two main components:
1. **Python FastAPI Backend:** Runs a deterministic replay parser, reconstructs the game state from the RNG seed, builds a SciPy KDTree matching index on top of historical Grandmaster plays, and queries local Ollama instances running Gemma 4:26b.
2. **Chrome Extension (Manifest V3):** Injects a click-through resizable Shadow DOM overlay on top of the Tetr.io grid. Relays keyboard inputs over WebSockets to synchronize telemetry and receives spotting recommendations or peek-heuristics flashes.

---

## Directory Map

```
Tetris-Analysis/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── endpoints.py        # HTTP routes for parsing and integrated LLM advice
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Project settings and CORS configurations
│   │   │   ├── rng.py              # MINSTD Lehmer PRNG and 7-bag queue generator
│   │   │   ├── vectorizer.py       # 20-dimensional playfield topology vectorizer
│   │   │   └── ollama_client.py    # Local Ollama client with resilient rule-based failovers
│   │   ├── index/
│   │   │   ├── __init__.py
│   │   │   ├── kdtree_index.py     # Sub-millisecond SciPy KDTree grounding index
│   │   │   └── kaggle_tetrio_top_500.csv # Local cached pro dataset (5,000 matches)
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   └── ttr_parser.py       # Resilient .ttr / .ttrm replay data traverser
│   │   ├── __init__.py
│   │   └── main.py                 # FastAPI application and route registrar
│   ├── requirements.txt            # Declarative list of Python dependencies
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
│   └── test_ollama.py              # Prompter and fallback fallback tests
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
The server will start up on `http://localhost:8000`. It automatically builds a cached local database of 5,000 Grandmaster match rows on its first boot to index the KDTree.

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

### 1. Replay Ingestion (File)
* **URL:** `/api/v1/parse-file`
* **Method:** `POST`
* **Request:** Multipart Form-Data with a `.ttr`, `.ttrm`, or `.json` file.
* **Response:** Parsed seed, player metadata, event log, and projected piece queue.

### 2. Replay Ingestion (JSON)
* **URL:** `/api/v1/parse-json`
* **Method:** `POST`
* **Request JSON Body:** Raw replay payload.
* **Response:** Parsed seed, player metadata, event log, and projected piece queue.

### 3. Nearest Neighbor Match
* **URL:** `/api/v1/query-recommendation`
* **Method:** `POST`
* **Request JSON Body:**
  ```json
  {
    "grid": [[0, 0, ...], ...]
  }
  ```
  *(A 10-column by 40-row integer list representation of playfield blocks where 0 is empty and 1 is filled)*
* **Response:** Closest matching Grandmaster play, rating, distance, category, and tactical action.

### 4. Integrated Tactical LLM Advice
* **URL:** `/api/v1/query-advice`
* **Method:** `POST`
* **Request JSON Body:**
  ```json
  {
    "grid": [[0, 0, ...], ...],
    "active_piece": "T",
    "queue": ["I", "O", "S", "Z", "L"]
  }
  ```
* **Response:** Full spatial query profile, nearest-neighbor matched Grandmaster anchor play, and the real-time Gemma LLM tactical spotter advice (or resilient local failover recommendation).

---

## Execution of Automated Tests

To run the complete mathematical and API integration test suite containing 16 unit tests, execute pytest:
```bash
PYTHONPATH=backend venv/bin/pytest tests/
```
Tests check MINSTD Lehmer behavior, the 7-bag invariant (each consecutive group of 7 pieces contains exactly one of each tetromino), resilient JSON parsing paths, spatial vector heights/holes, prompt layout compilation, and mocked/offline Ollama timeouts.
