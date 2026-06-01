from typing import Dict, Any

class PacingEvaluator:
    """
    Evaluates speed, execution pacing, and planning hesitation metrics.
    Helps players rebuild speed (PPS) while maintaining perfect finesse muscle memory.
    """

    @staticmethod
    def evaluate_pacing(
        spawn_time_ms: float,
        first_key_time_ms: float,
        drop_time_ms: float,
        key_count: int,
        finesse_faults: int
    ) -> Dict[str, Any]:
        """
        Evaluate speed pacing for a single piece cycle.
        
        spawn_time_ms: Timestamp when the piece spawned.
        first_key_time_ms: Timestamp of the player's first input for this piece.
        drop_time_ms: Timestamp when hardDrop was executed.
        key_count: Total keys used.
        finesse_faults: Faults count in this placement (0 or 1).
        """
        # Calculations
        placement_duration = max(50.0, drop_time_ms - spawn_time_ms) / 1000.0  # seconds
        pps = 1.0 / placement_duration
        
        # Planning hesitation (spawn to first input)
        planning_latency_ms = max(0.0, first_key_time_ms - spawn_time_ms)
        
        # Mechanical execution speed (first input to placement)
        execution_duration_ms = max(0.0, drop_time_ms - first_key_time_ms)
        
        # Keystrokes Per Piece (KPP)
        kpp = float(key_count)

        # Diagnose bottlenecks
        # 1. High hesitation (planning bottleneck): user takes too long to decide where to put the piece
        # 2. Slow execution (mechanical bottleneck): user decides fast but inputs keypresses slowly
        # 3. Flow zone: fast planning and execution
        
        advice = ""
        zone = "Balanced"
        
        if planning_latency_ms > 220.0:
            zone = "Planning Hesitation"
            advice = (
                "Decisional Hesitation: You took "
                f"{int(planning_latency_ms)}ms before your first keystroke. Scan upcoming queue early "
                "to decide placements prior to spawn, bypassing visual planning lag."
            )
        elif execution_duration_ms > 450.0:
            zone = "Mechanical Hesitation"
            advice = (
                "Mechanical Hesitation: Decided placement quickly, but keypress execution took "
                f"{int(execution_duration_ms)}ms. Focus on clean DAS holding and smooth rotations."
            )
        else:
            zone = "Flow Zone"
            advice = (
                "Optimal Flow: Sub-200ms planning time and fast mechanical drops. "
                "Your finesse muscle memory is becoming automatic."
            )
            
        # Balanced flow rating (0 to 100) combining speed and finesse
        # Finesse penalty: faults immediately impact flow stability
        base_flow = min(100.0, pps * 30.0) # 3.3 PPS reaches 100 base
        finesse_multiplier = 1.0 if finesse_faults == 0 else 0.6
        flow_score = float(round(base_flow * finesse_multiplier, 1))

        return {
            "pieces_per_second": round(pps, 2),
            "planning_latency_ms": round(planning_latency_ms, 1),
            "execution_duration_ms": round(execution_duration_ms, 1),
            "keystrokes_per_piece": kpp,
            "finesse_faults": finesse_faults,
            "pacing_zone": zone,
            "coaching_advice": advice,
            "flow_state_score": flow_score
        }
