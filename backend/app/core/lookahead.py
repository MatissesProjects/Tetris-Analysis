from typing import List, Dict, Any

class LookaheadPlanner:
    """
    Lookahead Planning and Queue Forecasting Suite.
    Calculates coordinated placement blue-prints for the next 5 pieces in the queue
    to help players visualize multi-step stack builds rather than placing pieces reactively.
    """

    @staticmethod
    def calculate_queue_blueprint(
        grid_heights: List[int],
        queue: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Compute coordinated landing columns and rotations for the next 5 upcoming pieces
        to maintain a stable flat surface profile.
        
        grid_heights: List of current 10 column heights
        queue: Next 5 pieces in the queue (e.g. ['I', 'T', 'O', 'S', 'Z'])
        """
        active_heights = list(grid_heights)
        blueprint = []
        
        # Standard Tetromino column spans and optimal flat profiles
        # For simplicity and speed, we map optimal placement strategies
        # to flatten the topology recursively for the 5-piece preview.
        for idx, piece in enumerate(queue[:5]):
            target_col = 0
            target_rot = 0
            reason = ""
            
            # Find the lowest local valley to flatten the topology
            # T, O, I, L, J, S, Z placements
            if piece == "I":
                # I-piece is perfect to flat-fill a deep column well, or lay flat to bridge valleys
                # Look for columns with height <= current average - 3 (well)
                avg_h = sum(active_heights) / 10
                deep_well = -1
                for col in range(10):
                    if active_heights[col] <= avg_h - 3:
                        deep_well = col
                        break
                        
                if deep_well != -1:
                    target_col = deep_well
                    target_rot = 1 # Vertical drop into well
                    active_heights[deep_well] += 4
                    reason = f"Drop vertical I-piece into Column {deep_well} well to resolve vertical structure imbalances."
                else:
                    # Lay flat over the lowest columns
                    min_col = active_heights.index(min(active_heights))
                    target_col = min(min_col, 6) # Span 4 columns
                    target_rot = 0 # Horizontal
                    for c in range(target_col, target_col + 4):
                        active_heights[c] += 1
                    reason = f"Lay horizontal I-piece across Columns {target_col}-{target_col+3} to raise the floor evenly."

            elif piece == "O":
                # O-piece takes a 2x2 square. Place in lowest adjacent column pair.
                best_pair_col = 0
                min_sum = 999
                for col in range(9):
                    pair_sum = active_heights[col] + active_heights[col+1]
                    if pair_sum < min_sum:
                        min_sum = pair_sum
                        best_pair_col = col
                target_col = best_pair_col
                target_rot = 0
                active_heights[best_pair_col] += 2
                active_heights[best_pair_col+1] += 2
                reason = f"Place square O-piece flat across Column {best_pair_col} and {best_pair_col+1} to seal surface valleys."

            elif piece == "T":
                # T-piece is versatile. Excellent to fill small gaps.
                # Search for a 3-column span where center is lower: [H, H-1, H]
                t_spin_found = -1
                for col in range(1, 9):
                    if active_heights[col] < active_heights[col-1] and active_heights[col] < active_heights[col+1]:
                        t_spin_found = col
                        break
                        
                if t_spin_found != -1:
                    target_col = t_spin_found
                    target_rot = 2 # Upside down T
                    active_heights[t_spin_found-1] += 1
                    active_heights[t_spin_found] += 1
                    active_heights[t_spin_found+1] += 1
                    reason = f"T-slot identified. Insert T-piece upside-down centered on Column {t_spin_found}."
                else:
                    min_col = active_heights.index(min(active_heights))
                    target_col = max(1, min(min_col, 8))
                    target_rot = 0
                    active_heights[target_col-1] += 1
                    active_heights[target_col] += 2
                    active_heights[target_col+1] += 1
                    reason = f"Place flat T-piece over Column {target_col} to flatten adjacent surface profile."

            elif piece in {"S", "Z"}:
                # Place horizontal to span 3 columns
                min_col = active_heights.index(min(active_heights))
                target_col = max(1, min(min_col, 8))
                target_rot = 0
                active_heights[target_col-1] += 1
                active_heights[target_col] += 1
                active_heights[target_col+1] += 1
                reason = f"Place horizontal {piece}-piece over Column {target_col} to flat-build stack."

            else:  # L or J pieces
                # Place flat with vertical notch in lowest columns
                min_col = active_heights.index(min(active_heights))
                target_col = max(1, min(min_col, 8))
                target_rot = 0
                active_heights[target_col-1] += 1
                active_heights[target_col] += 1
                active_heights[target_col+1] += 2
                reason = f"Place flat {piece}-piece across Columns {target_col-1}-{target_col+1} with notch on the high column."

            blueprint.append({
                "queue_index": idx + 1,
                "piece": piece,
                "recommended_column": target_col,
                "recommended_rotation": target_rot,
                "placement_logic": reason
            })
            
        return blueprint
