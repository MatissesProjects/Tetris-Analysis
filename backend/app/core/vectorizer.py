from typing import List, Dict, Any, Tuple

class BoardVectorizer:
    """
    Utility for vectorizing a 10x40 Tetris board playfield matrix into spatial features.
    
    The playfield matrix represents:
    - Width: 10 columns (x in 0..9)
    - Height: 40 rows (y in 0..39, where y=0 is the bottom row and y=39 is the top skyline row)
    - Matrix value: 0 for empty cell, 1 (or any positive integer) for a filled block.
    """

    @staticmethod
    def get_column_heights(grid: List[List[int]]) -> List[int]:
        """
        Calculate the height of each column.
        Height is 1-indexed (e.g. if row index 0 is filled, height is 1. If column is empty, height is 0).
        """
        heights = [0] * 10
        rows_count = len(grid)
        if rows_count == 0:
            return heights

        for col in range(10):
            # Scan from top row (y = rows_count - 1) down to bottom (y = 0)
            for row in range(rows_count - 1, -1, -1):
                if grid[row][col] != 0:
                    heights[col] = row + 1
                    break
        return heights

    @staticmethod
    def get_bumpiness_profile(heights: List[int]) -> List[int]:
        """
        Calculate the differences between adjacent column heights.
        Returns a list of 9 integers representing the surface profile.
        """
        return [heights[i + 1] - heights[i] for i in range(9)]

    @staticmethod
    def find_holes(grid: List[List[int]], heights: List[int]) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Detect empty cells ('holes') that have at least one filled block above them.
        Returns:
        - Total number of holes (int)
        - List of hole coordinates: [{'row': y, 'column': x}]
        """
        holes_count = 0
        hole_coordinates = []
        rows_count = len(grid)

        for col in range(10):
            top_block_row = heights[col] - 1  # 0-indexed top row index
            if top_block_row < 0:
                continue  # Empty column has no holes

            # Any 0 cell below top_block_row is a hole
            for row in range(top_block_row):
                if grid[row][col] == 0:
                    holes_count += 1
                    hole_coordinates.append({
                        "row": row,
                        "column": col,
                        "description": f"Column {col} downstack lane capped at row {row}"
                    })
        return holes_count, hole_coordinates

    @classmethod
    def vectorize_board(cls, grid: List[List[int]]) -> Dict[str, Any]:
        """
        Extract complete spatial vectorization profiles from a board grid.
        Returns a dictionary containing:
        - column_heights: list of 10 integers
        - bumpiness: list of 9 integers
        - holes_count: int
        - holes: list of coordinate dicts
        - feature_vector: list of 20 floats/ints representing [heights + bumpiness + [holes_count]]
        """
        # Assure standard height limits
        if not grid:
            grid = [[0] * 10 for _ in range(40)]

        heights = cls.get_column_heights(grid)
        bumpiness = cls.get_bumpiness_profile(heights)
        holes_count, holes = cls.find_holes(grid, heights)
        
        # Assemble standard 20D feature vector
        feature_vector = heights + bumpiness + [holes_count]
        
        return {
            "column_heights": heights,
            "bumpiness": bumpiness,
            "holes_count": holes_count,
            "holes": holes,
            "feature_vector": feature_vector
        }
