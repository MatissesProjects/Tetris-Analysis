import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.parser.ttr_parser import TTRParser
from app.core.vectorizer import BoardVectorizer
from app.index.kdtree_index import grounding_index
from app.core.ollama_client import ollama_client
from app.core.finesse import FinesseEvaluator
from app.core.speed import PacingEvaluator
from app.core.lookahead import LookaheadPlanner
from app.core.eltetris import ElTetrisEvaluator

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
