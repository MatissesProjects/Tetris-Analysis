# Master Engineering Specification: Aegis-Tetris Analyzer

This document serves as the comprehensive, production-ready technical master plan for building **Aegis-Tetris Analyzer**, an offline-first, full-stack training ecosystem. It combines a lightweight browser frontend with a high-performance Python analytics engine and a local **Gemma 4:26b** instance to diagnose mid-game spatial blunders, eliminate end-game panic, teach advanced SRS+ mechanics, and enforce elite lookahead capabilities.

---

## 1. System Architecture & Tech Stack

The platform is decoupled into a low-latency client wrapper and a high-throughput computational backend to keep the browser environment lightweight and responsive.

```
[ Tetr.io Client / Sandbox UI ] 
        ▲
        │ (Bi-directional WebSockets: Input Streams, Render Masks, Overlays)
        ▼
[ Python FastAPI Backend Engine ] 
        │
        ├──► [ K-D Tree Structural Pattern Matcher (Kaggle Dataset Index) ]
        ├──► [ SRS+ Geometry & 180-Degree Rotation Simulator ]
        └──► [ Local Ollama Interface ──► Gemma 4:26b ]

```

### Frontend Stack (Chrome Extension & Sandbox)

* **Architecture:** Manifest V3 Extension.
* **UI Layer:** Shadow DOM injections into the Tetr.io DOM for inline metrics; dedicated standalone dashboard page for sandbox playback and deep timeline reviews.
* **Graphics & Rendering:** HTML5 Canvas API mirroring the native 10x40 matrix grid state.

### Backend Stack (Heavy Lifting Core)

* **Core Engine:** Python 3.11+ using `FastAPI` and `WebSockets` for real-time frame streaming.
* **Matrix Processing:** `NumPy` for lightning-fast mathematical transformations of playfield topologies.
* **Indexing:** `SciPy (spatial.KDTree)` for sub-millisecond structural matching against historical grandmaster datasets.
* **Inference Pipeline:** Local `Ollama` API connection serving `gemma4:26b`.

---

## 2. Telemetry Pipeline & Replay Extraction

To analyze performance, the engine must ingest historical matches and reconstruct exact structural states deterministically.

```
  [ .ttr/.ttrm File ] ──► [ Extract Seed & Event Array ] ──► [ Step-by-Step State Reconstructor ]
                                                                             │
                                                                             ▼
                                                                  [ Telemetry Output ]
                                                                  - Column Height Variance
                                                                  - Hole-Capping Flags
                                                                  - Finesse Inversion Ratios

```

### Replay Data Structure

Tetr.io single-player (`.ttr`) and multiplayer (`.ttrm`) files track absolute input timelines rather than snapshot grids. The Python backend extracts the initialization seed and sequential event logs:

* **Seed Extraction:** Extracts the random number generator parameters to reconstruct the exact sequential 7-bag piece distribution.


* **Tick-Rate Parsing:** Evaluates keypress events mapped to subframe ticks ($60 \text{ frames/sec} \times 10 \text{ subframes} = 600 \text{ ticks/sec}$).



### Anomaly Isolation & Thresholds

The Python backend processes the reconstructed gameplay log and flags frames where performance collapses:

* **Panic State Indicator:** Triggered when the average column height exceeds 12 rows, accompanied by a sudden downward spike in Pieces-Per-Second (PPS) and an upward spike in finesse errors.


* **Hole-Capping Detection:** Monitored by scanning the matrix column by column. If an empty cell has a filled cell anywhere above it, the engine tracks back to the exact tick that filled the upper cell, cataloging it as an unforced downstack obstruction.



---

## 3. World-Class Training Feature Synthesis

Aegis-Tetris Analyzer adapts the core loop mechanics of elite training tools into a single, cohesive framework:

| Feature Inspiration | Mechanical Core | Aegis Implementation |
| --- | --- | --- |
| **Tetresse**<br> | Instantly resets the state upon a finesse fault, enforcing perfect physical execution.

 | **Finesse Rewind:** Instantly rewinds the sandbox timeline by 3 pieces when an input violation occurs during high-stress panic phases, forcing mechanical recalculation.

 |
| **Jstris Cheese Race**<br> | Generates complex, messy rows of broken garbage blocks to train raw survival speed.

 | **Dynamic Cheese Synthesis:** Extracts real mid-game cluttered boards where you panicked, isolates the messy rows, and proceduralizes them into endless downstack survival puzzles.

 |
| **Sfinder / PC Finder**<br> | Calculates mathematically absolute perfect clear sequences using lookup tables.

 | **Gemma Lookahead Overlay:** Projects dynamic, real-time optimal queue placements directly onto the UI based on your upcoming 5 pieces.

 |

---

## 4. Advanced Spin & Geometric Setup Engine

The Python engine explicitly maps Tetr.io’s unique **SRS+** rotation system to teach advanced setups like Z/S Triples and 180° J/L spins.

### S and Z Triple Notch Diagnostics

S and Z Triples do not rely on traditional block overhangs like T-spins; they exploit natural notch geometry.

```
   [Wall] █                 █ [Wall]      Execution (S-Triple):
   [Wall] █ ░░              █ [Wall]      1. Soft-drop S-Piece vertically
   [Wall] █ ░░ ◄── Ledge    █ [Wall]         onto the 1-cell ledge.
   [Wall] █    ██           █ [Wall]      2. Execute CCW Rotation.
   [Wall] █   ██ ◄── Cavity █ [Wall]      3. SRS+ Test 4 kicks piece
   [Base] ███████████████████ [Base]         downward and inward.

```

