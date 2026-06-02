import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from fastapi import UploadFile

from backend.app.core.training import TrainingSuggester, TRAINING_MODES
from backend.app.api.endpoints import (
    get_available_trainings,
    suggest_trainings,
    suggest_from_replay_file,
    SuggestPayload,
    GameStatsPayload
)

def test_get_available_trainings():
    """Verify that available trainings library is correctly returned."""
    trainings = TrainingSuggester.get_available_trainings()
    assert len(trainings) == 6
    ids = {t["id"] for t in trainings}
    assert "finesse_rewind" in ids
    assert "lookahead_mask" in ids
    assert "cheese_race" in ids
    assert "speed_pacing" in ids
    assert "opening_mastery" in ids
    assert "attack_optimization" in ids


def test_suggest_finesse_rewind():
    """Verify that a high finesse fault rate suggests Finesse Rewind."""
    stats = {
        "pieces_placed": 100,
        "finesse_faults": 20,  # 20% fault rate
    }
    suggestions = TrainingSuggester.suggest_trainings(stats)
    assert len(suggestions) >= 1
    assert suggestions[0]["training_id"] == "finesse_rewind"
    assert "finesse fault rate is 20.0%" in suggestions[0]["reason"]


def test_suggest_lookahead_mask():
    """Verify that high planning latency suggests Lookahead Mask."""
    stats = {
        "pieces_placed": 10,
        "average_planning_latency_ms": 250.0,
    }
    suggestions = TrainingSuggester.suggest_trainings(stats)
    assert len(suggestions) >= 1
    assert any(s["training_id"] == "lookahead_mask" for s in suggestions)
    mask_sugg = [s for s in suggestions if s["training_id"] == "lookahead_mask"][0]
    assert "average planning latency is 250.0ms" in mask_sugg["reason"]


def test_suggest_cheese_race():
    """Verify that high board height or capped holes suggest Cheese Race."""
    stats = {
        "max_height": 15,
        "capped_holes_count": 4,
    }
    suggestions = TrainingSuggester.suggest_trainings(stats)
    assert len(suggestions) >= 1
    assert suggestions[0]["training_id"] == "cheese_race"
    assert "4 capped downstack holes" in suggestions[0]["reason"]
    assert "maximum stack height of 15" in suggestions[0]["reason"]


def test_suggest_speed_pacing():
    """Verify that low speed and high execution delay suggest Speed Pacing."""
    stats = {
        "pps": 1.2,
        "average_execution_latency_ms": 450.0,
    }
    suggestions = TrainingSuggester.suggest_trainings(stats)
    assert len(suggestions) >= 1
    assert suggestions[0]["training_id"] == "speed_pacing"
    assert "speed is 1.20 PPS" in suggestions[0]["reason"]


def test_suggest_opening_mastery():
    """Verify that failing to match openings suggests Opening Mastery."""
    stats = {
        "pieces_placed": 10,
        "opening_matched": False,
    }
    suggestions = TrainingSuggester.suggest_trainings(stats)
    assert len(suggestions) >= 1
    assert any(s["training_id"] == "opening_mastery" for s in suggestions)


def test_suggest_attack_optimization():
    """Verify that low attack efficiency suggests Attack Optimization."""
    stats = {
        "pieces_placed": 50,
        "pps": 2.0,
        "apm": 10.0,  # 5 APM/PPS (very low)
        "b2b_spikes": 1,
    }
    suggestions = TrainingSuggester.suggest_trainings(stats)
    assert len(suggestions) >= 1
    assert any(s["training_id"] == "attack_optimization" for s in suggestions)


def test_suggest_fallback_balanced():
    """Verify that balanced stats suggest default Speed Pacing fallback."""
    stats = {
        "pieces_placed": 50,
        "pps": 2.0,
        "finesse_faults": 0,
        "max_height": 2,
        "average_planning_latency_ms": 100.0,
        "average_execution_latency_ms": 200.0,
        "opening_matched": True,
        "apm": 40.0,
        "b2b_spikes": 5
    }
    suggestions = TrainingSuggester.suggest_trainings(stats)
    assert len(suggestions) == 1
    assert suggestions[0]["training_id"] == "speed_pacing"
    assert "well-balanced" in suggestions[0]["reason"]


def test_parse_events_for_stats():
    """Verify parsing replay events constructs correct pacing/finesse stats."""
    # 2 pieces, first spawn at 0, first input at 100, hardDrop at 300
    # second spawn at 300, first input at 450, hardDrop at 800
    events = [
        # Piece 1
        {"frame": 6, "type": "keydown", "data": {"key": "moveLeft", "subframe": 0.0}},  # time = 6 * 16.6667 = 100ms
        {"frame": 18, "type": "keydown", "data": {"key": "hardDrop", "subframe": 0.0}}, # time = 18 * 16.6667 = 300ms
        # Piece 2
        {"frame": 27, "type": "keydown", "data": {"key": "rotateCW", "subframe": 0.0}}, # time = 27 * 16.6667 = 450ms
        {"frame": 48, "type": "keydown", "data": {"key": "hardDrop", "subframe": 0.0}}, # time = 48 * 16.6667 = 800ms
    ]

    stats = TrainingSuggester.parse_events_for_stats(events)
    assert stats["pieces_placed"] == 2
    # Total match time is 800ms (0.8s) -> 2 / 0.8 = 2.5 PPS
    assert stats["pps"] == 2.5
    # First piece planning = 100 - 0 = 100. Second piece planning = 450 - 300 = 150. Avg = 125ms
    assert stats["average_planning_latency_ms"] == 125.0
    # First piece execution = 300 - 100 = 200. Second piece execution = 800 - 450 = 350. Avg = 275ms
    assert stats["average_execution_latency_ms"] == 275.0


def test_api_get_available_trainings():
    """Verify get_available_trainings API endpoint."""
    res = get_available_trainings()
    assert isinstance(res, list)
    assert len(res) == 6


def test_api_suggest_trainings():
    """Verify suggest_trainings API endpoint."""
    payload = SuggestPayload(
        username="Tester",
        stats=GameStatsPayload(
            pps=1.0,
            pieces_placed=100,
            finesse_faults=25,
            average_execution_latency_ms=500.0
        )
    )
    res = suggest_trainings(payload)
    assert res["username"] == "Tester"
    suggestions = res["suggestions"]
    assert len(suggestions) >= 2
    assert suggestions[0]["training_id"] == "finesse_rewind"


@pytest.mark.anyio
async def test_api_suggest_from_replay():
    """Verify suggest_from_replay_file API endpoint."""
    # Create mock replay file content
    mock_replay = {
        "data": {
            "user": {"username": "ReplayTester"},
            "stats": {"pps": 1.1},
            "game": {"seed": 12345},
            "events": [
                {"frame": 12, "type": "keydown", "data": {"key": "moveRight", "subframe": 0.0}},
                {"frame": 24, "type": "keydown", "data": {"key": "hardDrop", "subframe": 0.0}},
            ]
        }
    }
    content = json.dumps(mock_replay).encode("utf-8")
    
    # Mock UploadFile
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "test.ttr"
    mock_file.read.return_value = content
    
    res = await suggest_from_replay_file(mock_file)
    assert res["metadata"]["username"] == "ReplayTester"
    assert "suggestions" in res
    assert len(res["suggestions"]) >= 1
