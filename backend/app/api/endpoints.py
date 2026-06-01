import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.parser.ttr_parser import TTRParser
from app.index.kdtree_index import grounding_index

router = APIRouter()

class GridPayload(BaseModel):
    grid: List[List[int]] = Field(..., description="10x40 integer matrix representing playfield blocks (0=empty, 1=filled)")

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

