import pytest
from backend.app.core.finesse import FinesseEvaluator

def test_finesse_optimal_calculations():
    """Verify minimum keystroke outputs for various playfield destination grids."""
    # Spawn is col 4
    # Column 0: DAS left -> 1 key
    keys_count, path = FinesseEvaluator.get_optimal_movements("T", target_col=0, target_rot=0)
    assert keys_count == 1
    assert "DAS Left" in path

    # Column 4 (spawn), Rotation 1 (CW) -> 1 key (rotateCW)
    keys_count, path = FinesseEvaluator.get_optimal_movements("I", target_col=4, target_rot=1)
    assert keys_count == 1
    assert "Rotate Clockwise" in path

    # Column 2, Rotation 3 (CCW) -> 2 keys (Tap left twice) + 1 key (rotateCCW) = 3 keys
    keys_count, path = FinesseEvaluator.get_optimal_movements("O", target_col=2, target_rot=3)
    assert keys_count == 3
    assert "Tap Left twice" in path
    assert "Rotate Counter-Clockwise" in path


def test_finesse_evaluation_perfect():
    """Verify that a perfect keystroke sequence does not trigger a finesse fault."""
    result = FinesseEvaluator.evaluate_placement(
        piece="J",
        target_col=0,
        target_rot=0,
        user_keys=["moveLeft"] # DAS Left (represented here as a single input)
    )
    
    assert result["finesse_fault_committed"] is False
    assert result["excess_keystrokes"] == 0
    assert "Perfect" in result["feedback"]


def test_finesse_evaluation_faulty():
    """Verify that excessive tapping correctly flags a finesse fault with exact advice."""
    # User taps moveLeft 4 times to reach column 0 instead of using a single DAS Left hold
    result = FinesseEvaluator.evaluate_placement(
        piece="L",
        target_col=0,
        target_rot=0,
        user_keys=["moveLeft", "moveLeft", "moveLeft", "moveLeft"]
    )
    
    assert result["finesse_fault_committed"] is True
    assert result["user_keystroke_count"] == 4
    assert result["optimal_keystroke_count"] == 1
    assert result["excess_keystrokes"] == 3
    assert "Finesse Fault" in result["feedback"]
    assert "DAS Left to wall" in result["feedback"]
