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


def test_parse_real_ttr_file():
    """Verify that parsing the real 40line.ttr extracts the correct stats including perfect pieces."""
    import os
    import json
    path = os.path.expanduser('~/Downloads/40line.ttr')
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        result = TTRParser.parse_replay(data)
        stats = result.get("metadata", {}).get("stats", {})
        assert stats.get("finesse_faults") == 28
        assert stats.get("finesse_perfect_pieces") == 84
        assert stats.get("pieces") == 106


def test_parser_extracts_clears_spins_combos():
    """Verify that clears, spins, and combo stats are successfully extracted by the parser."""
    mock_data = {
        "replay": {
            "results": {
                "stats": {
                    "score": 120000,
                    "lines": 40,
                    "piecesplaced": 100,
                    "clears": {
                        "singles": 5,
                        "doubles": 2,
                        "triples": 1,
                        "quads": 7,
                        "tspindoubles": 3
                    },
                    "topcombo": 6,
                    "topbtb": 4,
                    "tspins": 5
                },
                "aggregatestats": {
                    "pps": 1.8,
                    "apm": 30.5,
                    "vsscore": 65.4
                }
            }
        }
    }
    metadata = TTRParser.extract_metadata(mock_data)
    stats = metadata.get("stats", {})
    
    assert stats.get("topcombo") == 6
    assert stats.get("topbtb") == 4
    assert stats.get("tspins") == 5
    assert stats.get("vsscore") == 65.4
    assert stats.get("clears", {}).get("quads") == 7
    assert stats.get("clears", {}).get("tspindoubles") == 3

