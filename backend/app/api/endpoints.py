import json
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.parser.ttr_parser import TTRParser
from app.core.vectorizer import BoardVectorizer
from app.index.kdtree_index import grounding_index
from app.core.ollama_client import ollama_client
from app.core.finesse import FinesseEvaluator
from app.core.speed import PacingEvaluator
from app.core.lookahead import LookaheadPlanner
from app.core.eltetris import ElTetrisEvaluator
from app.core.attack import AttackCalculator
from app.core.openings import OpeningMatcher
from app.core.training import TrainingSuggester

router = APIRouter()

class GridPayload(BaseModel):
    grid: List[List[int]] = Field(..., description="10x40 integer matrix representing playfield blocks (0=empty, 1=filled)")

class AdvicePayload(BaseModel):
    grid: List[List[int]] = Field(..., description="10x40 integer matrix representing playfield blocks (0=empty, 1=filled)")
    active_piece: str = Field("I", description="Standard active held piece tetromino symbol")
    queue: List[str] = Field(..., description="List of upcoming pieces, e.g. ['Z', 'L', 'S']")

class FinessePayload(BaseModel):
    piece: str = Field(..., description="Tetromino symbol, e.g. T, I, O, L, J, S, Z")
    target_column: int = Field(..., description="Target landing column (0 to 9)")
    target_rotation: int = Field(..., description="Target landing rotation (0 to 3)")
    user_keys: List[str] = Field(..., description="Keystrokes recorded for this piece placement")

class PacingPayload(BaseModel):
    spawn_time_ms: float = Field(..., description="Timestamp in ms when piece spawned")
    first_key_time_ms: float = Field(..., description="Timestamp in ms when first key was pressed")
    drop_time_ms: float = Field(..., description="Timestamp in ms when piece dropped")
    key_count: int = Field(..., description="Total keys recorded for placement")
    finesse_faults: int = Field(0, description="Finesse faults recorded (0 or 1)")

class LookaheadPayload(BaseModel):
    grid_heights: List[int] = Field(..., description="List of 10 active column heights")
    queue: List[str] = Field(..., description="List of upcoming pieces in the lookahead queue")

class AttackPayload(BaseModel):
    clear_type: str = Field(..., description="Line clear type, e.g. single, quad, tspin_double")
    b2b_chain_length: int = Field(0, description="Active Back-to-Back chain length")
    combo_count: int = Field(0, description="Current combo counter")

class OpeningPayload(BaseModel):
    pieces_placed: List[str] = Field(..., description="Tetromino shapes in order of placement")
    columns_placed: List[int] = Field(..., description="Landing columns in order of placement")

class GameStatsPayload(BaseModel):
    pps: Optional[float] = Field(None, description="Pieces per second")
    pieces_placed: Optional[int] = Field(None, description="Total pieces placed in the game")
    finesse_faults: Optional[int] = Field(None, description="Total finesse faults committed")
    max_height: Optional[int] = Field(None, description="Maximum height reached on the board")
    capped_holes_count: Optional[int] = Field(None, description="Count of capped downstack holes")
    average_planning_latency_ms: Optional[float] = Field(None, description="Average time before first keystroke per piece")
    average_execution_latency_ms: Optional[float] = Field(None, description="Average keypress execution time per piece")
    opening_matched: Optional[bool] = Field(None, description="Whether a classic opening was recognized")
    apm: Optional[float] = Field(None, description="Attack per minute")
    b2b_spikes: Optional[int] = Field(None, description="Count of back-to-back spikes or lines cleared")
    keystrokes_per_piece: Optional[float] = Field(None, description="Average keystrokes per piece (KPP)")
    kpp: Optional[float] = Field(None, description="Average keys per piece (KPP) alias")
    double_rotations: Optional[int] = Field(None, description="Count of double 90-degree rotations in a game")
    rotate180_count: Optional[int] = Field(None, description="Count of direct 180-degree rotations used")
    topcombo: Optional[int] = Field(None, description="Maximum combo reached")
    topbtb: Optional[int] = Field(None, description="Maximum Back-to-Back chain length reached")
    tspins: Optional[int] = Field(None, description="Total T-Spins completed")
    quads: Optional[int] = Field(None, description="Total Quads completed")
    clears_json: Optional[str] = Field(None, description="Serialized clears dictionary")

