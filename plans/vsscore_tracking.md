# Implementation Plan: VS Score Tracking & Visualization

We will extract the `vsscore` (VS Score) from TETR.IO replay files, persist it in our database history, and visualize it alongside existing metrics (Score, PPS, APM, Finesse Rate) in the frontend dashboard.

## 1. Database Schema Update
- Update `backend/app/db/database.py` to include `vsscore` (type `REAL`) in the `scores` table.
- Modify `init_db()` to automatically run a migration check (using `PRAGMA table_info(scores)`) to add the `vsscore` column to existing databases without data loss.
- Update `add_score()` to accept `vsscore` and save it.
- Ensure `get_scores()` includes the `vsscore` in the returned records.

## 2. Parser Update
- Update `backend/app/parser/ttr_parser.py` to extract `vsscore` from JSON replay files.
- Look for `vsscore` key in:
  - Root `stats` level
  - `replay.results.stats`
  - `replay.results.aggregatestats`

## 3. API & Endpoints Integration
- Update Pydantic model `ScoreCreatePayload` in `backend/app/api/endpoints.py` to include `vsscore`.
- In `/trainings/suggest-from-replay`, extract `vsscore` from parsed replay metadata.
- If `vsscore` is not found/null in the replay data, calculate a fallback estimate: `vsscore = apm + pps * 20`.
- Update the `add_score()` invocation inside `/trainings/suggest-from-replay` to pass `vsscore`.

## 4. Frontend Dashboard UI Enhancement
- In `backend/app/static/index.html`:
  - Add "VS Score" button/toggle to the metric selector for the progression chart.
  - Render VS Score on the Chart.js line chart when toggled.
  - Update the score history table columns to display "VS Score".
  - Include VS Score in the recent run analysis overview.

## 5. Execution Roadmap & Git Commits
- **Phase 1: DB & Parser Modifications**
  - Implement schema changes and migrations in `database.py`.
  - Update replay parser to extract `vsscore`.
  - Commit to git: "Add vsscore to database schema and ttr parser"
- **Phase 2: API Endpoints**
  - Modify endpoints in `endpoints.py` to save and retrieve `vsscore`.
  - Commit to git: "Expose vsscore in api endpoints and auto-saving"
- **Phase 3: Frontend Dashboard UI**
  - Update chart.js and table views in `index.html`.
  - Commit to git: "Display vsscore in frontend dashboard chart and table"
- **Phase 4: Verification & Tests**
  - Write test cases for the parser and endpoint integration.
  - Commit to git: "Add test cases for vsscore tracking and parsing"
