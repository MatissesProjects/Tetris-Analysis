import pytest
from backend.app.core.lookahead import LookaheadPlanner

def test_lookahead_well_fill():
    """Verify that a vertical I-piece is recommended when a deep column well exists."""
    # Column 4 has a deep well (height 0), others have height 4
    heights = [4, 4, 4, 4, 0, 4, 4, 4, 4, 4]
    queue = ["I"]
    
    plan = LookaheadPlanner.calculate_queue_blueprint(heights, queue)
    
    assert len(plan) == 1
    action = plan[0]
    assert action["piece"] == "I"
    assert action["recommended_column"] == 4
    assert action["recommended_rotation"] == 1 # Vertical
    assert "well" in action["placement_logic"]


def test_lookahead_o_piece_flat():
    """Verify that square O-piece is laid across the lowest adjacent columns."""
    # Columns 2 and 3 are lowest
    heights = [5, 5, 2, 2, 5, 5, 5, 5, 5, 5]
    queue = ["O"]
    
    plan = LookaheadPlanner.calculate_queue_blueprint(heights, queue)
    
    assert len(plan) == 1
    action = plan[0]
    assert action["piece"] == "O"
    assert action["recommended_column"] == 2
    assert "square O-piece" in action["placement_logic"]


def test_lookahead_entire_blueprint_generation():
    """Verify that a full 5-piece queue yields a coordinated sequence of placements."""
    heights = [0] * 10
    queue = ["I", "O", "T", "S", "Z"]
    
    blueprint = LookaheadPlanner.calculate_queue_blueprint(heights, queue)
    
    assert len(blueprint) == 5
    pieces = [p["piece"] for p in blueprint]
    assert pieces == ["I", "O", "T", "S", "Z"]
    
    for item in blueprint:
        assert "queue_index" in item
        assert "recommended_column" in item
        assert "recommended_rotation" in item
        assert "placement_logic" in item