class SuggestPayload(BaseModel):
    username: Optional[str] = Field("Player", description="Username of the player")
    stats: GameStatsPayload = Field(..., description="Gameplay metrics")

class ScoreCreatePayload(BaseModel):
    username: str = Field(..., description="Player username")
    score: int = Field(..., description="Final score of the run")
    pps: float = Field(..., description="Pieces per second")
    apm: float = Field(..., description="Attacks per minute")
    finesse_faults: int = Field(..., description="Finesse faults")
    finesse_rate: float = Field(..., description="Finesse rate (0.0 to 1.0)")
    pieces_placed: int = Field(..., description="Total pieces placed")
    lines_cleared: int = Field(..., description="Total lines cleared")
    replay_name: Optional[str] = Field(None, description="Optional name of the replay file")
    vsscore: float = Field(0.0, description="VS Score of the run")
    topcombo: int = Field(0, description="Maximum combo reached")
    topbtb: int = Field(0, description="Maximum Back-to-Back chain length reached")
    tspins: int = Field(0, description="Total T-Spins completed")
    quads: int = Field(0, description="Total Quads completed")
    clears_json: Optional[str] = Field(None, description="Serialized clears breakdown dictionary")

@router.post("/parse-file")
async def parse_replay_file(file: UploadFile = File(...)):
    """
    Parse an uploaded TETR.IO replay file (.ttr or .ttrm).
    Returns the seed, metadata, raw event history, and projected queue.
    """
    if not (file.filename.endswith(".ttr") or file.filename.endswith(".ttrm") or file.filename.endswith(".json")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload a .ttr, .ttrm, or .json file."
        )
        
    try:
        content = await file.read()
        replay_data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON format. The uploaded file is corrupted or not a valid JSON structure."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while reading the file: {str(e)}"
        )
        
    parsed_result = TTRParser.parse_replay(replay_data)
    
    if parsed_result["seed"] is None:
        raise HTTPException(
            status_code=422,
            detail="Failed to locate game seed in replay file. Make sure the file is a valid TETR.IO replay."
        )
        
    return parsed_result


@router.post("/parse-json")
def parse_replay_json(payload: Dict[str, Any]):
    """
    Parse a raw TETR.IO replay JSON object sent directly in the request body.
    Returns the seed, metadata, raw event history, and projected queue.
    """
    parsed_result = TTRParser.parse_replay(payload)
    
    if parsed_result["seed"] is None:
        raise HTTPException(
            status_code=422,
            detail="Failed to locate game seed in replay JSON payload."
        )
        
    return parsed_result


@router.post("/query-recommendation")
def query_recommendation(payload: GridPayload):
    """
    Retrieve sub-millisecond grandmaster structural matches and spatial advice based on the active board grid.
    """
    grid = payload.grid
    if len(grid) != 40 or any(len(row) != 10 for row in grid):
        raise HTTPException(
            status_code=400,
            detail="Invalid grid dimension. Grid must be exactly 10 columns by 40 rows."
        )
    try:
        return grounding_index.query_nearest_grandmaster(grid)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during KDTree match search: {str(e)}"
        )


