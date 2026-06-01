import pytest
from backend.app.core.eltetris import ElTetrisEvaluator

def test_eltetris_empty_board():
    """Verify clean empty board scores sit at perfect 100 ratings."""
    grid = [[0] * 10 for _ in range(40)]
    heights = [0] * 10
    bumpiness = [0] * 9
    
    result = ElTetrisEvaluator.evaluate_board(
        grid=grid,
        heights=heights,
        bumpiness=bumpiness,
        holes_count=0
    )
    
    assert result["eltetris_fitness_rating"] == 100.0
    assert result["aggregate_height"] == 0
    assert result["wells_count"] == 0
    assert "structural_bottlenecks" in result
    assert len(result["structural_bottlenecks"]) == 0


def test_eltetris_transitions():
    """Verify that row and column cell transitions are evaluated perfectly."""
    grid = [[0] * 10 for _ in range(40)]
    
    # Place a single block at bottom row, column 2
    grid[0][2] = 1
    
    row_t = ElTetrisEvaluator.get_row_transitions(grid)
    col_t = ElTetrisEvaluator.get_column_transitions(grid)
    
    # Bottom row transition checkpoints:
    # Wall (filled) -> col 0 (empty) [1]
    # col 1 (empty) -> col 2 (filled) [2]
    # col 2 (filled) -> col 3 (empty) [3]
    # col 9 (empty) -> Wall (filled) [4]
    # Total row transitions for r=0 is 4. Other 39 empty rows have 2 transitions each (78). Total = 82.
    assert row_t == 82

    # Column transition checkpoints:
    # Floor (filled) -> col 2 row 0 (filled) [0]
    # col 2 row 0 (filled) -> col 2 row 1 (empty) [1]
    # Total transitions in column 2 = 1. Other columns have 1 transition (floor to empty).
    # Total col transitions = 1 (for col 2) + 9 (for other columns) = 10 transitions.
    assert col_t == 10


def test_eltetris_wells_depth():
    """Verify that deep narrow wells are identified with exact depths."""
    # Column 5 has a deep well (adjacent columns 4 and 6 are height 5 and 6)
    # Heights: [0, 0, 0, 0, 5, 1, 6, 0, 0, 0]
    # Column 5 has height 1. Adjacent heights are 5 (left) and 6 (right).
    # Well depth = min(5, 6) - 1 = 4.
    heights = [0, 0, 0, 0, 5, 1, 6, 0, 0, 0]
    
    wells = ElTetrisEvaluator.get_wells(heights)
    assert len(wells) == 1
    assert wells[0]["column"] == 5
    assert wells[0]["depth"] == 4


def test_eltetris_diagnostics():
    """Verify that structural bottlenecks trigger correct coaching flags."""
    grid = [[0] * 10 for _ in range(40)]
    
    # 5-level deep well
    heights = [0, 0, 0, 0, 6, 1, 6, 0, 0, 0]
    
    result = ElTetrisEvaluator.evaluate_board(
        grid=grid,
        heights=heights,
        bumpiness=[0]*9,
        holes_count=4 # High holes
    )
    
    # Diagnostics should spot wells and holes
    diagnostics = result["structural_bottlenecks"]
    assert len(diagnostics) == 2
    
    well_flag = any("Deep Well Obstruction" in d for d in diagnostics)
    hole_flag = any("Hole Accumulation" in d for d in diagnostics)
    
    assert well_flag is True
    assert hole_flag is True
