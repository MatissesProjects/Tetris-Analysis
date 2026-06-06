from typing import Dict, Any

class AttackCalculator:
    """
    Garbage Attack & APM Efficiency Coach.
    Uses canonical TETR.IO Wiki formulas (base lines + B2B + Combo Multipliers)
    to audit damage output, spike threat, and resource efficiency.
    """

    @staticmethod
    def calculate_combo_garbage(combo: int) -> int:
        """
        Standard TETR.IO combo table mapping combo count to added garbage lines.
        """
        if combo <= 0:
            return 0
        elif combo == 1:
            return 1
        elif combo == 2:
            return 1
        elif combo == 3:
            return 2
        elif combo == 4:
            return 2
        elif combo == 5:
            return 3
        elif combo == 6:
            return 3
        elif combo == 7:
            return 4
        elif combo == 8:
            return 4
        elif combo == 9:
            return 4
        else:
            return 5  # Combo 10+ caps at +5 lines per drop

    @classmethod
    def evaluate_clear(
        cls,
        clear_type: str,
        b2b_chain_length: int,
        combo_count: int
    ) -> Dict[str, Any]:
        """
        Evaluate a line clear event and calculate the exact garbage sent under TETR.IO rules.
        
        clear_type: single, double, triple, quad (Tetris), tspin_mini, tspin_single, tspin_double, tspin_triple, perfect_clear
        b2b_chain_length: Current consecutive B2B chain length.
        combo_count: Current combo count (consecutive line clears).
        """
        # 1. Base Attack
        base_map = {
            "single": 0,
            "double": 1,
            "triple": 2,
            "quad": 4,          # Tetris
            "tspin_mini": 0,
            "tspin_mini_single": 0,
            "tspin_mini_double": 1,
            "tspin_mini_triple": 2,
            "tspin_single": 2,
            "tspin_double": 4,
            "tspin_triple": 6,
            "jspin_mini": 0,
            "jspin_mini_single": 0,
            "jspin_mini_double": 1,
            "jspin_mini_triple": 2,
            "jspin_single": 2,
            "jspin_double": 4,
            "jspin_triple": 6,
            "lspin_mini": 0,
            "lspin_mini_single": 0,
            "lspin_mini_double": 1,
            "lspin_mini_triple": 2,
            "lspin_single": 2,
            "lspin_double": 4,
            "lspin_triple": 6,
            "perfect_clear": 10
        }
        
        base_lines = base_map.get(clear_type.lower(), 0)
        
        # 2. Back-to-Back (B2B) Bonus
        is_spin = "spin" in clear_type.lower()
        is_difficult = clear_type.lower() == "quad" or is_spin
        b2b_bonus = 0
        b2b_active = b2b_chain_length > 0
        
        if is_difficult and b2b_active:
            # Under standard rules, active B2B adds +1 garbage
            b2b_bonus = 1
            
        # 3. Combo Bonus
        combo_bonus = cls.calculate_combo_garbage(combo_count)
        
        # Total Garbage Sent
        total_garbage = base_lines + b2b_bonus + combo_bonus
        
        # Action coaching and diagnostics
        verdict = ""
        category = "Defensive"
        
        if clear_type == "single":
            category = "Inefficient"
            verdict = (
                "B2B Break Hazard: You cleared a Single row which sends 0 garbage and breaks your active B2B chain. "
                "Stack higher to clear Quads or T-spins instead, preserving high B2B multipliers."
            )
        elif total_garbage >= 6:
            category = "Spike Attack"
            verdict = (
                f"Spike Threat: Executed a massive {total_garbage}-line garbage spike. "
                "Excellent combination of B2B and combo modifiers to overwhelm opponent boards."
            )
        elif is_difficult:
            category = "B2B Engine"
            verdict = (
                f"B2B Engine Maintained: Sent {total_garbage} garbage lines. "
                "Excellent play to secure consistent damage pressure without stack expansion."
            )
        else:
            category = "Downstack Pace"
            verdict = f"Clean clear: Sent {total_garbage} garbage lines to lower column weight."
            
        return {
            "clear_type": clear_type,
            "base_garbage": base_lines,
            "b2b_bonus": b2b_bonus,
            "combo_bonus": combo_bonus,
            "total_garbage_sent": total_garbage,
            "attack_category": category,
            "tactical_coaching": verdict
        }
