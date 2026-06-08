# Implementation Plan: Reload Session History

We need to allow users to click on any session history item in the sidebar/history list and reload that run's statistics, charts, and recommendations back into the dashboard.

## 1. Database Schema Enhancements
To fully reconstruct a replay analysis from the database, we need to store additional telemetry metrics that were previously discarded or only calculated during replay parsing:
* `average_planning_latency_ms` (REAL)
* `average_execution_latency_ms` (REAL)
* `double_rotations` (INTEGER)
* `rotate180_count` (INTEGER)
* `kpp` (REAL, representing keystrokes per piece)

### Migration Plan
Update `backend/app/db/database.py`:
1. Modify `scores` table initialization to include these columns.
2. In the migration/schema-check function `init_db()`, check if these columns exist, and if not, run `ALTER TABLE scores ADD COLUMN <col> ...`.
3. Update `add_score()` to accept and save these parameters.
4. Update `get_scores()` to return them.

## 2. API Endpoints
Update `backend/app/api/endpoints.py`:
1. Modify the `suggest_from_replay_file` endpoint to extract and pass the additional columns to `add_score()`.
2. Return the new `score_id` (retrieved from `add_score`) in the response of `suggest_from_replay_file`.
3. Implement/update `GET /api/v1/scores/{score_id}`:
   * Fetch the score row by ID from the database.
   * If not found, return 404.
   * Check if `replay_name` is present. If so, check if the file exists under the user's `~/Downloads/` directory.
   * **If file exists in Downloads:**
     * Read and parse the file dynamically using `TTRParser.parse_replay()`.
     * Extract stats and suggestions.
     * Return the full parsed replay payload.
   * **If file does not exist in Downloads (Fallback):**
     * Parse the stats from the database row, reconstruct the payload structure (metadata, extracted_stats), and generate suggestions dynamically via `TrainingSuggester.suggest_trainings(stats)`.
     * Return the formatted response (matching the structure returned by `/trainings/suggest-from-replay`).

## 3. Frontend Integration
Update `backend/app/static/index.html`:
1. Add a cursor pointer and an active/selected state styling for `.history-item`.
2. Update `renderHistoryList()` to add:
   * A click handler to each item: `onclick="loadHistoryItem(${record.id})"` (ensuring `event.stopPropagation()` is called on the delete button to prevent triggering it).
   * A check to see if the item is currently active/selected, adding a `.active` class.
3. Implement `loadHistoryItem(id)`:
   * Add a visual selected state to the clicked history item.
   * Fetch `/api/v1/scores/{id}` from the backend.
   * Pass the returned data directly to `populateDashboard(data)`.
   * Keep track of the currently selected history ID in a global variable (`currentSelectedScoreId`).
4. Update `populateDashboard(data)` to accept a custom selected ID or handle the selection highlight when a new replay file is uploaded and auto-saved.
