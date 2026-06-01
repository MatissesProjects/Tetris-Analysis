import pytest
from backend.app.parser.ttr_parser import TTRParser

def test_parser_extracts_seed_from_various_paths():
    """Verify the parser resiliently searches all known seed locations in replay JSON."""
    
    # Path: data.game.seed
    payload_1 = {
        "data": {
            "game": {
                "seed": 987654321
            }
        }
    }
    assert TTRParser.extract_seed(payload_1) == 987654321
    
    # Path: data.opts.seed
    payload_2 = {
        "data": {
            "opts": {
                "seed": 112233
            }
        }
    }
    assert TTRParser.extract_seed(payload_2) == 112233
    
    # Path: seed at root
    payload_3 = {
        "seed": 554433
    }
    assert TTRParser.extract_seed(payload_3) == 554433


def test_parser_extracts_events_and_metadata():
    """Verify events are correctly traversed and user stats are compiled."""
    mock_events = [
        {"frame": 10, "type": "keydown", "data": {"key": "moveLeft", "subframe": 0.2}},
        {"frame": 12, "type": "keyup", "data": {"key": "moveLeft", "subframe": 0.8}},
        {"frame": 20, "type": "keydown", "data": {"key": "hardDrop", "subframe": 0.0}}
    ]
    
    mock_replay = {
        "data": {
            "user": {
                "username": "TetrisPro"
            },
            "stats": {
                "score": 50000,
                "pps": 2.4,
                "lines": 40
            },
            "game": {
                "seed": 8888
            },
            "events": mock_events
        }
    }
    
    # Parse full replay
    result = TTRParser.parse_replay(mock_replay)
    
    assert result["seed"] == 8888
    assert result["metadata"]["username"] == "TetrisPro"
    assert result["metadata"]["stats"]["score"] == 50000
    assert result["metadata"]["stats"]["pps"] == 2.4
    assert result["events_count"] == 3
    assert result["events"] == mock_events
    
    # Verify projected queue starts with the correct number of items (100)
    assert len(result["projected_queue"]) == 100
    # The queue elements should be valid tetromino symbols
    valid_pieces = {"Z", "L", "O", "S", "I", "J", "T"}
    for piece in result["projected_queue"]:
        assert piece in valid_pieces