@router.post("/query-advice")
def query_advice(payload: AdvicePayload):
    """
    Retrieve real-time tactical Gemma advice and nearest-neighbor Grandmaster anchors based on active gameplay frames.
    """
    grid = payload.grid
    if len(grid) != 40 or any(len(row) != 10 for row in grid):
        raise HTTPException(
            status_code=400,
            detail="Invalid grid dimension. Grid must be exactly 10 columns by 40 rows."
        )
        
    try:
        # 1. Vectorize playfield
        profile = BoardVectorizer.vectorize_board(grid)
        
        # 2. Query nearest Grandmaster anchor from KDTree
        matched = grounding_index.query_nearest_grandmaster(grid)
        anchor = matched["nearest_match"]
        
        # 3. Query Gemma spatial advice from OllamaClient
        advice_result = ollama_client.query_spatial_advice(
            heights=profile["column_heights"],
            bumpiness=profile["bumpiness"],
            holes_count=profile["holes_count"],
            holes=profile["holes"],
            active_piece=payload.active_piece,
            queue=payload.queue,
            grandmaster_anchor=anchor
        )
        
        return {
            "query_profile": matched["query_profile"],
            "nearest_match": anchor,
            "tactical_spotter": advice_result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during integrated advice processing: {str(e)}"
        )


@router.post("/check-finesse")
def check_finesse(payload: FinessePayload):
    """
    Evaluate recorded keystrokes for a piece placement against mathematical SRS optimal routes.
    """
    try:
        return FinesseEvaluator.evaluate_placement(
            piece=payload.piece,
            target_col=payload.target_column,
            target_rot=payload.target_rotation,
            user_keys=payload.user_keys
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during finesse analysis: {str(e)}"
        )


@router.post("/check-pacing")
def check_pacing(payload: PacingPayload):
    """
    Evaluate planning and mechanical timing profiles to optimize play speed.
    """
    try:
        return PacingEvaluator.evaluate_pacing(
            spawn_time_ms=payload.spawn_time_ms,
            first_key_time_ms=payload.first_key_time_ms,
            drop_time_ms=payload.drop_time_ms,
            key_count=payload.key_count,
            finesse_faults=payload.finesse_faults
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during speed pacing evaluation: {str(e)}"
        )


@router.post("/query-lookahead")
def query_lookahead(payload: LookaheadPayload):
    """
    Generate an optimal 5-piece lookahead blueprint to maintain a flat surface topology.
    """
    heights = payload.grid_heights
    if len(heights) != 10:
        raise HTTPException(
            status_code=400,
            detail="Invalid grid heights dimension. Array must contain exactly 10 column heights."
        )
    try:
        return LookaheadPlanner.calculate_queue_blueprint(
            grid_heights=heights,
            queue=payload.queue
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during lookahead planning: {str(e)}"
        )


