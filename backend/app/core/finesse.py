from typing import List, Dict, Any, Tuple

class FinesseEvaluator:
    """
    Evaluator for tracking Tetris finesse faults.
    Finesse defines the mathematically optimal sequence of keystrokes 
    to position a piece at a target column and rotation state under SRS (Super Rotation System).
    """

    @staticmethod
    def get_optimal_movements(piece: str, target_col: int, target_rot: int) -> Tuple[int, str]:
        """
        Calculate the absolute minimum keystroke count and description for moving
        a piece from spawn (column 4) to target column and rotation state.
        
        piece: T, I, O, L, J, S, Z
        target_col: 0 to 9
        target_rot: 0 (spawn), 1 (CW), 2 (180), 3 (CCW)
        """
        # 1. Rotation optimal cost
        rot_keys = 0
        rot_desc = ""
        if target_rot == 1:
            rot_keys = 1
            rot_desc = "Rotate Clockwise"
        elif target_rot == 2:
            rot_keys = 1  # 180 key exists
            rot_desc = "Rotate 180"
        elif target_rot == 3:
            rot_keys = 1
            rot_desc = "Rotate Counter-Clockwise"

        # 2. Horizontal movement optimal cost
        # Pieces spawn at column 4
        spawn_col = 4
        
        # Calculate tap counts
        tap_cost = abs(target_col - spawn_col)
        
        # Calculate DAS (Auto-shift to walls) counts
        # DAS to left (col 0): 1 input (DAS Left)
        # DAS to right (col 9): 1 input (DAS Right)
        
        if target_col == 0:
            move_keys = 1
            move_desc = "DAS Left to wall"
        elif target_col == 9:
            move_keys = 1
            move_desc = "DAS Right to wall"
        elif target_col == 1:
            # Tap left 3 times (3) or DAS left + tap right once (2)
            if tap_cost < 2:
                move_keys = tap_cost
                move_desc = f"Tap Left {tap_cost} times"
            else:
                move_keys = 2
                move_desc = "DAS Left to wall, then Tap Right once"
        elif target_col == 2:
            # Tap left 2 times (2) or DAS left + tap right twice (3)
            move_keys = 2
            move_desc = "Tap Left twice"
        elif target_col == 8:
            # Tap right 4 times (4) or DAS right + tap left once (2)
            move_keys = 2
            move_desc = "DAS Right to wall, then Tap Left once"
        elif target_col == 7:
            # Tap right 3 times (3) or DAS right + tap left twice (3)
            move_keys = 3
            move_desc = "Tap Right 3 times or DAS Right + Tap Left twice"
        else:
            # Columns 3, 4, 5, 6
            if target_col > spawn_col:
                move_keys = tap_cost
                move_desc = f"Tap Right {tap_cost} times"
            elif target_col < spawn_col:
                move_keys = tap_cost
                move_desc = f"Tap Left {tap_cost} times"
            else:
                move_keys = 0
                move_desc = "No movement required"

        total_keys = rot_keys + move_keys
        
        # Combine descriptions
        parts = []
        if move_desc and move_keys > 0:
            parts.append(move_desc)
        if rot_desc and rot_keys > 0:
            parts.append(rot_desc)
            
        full_desc = " + ".join(parts) if parts else "Hard Drop instantly"
        
        return total_keys, full_desc

    @classmethod
    def evaluate_placement(
        cls,
        piece: str,
        target_col: int,
        target_rot: int,
        user_keys: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate a single piece placement against mathematical optimal finesse standards.
        user_keys: List of inputs logged for the piece (e.g. ['moveLeft', 'rotateCW'])
        """
        # Clean user keys to only include movement and rotation inputs
        filtered_keys = [
            k for k in user_keys 
            if k in {"moveLeft", "moveRight", "rotateCW", "rotateCCW", "rotate180", "softDrop"}
        ]
        
        user_count = len(filtered_keys)
        optimal_count, optimal_desc = cls.get_optimal_movements(piece, target_col, target_rot)
        
        fault = user_count > optimal_count
        excess_keys = max(0, user_count - optimal_count)
        
        return {
            "piece": piece,
            "target_column": target_col,
            "target_rotation": target_rot,
            "user_keystroke_count": user_count,
            "user_keystroke_list": filtered_keys,
            "optimal_keystroke_count": optimal_count,
            "optimal_path": optimal_desc,
            "finesse_fault_committed": fault,
            "excess_keystrokes": excess_keys,
            "feedback": (
                "Perfect Finesse placement."
                if not fault else
                f"Finesse Fault: Used {user_count} keys instead of {optimal_count}. Optimal path: {optimal_desc}."
            )
        }
