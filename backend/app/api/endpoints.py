import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
from app.parser.ttr_parser import TTRParser

router = APIRouter()

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