1. **Topology Scan:** The backend tracks the board's surface vector. It searches for a 3-row vertical wall directly adjacent to a single-cell horizontal landing ledge.
2. **Advisory Trigger:** If an S or Z piece is detected within the upcoming 3 pieces of the queue, the engine calculates the placements required to complete the notch and overlays a translucent guide on the board.

### SRS+ 180-Degree Traversal Engine

Tetr.io's custom 180-degree kick tables allow shapes to slip through spaces that are completely inaccessible via standard 90-degree rotations.

* **The Tunnels Identification:** The Python engine models empty $2 \times 1$ or $1 \times 2$ pockets embedded under clean garbage configurations.
* **Kick Mapping:** When a J or L piece is active, the engine checks if a 180-degree rotation keypress at the opening of a corner dependency triggers an extreme translation offset, allowing the piece to "quantum tunnel" into an open downstack lane beneath the clutter.

### Kaggle Dataset Grounding Pipeline

To prevent the AI from recommending unrealistic, theoretical maneuvers, the backend matches your current board state against a local index of the **7.7 Million Row Kaggle Tetr.io Dataset**.

1. **Vectorization:** Every frame is converted into an array capturing column heights, hole coordinates, and queue state.
2. **Nearest Neighbor Search:** A `scipy.spatial.KDTree` scans the historical positions of the top 500 players to locate an identical or structurally highly similar environment.
3. **Anchor Extraction:** The backend pulls the exact, battle-tested decision made by the Grandmaster (e.g., *“Player ignored the flashy T-spin, preserved back-to-back status, and prioritized downstacking the column-3 hole”*) and injects it into Gemma's prompt.

---

## 5. Lookahead Training (The Hidden Matrix Mask)

This specialized operational mode forces players to break their visual dependency on the active drop zone, shifting their focus entirely to the upcoming queue elements.

```
+---------------------------+
| [HOLD]             [NEXT] |   Visual Interface State:
|  [I]                [T]   |   - Active 10x40 Grid: 100% Blacked Out
|                     [O]   |   - Queue Containers: Fully Visible
| +-----------------------+ |   
| |                       | |   Core Objective:
| |      HIDDEN MATRIX    | |   Force short-term memory to maintain
| |          MASK         | |   the stack layout while peripheral 
| |                       | |   vision parses the incoming bag.
| +-----------------------+ |
+---------------------------+

```

### Mask Configuration Modes

* **Ghost Mode:** The playfield canvas opacity is set to `0.85`, rendering a faint, barely visible silhouette of the current stack structure.
* **Blind Mode:** The playfield canvas opacity is locked at `1.0`. The board is completely dark.

### The Real-Time Spotter Loop

As you execute blind inputs on the frontend, the extension mirrors the actions over WebSockets to the Python server. The server tracks the true virtual state behind the scenes:

* **The 3-Bag Peek Heuristic:** If you place 3 consecutive pieces cleanly without introducing a structural error or capping a hole, the frontend container briefly sets opacity to `0.0` for **100 milliseconds** (6 frames), giving you a momentary visual check of the stack before returning to total darkness.
* **Intervention Unmasking:** If an input creates a fatal structural blockage, the mask drops instantly, the game freezes, and **Gemma 4:26b** delivers an explanation of exactly where your internal mental map of the board diverged from reality.

---

## 6. Gemma 4:26b Prompt Optimization Protocol

To extract actionable tactical feedback from a local 26B model without latency issues, all spatial data must be strictly structured as raw text parameters before transmission.

### Standardized JSON Context Payload

```json
{
  "session_phase": "End-Game Panic Recovery",
  "board_topology": {
    "average_stack_height": 15,
    "surface_bumpiness": 9,
    "critical_obstructions": [
      {"row": 4, "column": 3, "description": "Column 3 downstack lane capped by horizontal J-Piece"}
    ]
  },
  "piece_environment": {
    "held_piece": "I",
    "active_piece": "T",
    "upcoming_queue": ["S", "Z", "O", "L", "J"]
  },
  "empirical_baseline": {
    "match_source": "Kaggle Index - Match #7412 - Top 500 Player",
    "grandmaster_action": "Executed soft-drop vertical T-spin into column 9 to lower stack height before incoming 8-row spike resolved."
  },
  "user_telemetry": {
    "current_pps": 1.9,
    "finesse_faults_last_10_pieces": 6,
    "fatal_action": "Panicked under incoming spike. Hard-dropped T-piece horizontally on column 3, completely closing the downstack path."
  }
}

```

### System Instruction Prompt

```
You are an elite, grandmaster-tier Tetr.io tactical analyst and sports psychologist. 
Analyze the provided JSON context payload detailing a user's gameplay breakdown.

Your response must strictly adhere to these criteria:
1. Do not output raw coordinate lists or reiterate data blocks verbatim.
2. Directly diagnose the psychological or structural issue (e.g., misidentifying the downstack column due to end-game fear).
3. Contrast the user's action with the empirical grandmaster baseline provided in the payload.
4. Deliver short, precise, actionable tactical commands that the user can immediately practice in the upcoming interactive sandbox session.

```

---

## 7. Immediate Development Checklist

To begin building the system methodically, execute these components in order:

* **Phase 1 (Backend Core):** Set up the FastAPI framework, implement the replay `.ttr` seed parsing engine, and verify deterministic matrix state reproduction.


* **Phase 2 (Extension UI):** Build the Manifest V3 canvas container overlay script to inject the `aegis_lookahead_mask` and interface elements natively onto the Tetr.io window.
* **Phase 3 (Pattern Integration):** Load the Kaggle dataset into a local SciPy KDTree index to enable rapid structural querying based on surface topology profiles.
* **Phase 4 (Inference Connection):** Connect the local Ollama instance running Gemma 4:26b to the background telemetry stream to activate real-time interactive sandbox analysis.