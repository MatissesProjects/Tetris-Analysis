# Implementation Plan: Finesse Rate Calculation Correction

We will correct the finesse rate calculation in the Aegis-Tetris Analyzer. Currently, the finesse rate is calculated using a key-based formula `(KPT - finesse_faults) / KPT`, which differs from standard TETR.IO behavior. Under standard TETR.IO rules, finesse rate is defined as the percentage of pieces placed with perfect finesse (0 faults) out of the total pieces placed: `perfect_pieces / total_pieces`.

## 1. Diagnostics & File Examination

We verified the content of `40line.ttr` in the downloads folder:
- **Total Pieces Placed (`piecesplaced`):** 106
- **Perfect Pieces (`perfectpieces`):** 84
- **Finesse Faults (`faults`):** 28
- **TETR.IO Finesse Rate:** `84 / 106 = 79.25%`
- **Current calculation:** `(KPT - faults) / KPT` evaluates to `~91.9%` because KPT is total keystrokes (average KPP * pieces).

## 2. Planned Changes

### A. TTRParser Metadata Extraction (`backend/app/parser/ttr_parser.py`)
- Update `TTRParser.extract_metadata` to extract `perfectpieces` from the official replay JSON structure.
- Save it as `finesse_perfect_pieces` in the returned stats dictionary.

### B. Endpoints Calculation (`backend/app/api/endpoints.py`)
- Update `/api/v1/trainings/suggest-from-replay` to:
  - Retrieve `finesse_perfect_pieces` from `merged_stats`.
  - Calculate `finesse_rate` as `finesse_perfect_pieces / pieces` (if present).
  - Fall back to a piece-based heuristic `max(0, pieces - faults) / pieces` (instead of key-based `(kpt - faults) / kpt`) if `finesse_perfect_pieces` is not available. This is consistent with the event-based parsing in `TrainingSuggester.parse_events_for_stats` where faults are incremented per-piece.

### C. Training Suggester (`backend/app/core/training.py`)
- Update `TrainingSuggester.suggest_trainings` to:
  - Check for `finesse_perfect_pieces` and use it if present.
  - Fall back to `max(0.0, (pieces_placed - finesse_faults) / pieces_placed)` as the estimate when perfect piece count is not available.

### D. Frontend Display Fallback (`backend/app/static/index.html`)
- Update the frontend fallback calculation in `index.html` (line 849) to use a piece-based calculation instead of the key-based `kptVal` logic when `ext.finesse_rate` is missing.

## 3. Verification & Testing
- Write/run unit tests to verify the correctness of the calculations.
- Parse the user's `40line.ttr` via `/api/v1/trainings/suggest-from-replay` and assert that the returned `finesse_rate` is `0.7925` (79.25%).
- Verify that standard training recommendations adjust accordingly.
