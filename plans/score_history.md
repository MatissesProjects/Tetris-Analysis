# Implementation Plan: Score History & Progression Visualization

We will add a persistent score history feature to the Aegis-Tetris Analyzer, allowing users to track their performance metrics (Score, PPS, APM, Finesse Rate) across multiple sessions. This document outlines the planned design and implementation steps.

## 1. Data Storage & Schema Design

Since this is an offline-first desktop application, we will use a local **SQLite** database (`backend/app/db/history.db`). This ensures zero dependency overhead and robust local persistence.

### Schema: `scores` table
| Column Name | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Unique record ID |
| `username` | TEXT | Player username |
| `score` | INTEGER | Final score of the run |
| `pps` | REAL | Pieces per second |
| `apm` | REAL | Attacks per minute |
| `finesse_faults` | INTEGER | Finesse faults |
| `finesse_rate` | REAL | Finesse rate (0.0 to 1.0) |
| `pieces_placed` | INTEGER | Total pieces placed |
| `lines_cleared` | INTEGER | Total lines cleared |
| `timestamp` | DATETIME | Game timestamp (defaulting to current time) |
| `replay_name` | TEXT | Name of the parsed replay file (optional) |

---

## 2. Backend Architecture

### Database Utility (`backend/app/db/database.py`)
- Standard library `sqlite3` connection helper.
- Function to initialize the database/table if not present.
- Insertion function to add score records.
- Retrieval function returning lists of records sorted by time.
- Deletion functions (single entry & clear all).

### API Route Design (`backend/app/api/endpoints.py`)
Add the following endpoints under `/api/v1`:
- `GET /scores`: Retrieve all stored score history.
- `POST /scores`: Directly submit a score entry (for manual testing/extension compatibility).
- `DELETE /scores/{id}`: Delete a single history entry.
- `DELETE /scores/clear`: Clear the entire history.

### Auto-Logging Integration
In the `POST /trainings/suggest-from-replay` endpoint:
- Automatically extract the score, PPS, APM, lines, pieces, and finesse metrics, and insert a new record into the database.

---

## 3. Frontend Dashboard UI Enhancement

We will add a new **Progression History** section in `backend/app/static/index.html`.

### UI Mockup & Layout
- A dedicated **Progression & Analytics** panel featuring:
  - **Interactive Line Chart**: Chart.js loaded via CDN. Sleek custom styling: cyan/magenta gradients, neon gridlines, and tooltips.
  - **Interactive Metric Toggle**: Buttons to switch the chart view between Score, PPS, and Finesse Rate.
  - **History Table**: A list showing all previous runs with precise timestamps, key stats, and action buttons (e.g., delete).
  - **Bulk Actions**: A "Clear History" button with a confirmation modal/prompt.

### Telemetry / Replay Flow
1. User drags & drops a replay file.
2. The frontend sends it to `/api/v1/trainings/suggest-from-replay`.
3. The backend parses it, writes to SQLite, and returns the analysis.
4. The frontend refreshes the chart and history table by calling `GET /api/v1/scores`.

---

## 4. Execution Roadmap

1. **Step 1:** Create `backend/app/db/database.py` and write the initialization and CRUD functions.
2. **Step 2:** Integrate database initialization into the FastAPI app startup.
3. **Step 3:** Add endpoints to `backend/app/api/endpoints.py` and verify using manual python requests or testing tool.
4. **Step 4:** Integrate auto-saving into `/trainings/suggest-from-replay`.
5. **Step 5:** Modify `backend/app/static/index.html` to import Chart.js, render the progression chart, list history, and hook up endpoints.
6. **Step 6:** Validate the full integration.
7. **Step 7:** Commit logical chunks to Git.
