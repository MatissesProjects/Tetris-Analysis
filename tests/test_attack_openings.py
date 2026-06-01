import pytest
from backend.app.core.attack import AttackCalculator
from backend.app.core.openings import OpeningMatcher

def test_attack_single_b2b_break():
    """Verify that clearing a single breaks B2B and warns the player."""
    result = AttackCalculator.evaluate_clear(
        clear_type="single",
        b2b_chain_length=4,
        combo_count=0
    )
    
    assert result["total_garbage_sent"] == 0
    assert result["attack_category"] == "Inefficient"
    assert "B2B Break Hazard" in result["tactical_coaching"]


def test_attack_quad_b2b_spike():
    """Verify that a B2B Quad clear with a combo yields massive spike ratings."""
    # Quad base (4) + active B2B (1) + combo 3 bonus (2) = 7 garbage lines
    result = AttackCalculator.evaluate_clear(
        clear_type="quad",
        b2b_chain_length=2,
        combo_count=3
    )
    
    assert result["total_garbage_sent"] == 7
    assert result["attack_category"] == "Spike Attack"
    assert "Spike Threat" in result["tactical_coaching"]


def test_opening_matcher_tki3():
    """Verify that TKI 3 flat-top opening aligns with first bag placements."""
    # Matches TKI 3 columns exactly: [0, 8, 3, 5, 2]
    result = OpeningMatcher.match_opening(
        pieces_placed=["J", "L", "I", "S", "Z"],
        columns_placed=[0, 8, 3, 5, 2]
    )
    
    assert result["opening_recognized"] is True
    assert result["matched_name"] == "TKI 3 (Flat Top)"
    assert result["matching_percentage"] == 100.0
    assert "TKI 3" in result["coaching_tip"]


def test_opening_matcher_generic():
    """Verify that random early placements fall back to generic stacking diagnosis."""
    result = OpeningMatcher.match_opening(
        pieces_placed=["O", "I", "S", "Z", "T"],
        columns_placed=[4, 4, 4, 4, 4]
    )
    
    assert result["opening_recognized"] is False
    assert result["matched_name"] == "Generic Open Stacking"
    assert result["matching_percentage"] == 0.0
    assert "Generic Open Stacking" in result["coaching_tip"]