@router.post("/check-fitness")
def check_fitness(payload: GridPayload):
    """
    Evaluate playfield structural quality and transition counts using pro bot ElTetris weights.
    """
    grid = payload.grid
    if len(grid) != 40 or any(len(row) != 10 for row in grid):
        raise HTTPException(
            status_code=400,
            detail="Invalid grid dimension. Grid must be exactly 10 columns by 40 rows."
        )
    try:
        profile = BoardVectorizer.vectorize_board(grid)
        return ElTetrisEvaluator.evaluate_board(
            grid=grid,
            heights=profile["column_heights"],
            bumpiness=profile["bumpiness"],
            holes_count=profile["holes_count"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during ElTetris board evaluation: {str(e)}"
        )


@router.post("/check-attack")
def check_attack(payload: AttackPayload):
    """
    Evaluate attack power, B2B chain multipliers, and combo modifiers under canonical TETR.IO rules.
    """
    try:
        return AttackCalculator.evaluate_clear(
            clear_type=payload.clear_type,
            b2b_chain_length=payload.b2b_chain_length,
            combo_count=payload.combo_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during attack damage analysis: {str(e)}"
        )


@router.post("/check-opening")
def check_opening(payload: OpeningPayload):
    """
    Match placement sequences of the first bag against classic openings like TKI 3, DT Cannon, or MKO.
    """
    try:
        return OpeningMatcher.match_opening(
            pieces_placed=payload.pieces_placed,
            columns_placed=payload.columns_placed
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during opening match evaluation: {str(e)}"
        )


@router.get("/trainings")
def get_available_trainings():
    """
    Retrieve the library of all supported training modes.
    """
    return TrainingSuggester.get_available_trainings()


@router.post("/trainings/suggest")
def suggest_trainings(payload: SuggestPayload):
    """
    Analyze game summary stats and return prioritized training recommendations.
    """
    stats_dict = {k: v for k, v in payload.stats.model_dump().items() if v is not None}
    suggestions = TrainingSuggester.suggest_trainings(stats_dict)
    return {
        "username": payload.username,
        "suggestions": suggestions
    }


@router.post("/trainings/suggest-from-replay")
async def suggest_from_replay_file(file: UploadFile = File(...)):
    """
    Upload a replay file (.ttr, .ttrm, or .json), extract telemetry/stats, and suggest training regimens.
    """
    if not (file.filename.endswith(".ttr") or file.filename.endswith(".ttrm") or file.filename.endswith(".json")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload a .ttr, .ttrm, or .json file."
        )
        
    try:
        content = await file.read()
        replay_data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON format. The uploaded file is corrupted or not a valid JSON structure."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while reading the file: {str(e)}"
        )
        
    parsed_replay = TTRParser.parse_replay(replay_data)
    
    meta_stats = parsed_replay.get("metadata", {}).get("stats", {}) or {}
    
    events = parsed_replay.get("events", [])
    event_stats = TrainingSuggester.parse_events_for_stats(events)
    
    # Prioritize official game metadata (which includes accurate finesse fault tracking) over event-parsed heuristics
    merged_stats = {**event_stats, **meta_stats}
    
    # Calculate piece-based finesse rate: perfect_pieces / total_pieces
    pieces = int(merged_stats.get("pieces_placed") or merged_stats.get("pieces") or 0)
    perfect_pieces = merged_stats.get("finesse_perfect_pieces")
    
    if perfect_pieces is not None:
        perfect_pieces = int(perfect_pieces)
    else:
        faults = int(merged_stats.get("finesse_faults") or 0)
        perfect_pieces = max(0, pieces - faults)
        
    finesse_rate = 1.0
    if pieces > 0:
        finesse_rate = max(0.0, min(1.0, perfect_pieces / pieces))
    merged_stats["finesse_rate"] = round(finesse_rate, 4)
    
    suggestions = TrainingSuggester.suggest_trainings(merged_stats)
    
    # Auto-save score to database history
    score_id = None
    try:
        from app.db.database import add_score
        username = parsed_replay.get("metadata", {}).get("username") or "Player"
        score = int(merged_stats.get("score") or 0)
        pps = float(merged_stats.get("pps") or 0.0)
        apm = float(merged_stats.get("apm") or 0.0)
        finesse_faults = int(merged_stats.get("finesse_faults") or 0)
        finesse_rate = float(merged_stats.get("finesse_rate") or 1.0)
        pieces_placed = int(merged_stats.get("pieces_placed") or merged_stats.get("pieces") or 0)
        lines_cleared = int(merged_stats.get("lines") or merged_stats.get("lines_cleared") or 0)
        
        vsscore = merged_stats.get("vsscore")
        if vsscore is None:
            # Fallback VS score calculation: APM + PPS * 20
            vsscore = apm + pps * 20
        vsscore = round(float(vsscore), 2)
        merged_stats["vsscore"] = vsscore

        topcombo = int(merged_stats.get("topcombo") or 0)
        topbtb = int(merged_stats.get("topbtb") or 0)
        tspins = int(merged_stats.get("tspins") or 0)
        clears_dict = merged_stats.get("clears") or {}
        quads = int(clears_dict.get("quads") or 0)
        clears_json = json.dumps(clears_dict) if clears_dict else None

        # Add to merged_stats for response payload
        merged_stats["topcombo"] = topcombo
        merged_stats["topbtb"] = topbtb
        merged_stats["tspins"] = tspins
        merged_stats["quads"] = quads
        merged_stats["clears_json"] = clears_json
        
        # New telemetry fields
        average_planning_latency_ms = float(merged_stats.get("average_planning_latency_ms") or 0.0)
        average_execution_latency_ms = float(merged_stats.get("average_execution_latency_ms") or 0.0)
        double_rotations = int(merged_stats.get("double_rotations") or 0)
        rotate180_count = int(merged_stats.get("rotate180_count") or 0)
        kpp = float(merged_stats.get("keystrokes_per_piece") or merged_stats.get("kpp") or 0.0)
        
        score_id = add_score(
            username=username,
            score=score,
            pps=pps,
            apm=apm,
            finesse_faults=finesse_faults,
            finesse_rate=finesse_rate,
            pieces_placed=pieces_placed,
            lines_cleared=lines_cleared,
            replay_name=file.filename,
            vsscore=vsscore,
            topcombo=topcombo,
            topbtb=topbtb,
            tspins=tspins,
            quads=quads,
            clears_json=clears_json,
            average_planning_latency_ms=average_planning_latency_ms,
            average_execution_latency_ms=average_execution_latency_ms,
            double_rotations=double_rotations,
            rotate180_count=rotate180_count,
            kpp=kpp
        )
    except Exception as e:
        print(f"Failed to auto-save score to history: {e}")
    
    return {
        "metadata": parsed_replay.get("metadata", {}),
        "extracted_stats": merged_stats,
        "suggestions": suggestions,
        "score_id": score_id
    }


