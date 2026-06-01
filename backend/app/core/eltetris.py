from typing import List, Dict, Any

class ElTetrisEvaluator:
    """
    Core ElTetris Heuristic Board Evaluator.
    Adapted from pro-bot heuristics used in modern bot engines like ahmedrangel/tetrio-bot.
    Measures board health across aggregate height, bumpiness, row/column transitions, and deep wells.
    """

    @staticmethod
    def get_row_transitions(grid: List[List[int]]) -> int:
        """
        Count row transitions.
        A transition occurs when a cell is empty and its neighbor is filled (or vice versa).
        Include transitions from the board walls.
        """
        transitions = 0
        rows = len(grid)
        if rows == 0:
            return 0

        for r in range(rows):
            # Wall to first cell
            prev_cell = 1  # Wall is considered filled
            for c in range(10):
                cell = 1 if grid[r][c] != 0 else 0
                if cell != prev_cell:
                    transitions += 1
                prev_cell = cell
            # Last cell to right wall
            if prev_cell != 1:
                transitions += 1
                
        return transitions

    @staticmethod
    def get_column_transitions(grid: List[List[int]]) -> int:
        """
        Count column transitions.
        A transition occurs when a cell is empty and the cell above/below is filled.
        """
        transitions = 0
        rows = len(grid)
        if rows == 0:
            return 0

        for c in range(10):
            prev_cell = 1  # Floor is considered filled
            for r in range(rows):
                cell = 1 if grid[r][c] != 0 else 0
                if cell != prev_cell:
                    transitions += 1
                prev_cell = cell
            # Top cell to open skyline (skyline is considered empty)
            if prev_cell != 0:
                transitions += 1

        return transitions

    @staticmethod
    def get_wells(heights: List[int]) -> List[Dict[str, Any]]:
        """
        Identify wells. A well is a vertical column where adjacent columns are both higher.
        Returns: List of wells containing the column index and well depth.
        """
        wells = []
        for c in range(10):
            # Left wall check for column 0, right wall check for column 9
            left_h = heights[c+1] if c == 0 else heights[c-1]
            right_h = heights[c-1] if c == 9 else heights[c+1]
            
            # If current column is lower than both adjacent columns, it is a well
            if heights[c] < left_h and heights[c] < right_h:
                depth = min(left_h, right_h) - heights[c]
                wells.append({
                    "column": c,
                    "depth": depth
                })
        return wells

    @classmethod
    def evaluate_board(cls, grid: List[List[int]], heights: List[int], bumpiness: List[int], holes_count: int) -> Dict[str, Any]:
        """
        Calculate complete ElTetris board fitness using standard weights:
        - Aggregate Height Weight: -0.510066
        - Complete Lines Weight: +0.760666 (evaluated during placements, not state)
        - Holes Weight: -0.35663
        - Bumpiness Weight: -0.184483
        - Row Transitions Weight: -0.321788
        - Column Transitions Weight: -0.938121
        - Wells Weight: -0.12489
        """
        row_trans = cls.get_row_transitions(grid)
        col_trans = cls.get_column_transitions(grid)
        wells = cls.get_wells(heights)
        
        agg_height = sum(heights)
        wells_score = sum(w["depth"] for w in wells)

        # Standard linear evaluation weights
        score = (
            (agg_height * -0.51) +
            (holes_count * -0.35) +
            (sum(bumpiness) * -0.18) +
            (row_trans * -0.32) +
            (col_trans * -0.93) +
            (wells_score * -0.12)
        )
        
        # Normalize score to a 0-100 index for easier player reading
        # A completely clean empty board has 80 row transitions and 10 col transitions, scoring -34.9.
        # We offset by -34.9 to calibrate the 100.0 maximum.
        max_empty_score = -34.9
        rating = max(0.0, min(100.0, 100.0 + ((score - max_empty_score) / 1.5)))
        rating = float(round(rating, 1))

        # Diagnose structural bottlenecks
        diagnostics = []
        if col_trans > 18:
            diagnostics.append("High Column Transitions: Your stack columns have jagged filled/empty cell transitions. Focus on clean vertical flat-building to smooth transitions.")
        if wells_score > 4:
            deepest = max(wells, key=lambda w: w["depth"])
            diagnostics.append(f"Deep Well Obstruction: Column {deepest['column']} has a well depth of {deepest['depth']}. Avoid vertical canyons unless holding an I-piece.")
        if holes_count > 2:
            diagnostics.append("Hole Accumulation: Excess capped cells blocking downstacking. Prioritize line clearing over T-spin setup.")

        return {
            "eltetris_fitness_rating": rating,
            "aggregate_height": agg_height,
            "row_transitions": row_trans,
            "column_transitions": col_trans,
            "wells_count": len(wells),
            "wells": wells,
            "structural_bottlenecks": diagnostics,
            "verdict": (
                "Excellent structural profile."
                if not diagnostics else
                " / ".join(diagnostics)
            )
        }
