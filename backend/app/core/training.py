from typing import Dict, Any, List, Optional
from app.core.finesse import FinesseEvaluator
from app.core.speed import PacingEvaluator

TRAINING_MODES = {
    "finesse_rewind": {
        "id": "finesse_rewind",
        "name": "Finesse Rewind",
        "description": "Enforce perfect muscle memory by resetting the board state upon any finesse violation.",
        "benefits": "Builds error-free placement habits and SRS rotation efficiency.",
        "default_config": {
            "rewind_pieces": 3,
            "strict_mode": True
        }
    },
    "lookahead_mask": {
        "id": "lookahead_mask",
        "name": "Lookahead Blind/Ghost Mask",
        "description": "Obscure the active playfield and display only the next queue containers to force lookahead memory.",
        "benefits": "Develops spatial memory and peripheral visual queue planning.",
        "default_config": {
            "mask_mode": "ghost",
            "opacity": 0.85,
            "peek_frequency": 3
        }
    },
    "cheese_race": {
        "id": "cheese_race",
        "name": "Cheese Race / Downstacking Practice",
        "description": "Clear procedurally generated messy rows containing randomized downstack holes.",
        "benefits": "Improves downstacking logic and recovery under stressful clogged board states.",
        "default_config": {
            "garbage_rows": 10,
            "hole_randomness": 0.2
        }
    },
    "speed_pacing": {
        "id": "speed_pacing",
        "name": "Speed Pacing & Rhythm Training",
        "description": "Practice fast dropping with target beats and low mechanical delay thresholds.",
        "benefits": "Overcomes decisional hesitation and accelerates keystroke-to-piece ratios.",
        "default_config": {
            "target_pps": 2.0,
            "max_planning_latency_ms": 150.0
        }
    },
    "opening_mastery": {
        "id": "opening_mastery",
        "name": "Opening Setup Practice",
        "description": "Master classic Tetris opening setups by mirroring standard bag piece configurations.",
        "benefits": "Improves beginning-game attack rates and initial structure optimization.",
        "default_config": {
            "target_openings": ["TKI 3", "DT Cannon", "MKO"],
            "allow_mirrored": True
        }
    },
    "attack_optimization": {
        "id": "attack_optimization",
        "name": "Attack & B2B Chain Optimization",
        "description": "Maximize APM by practicing continuous Back-to-Back line clears and combos.",
        "benefits": "Boosts offensive threat, improves board cleaning efficiency and combo sustain.",
        "default_config": {
            "require_b2b": True,
            "minimum_combo": 2
        }
    }
}