@router.get("/scores", response_model=List[Dict[str, Any]])
def read_scores():
    """
    Get all stored scores in history, ordered chronologically.
    """
    try:
        from app.db.database import get_scores
        return get_scores()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch score history: {str(e)}")


@router.get("/scores/{score_id}", response_model=Dict[str, Any])
def read_single_score(score_id: int):
    """
    Retrieve a specific score record by ID, reconstruct the replay analysis payload,
    and generate dynamic suggestions.
    """
    try:
        from app.db.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scores WHERE id = ?", (score_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Score record not found")
            score_data = dict(row)
            
        # Reconstruct the merged_stats dict
        clears_json = score_data.get("clears_json")
        clears_dict = {}
        if clears_json:
            try:
                clears_dict = json.loads(clears_json)
            except Exception:
                pass
                
        merged_stats = {
            "score": score_data["score"],
            "pps": score_data["pps"],
            "apm": score_data["apm"],
            "finesse_faults": score_data["finesse_faults"],
            "finesse_rate": score_data["finesse_rate"],
            "pieces_placed": score_data["pieces_placed"],
            "lines": score_data["lines_cleared"],
            "vsscore": score_data["vsscore"],
            "topcombo": score_data["topcombo"],
            "topbtb": score_data["topbtb"],
            "tspins": score_data["tspins"],
            "quads": score_data["quads"],
            "clears": clears_dict,
            "clears_json": clears_json,
            "average_planning_latency_ms": score_data.get("average_planning_latency_ms") or 0.0,
            "average_execution_latency_ms": score_data.get("average_execution_latency_ms") or 0.0,
            "double_rotations": score_data.get("double_rotations") or 0,
            "rotate180_count": score_data.get("rotate180_count") or 0,
            "keystrokes_per_piece": score_data.get("kpp") or 0.0,
            "kpp": score_data.get("kpp") or 0.0
        }
        
        # Re-run the suggestion engine to get prioritized training recommendations
        suggestions = TrainingSuggester.suggest_trainings(merged_stats)
        
        return {
            "metadata": {
                "username": score_data["username"],
                "stats": merged_stats
            },
            "extracted_stats": merged_stats,
            "suggestions": suggestions,
            "score_id": score_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch score record: {str(e)}")


@router.post("/scores")
def create_score(payload: ScoreCreatePayload):
    """
    Manually add a score entry to the database history.
    """
    try:
        from app.db.database import add_score
        new_id = add_score(
            username=payload.username,
            score=payload.score,
            pps=payload.pps,
            apm=payload.apm,
            finesse_faults=payload.finesse_faults,
            finesse_rate=payload.finesse_rate,
            pieces_placed=payload.pieces_placed,
            lines_cleared=payload.lines_cleared,
            replay_name=payload.replay_name,
            vsscore=payload.vsscore,
            topcombo=payload.topcombo,
            topbtb=payload.topbtb,
            tspins=payload.tspins,
            quads=payload.quads,
            clears_json=payload.clears_json
        )
        return {"status": "success", "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add score to history: {str(e)}")


@router.delete("/scores/clear")
def clear_score_history():
    """
    Delete all scores from history.
    """
    try:
        from app.db.database import clear_scores
        clear_scores()
        return {"status": "success", "message": "Score history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear score history: {str(e)}")


@router.delete("/scores/{score_id}")
def delete_score_entry(score_id: int):
    """
    Delete a single score entry by ID.
    """
    try:
        from app.db.database import delete_score
        deleted = delete_score(score_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Score entry not found")
        return {"status": "success", "message": f"Score entry {score_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete score entry: {str(e)}")


class ChatPayload(BaseModel):
    message: str = Field(..., description="The user query to the AI Coach")
    history: List[Dict[str, str]] = Field([], description="Chat history as a list of role/content pairs")
    current_stats: Optional[Dict[str, Any]] = Field(None, description="Stats of the currently loaded replay, if any")


@router.post("/chat")
def chat_coaching(payload: ChatPayload):
    """
    Handle chat conversation between player and Aegis AI coach.
    Injects database scores history and recent replay analysis suggestions into the prompt.
    """
    try:
        from app.db.database import get_scores
        all_scores = get_scores()
        
        # Calculate suggestions if current stats are provided
        suggestions = None
        if payload.current_stats:
            stats_dict = {k: v for k, v in payload.current_stats.items() if v is not None}
            suggestions = TrainingSuggester.suggest_trainings(stats_dict)
        elif all_scores:
            # Fallback to computing suggestions on the latest stats from database
            latest_run = all_scores[-1]
            suggestions = TrainingSuggester.suggest_trainings(latest_run)
            
        result = ollama_client.query_chat_coaching(
            user_message=payload.message,
            history=payload.history,
            current_stats=payload.current_stats,
            all_scores=all_scores,
            suggestions=suggestions
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during chat routing: {str(e)}"
        )


@router.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """
    WebSocket endpoint for live telemetry streaming from the Chrome extension.
    Aggregates events, provides real-time lookahead unmask flashing, and triggers
    tactical suggestions/interventions.
    """
    await websocket.accept()
    session_events = []
    last_intervention_count = 0
    try:
        while True:
            event = await websocket.receive_json()
            session_events.append(event)
            
            key = event.get("data", {}).get("key")
            evt_type = event.get("type")
            
            # Locked piece checkpoint
            if key == "hardDrop" and evt_type == "keydown":
                stats = TrainingSuggester.parse_events_for_stats(session_events)
                if stats:
                    pieces_placed = stats.get("pieces_placed", 0)
                    # Flashing heuristic: flash every 3 pieces placed
                    if pieces_placed > 0 and pieces_placed % 3 == 0:
                        await websocket.send_json({"action": "flash_unmask"})
                    
                    # Intervention heuristic: if double rotations count grows
                    double_rots = stats.get("double_rotations", 0)
                    if double_rots > last_intervention_count and double_rots >= 2:
                        last_intervention_count = double_rots
                        await websocket.send_json({
                            "action": "intervention",
                            "message": "Finesse alert: Stop double-tapping 90° rotations! Utilize your dedicated 180° rotation input (C key) to save keystrokes and play faster."
                        })
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
