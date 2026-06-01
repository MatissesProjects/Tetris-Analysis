import pytest
from backend.app.core.speed import PacingEvaluator

def test_pacing_flow_zone():
    """Verify that fast planning and execution yields Flow Zone diagnosis."""
    # Spawn at 0ms, First input at 100ms (100ms planning latency)
    # Dropped at 300ms (200ms execution duration)
    # Total cycle duration = 300ms -> 3.33 PPS
    result = PacingEvaluator.evaluate_pacing(
        spawn_time_ms=0.0,
        first_key_time_ms=100.0,
        drop_time_ms=300.0,
        key_count=3,
        finesse_faults=0
    )
    
    assert result["pieces_per_second"] == 3.33
    assert result["planning_latency_ms"] == 100.0
    assert result["execution_duration_ms"] == 200.0
    assert result["pacing_zone"] == "Flow Zone"
    assert "Optimal Flow" in result["coaching_advice"]
    assert result["flow_state_score"] == 100.0  # Perfect flow score


def test_pacing_planning_hesitation():
    """Verify that slow decision times correctly flag planning hesitation."""
    # Spawn at 0ms, First input at 300ms (300ms planning latency > 220ms threshold)
    # Dropped at 500ms
    result = PacingEvaluator.evaluate_pacing(
        spawn_time_ms=0.0,
        first_key_time_ms=300.0,
        drop_time_ms=500.0,
        key_count=2,
        finesse_faults=0
    )
    
    assert result["pacing_zone"] == "Planning Hesitation"
    assert "Decisional Hesitation" in result["coaching_advice"]


def test_pacing_mechanical_hesitation():
    """Verify that slow keyboard executions correctly flag mechanical hesitation."""
    # Spawn at 0ms, First input at 50ms (50ms planning latency)
    # Dropped at 600ms (550ms execution duration > 450ms threshold)
    result = PacingEvaluator.evaluate_pacing(
        spawn_time_ms=0.0,
        first_key_time_ms=50.0,
        drop_time_ms=600.0,
        key_count=4,
        finesse_faults=0
    )
    
    assert result["pacing_zone"] == "Mechanical Hesitation"
    assert "Mechanical Hesitation" in result["coaching_advice"]


def test_pacing_flow_score_penalty():
    """Verify that committing a finesse fault applies a severe flow score penalty."""
    result = PacingEvaluator.evaluate_pacing(
        spawn_time_ms=0.0,
        first_key_time_ms=100.0,
        drop_time_ms=300.0,
        key_count=3,
        finesse_faults=1 # Fault!
    )
    
    # Base score was 100, but 0.6 multiplier applied
    assert result["flow_state_score"] == 60.0