class TrainingSuggester:
    """
    Core analytics suite that maps end-of-game statistics and telemetry
    to customized training suggestions for the user.
    """

    @staticmethod
    def get_available_trainings() -> List[Dict[str, Any]]:
        """Return the library of all supported training modes."""
        return list(TRAINING_MODES.values())

    @classmethod
    def suggest_trainings(cls, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze gameplay statistics and return a prioritized list of suggested trainings.
        Each recommendation includes priority ranking, diagnostic reason, and default config.
        """
        # Extract inputs with defaults
        pps = float(stats.get("pps") or stats.get("pieces_per_second") or 0.0)
        pieces_placed = int(stats.get("pieces_placed") or stats.get("pieces") or 0)
        max_height = int(stats.get("max_height") or 0)
        capped_holes_count = int(stats.get("capped_holes_count") or 0)
        avg_planning = float(stats.get("average_planning_latency_ms") or stats.get("planning_latency_ms") or 0.0)
        avg_execution = float(stats.get("average_execution_latency_ms") or stats.get("execution_duration_ms") or 0.0)
        opening_matched = stats.get("opening_matched", None)
        apm = float(stats.get("apm") or 0.0)
        b2b_spikes = int(stats.get("b2b_spikes") or 0)

        # Resolve finesse faults safely
        finesse_faults = stats.get("finesse_faults")
        if finesse_faults is None:
            finesse_obj = stats.get("finesse")
            if isinstance(finesse_obj, dict):
                finesse_faults = finesse_obj.get("faults", 0)
            elif isinstance(finesse_obj, (int, float)):
                finesse_faults = int(finesse_obj)
            else:
                finesse_faults = 0
        finesse_faults = int(finesse_faults)

        # 1. Finesse Fault Rate calculation
        finesse_rate = 0.0
        if pieces_placed > 0:
            finesse_rate = finesse_faults / pieces_placed

        recommendations = []

        # -- RULE 1: Finesse Rewind --
        # Triggered when finesse fault rate > 15% or total faults is high
        if finesse_rate > 0.15 or finesse_faults > 10:
            score = finesse_rate * 100.0 + (finesse_faults * 0.5)
            reason = (
                f"Your finesse fault rate is {finesse_rate:.1%} ({finesse_faults} faults across {pieces_placed} pieces). "
                "Practicing Finesse Rewind will help you eliminate excessive inputs and build perfect SRS execution muscle memory."
            )
            recommendations.append({
                "training_id": "finesse_rewind",
                "score": round(score, 1),
                "reason": reason,
                "config": TRAINING_MODES["finesse_rewind"]["default_config"]
            })

        # -- RULE 2: Lookahead Blind/Ghost Mask --
        # Triggered when average planning latency > 200ms
        if avg_planning > 200.0:
            score = (avg_planning - 200.0) / 4.0
            reason = (
                f"Your average planning latency is {avg_planning:.1f}ms (target is <200ms), indicating visual decision hesitation at piece spawn. "
                "The Lookahead Mask training obscures the active field, forcing you to focus on upcoming piece queue elements."
            )
            recommendations.append({
                "training_id": "lookahead_mask",
                "score": round(score, 1),
                "reason": reason,
                "config": TRAINING_MODES["lookahead_mask"]["default_config"]
            })

        # -- RULE 3: Cheese Race / Downstacking --
        # Triggered when capped holes or max heights show blockages
        if capped_holes_count >= 3 or max_height >= 14:
            score = (capped_holes_count * 15.0) + max(0.0, (max_height - 10.0) * 3.0)
            reason = (
                f"You ended the session with {capped_holes_count} capped downstack holes and reached a maximum stack height of {max_height}. "
                "Cheese Race will train you to downstack through messy structures and prioritize clean hole access."
            )
            recommendations.append({
                "training_id": "cheese_race",
                "score": round(score, 1),
                "reason": reason,
                "config": TRAINING_MODES["cheese_race"]["default_config"]
            })

        # -- RULE 4: Speed Pacing --
        # Triggered when PPS is slow and execution delay is high
        if pps > 0.0 and pps < 1.5 and avg_execution > 400.0:
            score = (1.5 - pps) * 40.0 + (avg_execution - 400.0) / 10.0
            reason = (
                f"Your speed is {pps:.2f} PPS with a mechanical execution latency of {avg_execution:.1f}ms. "
                "Speed Pacing training will help build rapid muscle execution rhythm and smooth out delayed inputs."
            )
            recommendations.append({
                "training_id": "speed_pacing",
                "score": round(score, 1),
                "reason": reason,
                "config": TRAINING_MODES["speed_pacing"]["default_config"]
            })

        # -- RULE 5: Opening Mastery --
        # Triggered if opening matcher indicates generic stacking
        if opening_matched is False and pieces_placed >= 7:
            score = 25.0
            reason = (
                "Your initial block placements did not match any standard tournament opening setups. "
                "Opening Mastery will teach you optimal start sequences (TKI 3, DT Cannon) to establish an early game advantage."
            )
            recommendations.append({
                "training_id": "opening_mastery",
                "score": score,
                "reason": reason,
                "config": TRAINING_MODES["opening_mastery"]["default_config"]
            })

        # -- RULE 6: Attack Optimization --
        # Triggered if attack rate (APM) is low relative to placement speed, and APM is explicitly tracked
        if pps > 0.0 and "apm" in stats and (apm / pps) < 15.0 and pieces_placed >= 30:
            attack_ratio = apm / pps
            score = (15.0 - attack_ratio) * 3.0 + max(0.0, (3.0 - b2b_spikes) * 10.0)
            reason = (
                f"Your offensive output efficiency is low ({attack_ratio:.1f} APM per PPS) with {b2b_spikes} back-to-back spikes. "
                "Attack Optimization will train you to stack for Quad/T-Spin combos while preserving Back-to-Back status."
            )
            recommendations.append({
                "training_id": "attack_optimization",
                "score": round(score, 1),
                "reason": reason,
                "config": TRAINING_MODES["attack_optimization"]["default_config"]
            })

        # Sort by score descending
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        # Assign priority ranking (1 is highest)
        for idx, rec in enumerate(recommendations):
            rec["priority"] = idx + 1
            # Remove internal score from response to keep payload clean, or keep it for debugging
            # Let's keep it but also provide priority
            
        # Fallback if no specific training triggered
        if not recommendations:
            recommendations.append({
                "training_id": "speed_pacing",
                "priority": 1,
                "score": 10.0,
                "reason": "Your play profile appears well-balanced. We recommend general Speed Pacing training to continue building overall speed and muscle memory.",
                "config": TRAINING_MODES["speed_pacing"]["default_config"]
            })

        return recommendations

    @classmethod
    def parse_events_for_stats(cls, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Segment key events from a replay into piece placements, and extract pacing stats.
        """
        if not events:
            return {}

        pieces = []
        current_piece_events = []
        last_drop_time = 0.0

        for event in events:
            evt_type = event.get("type")
            if evt_type not in ("keydown", "keyup"):
                continue

            key = event.get("data", {}).get("key")
            if not key:
                continue

            frame = event.get("frame", 0)
            subframe = event.get("data", {}).get("subframe", 0.0)
            # Standard conversion: 60fps * 10 subframes = 600 ticks per second (1.6667ms per tick)
            # If subframe is already within frame bounds, we multiply (frame + subframe) by frame duration (16.6667ms)
            evt_time = (frame + subframe) * 16.6667

            current_piece_events.append((key, evt_type, evt_time))

            if key == "hardDrop" and evt_type == "keydown":
                pieces.append({
                    "spawn_time": last_drop_time,
                    "events": current_piece_events
                })
                last_drop_time = evt_time
                current_piece_events = []

        total_pieces = len(pieces)
        if total_pieces == 0:
            return {}

        total_planning_latency = 0.0
        total_execution_duration = 0.0
        finesse_faults = 0
        valid_pacing_count = 0

        for p in pieces:
            spawn_time = p["spawn_time"]
            p_evts = p["events"]

            first_input_time = None
            hard_drop_time = None
            user_keys = []

            for key, etype, etime in p_evts:
                if etype == "keydown":
                    user_keys.append(key)
                    if key != "hardDrop":
                        if first_input_time is None:
                            first_input_time = etime
                    else:
                        hard_drop_time = etime

            if hard_drop_time is None:
                continue

            if first_input_time is None:
                first_input_time = hard_drop_time

            planning_latency = max(0.0, first_input_time - spawn_time)
            execution_duration = max(0.0, hard_drop_time - first_input_time)

            total_planning_latency += planning_latency
            total_execution_duration += execution_duration
            valid_pacing_count += 1

            # Simple fallback check for finesse faults if user_keys has excessive taps
            # Let's count keys. If they use more than 4 keystrokes for simple adjustments, count it as a fault.
            if len(user_keys) > 5:
                finesse_faults += 1

        avg_planning = total_planning_latency / valid_pacing_count if valid_pacing_count > 0 else 0.0
        avg_execution = total_execution_duration / valid_pacing_count if valid_pacing_count > 0 else 0.0
        
        # Estimate PPS based on total match time
        total_time_sec = last_drop_time / 1000.0
        pps = total_pieces / total_time_sec if total_time_sec > 0 else 0.0

        return {
            "pieces_placed": total_pieces,
            "pps": round(pps, 2),
            "finesse_faults": finesse_faults,
            "average_planning_latency_ms": round(avg_planning, 1),
            "average_execution_latency_ms": round(avg_execution, 1)
        }
