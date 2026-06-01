import pytest
from backend.app.core.vectorizer import BoardVectorizer

def test_empty_board_vectorization():
    """Verify that a clean empty board yields zeroed spatial vectors."""
    # 10 columns by 40 rows all empty
    grid = [[0] * 10 for _ in range(40)]
    
    profile = BoardVectorizer.vectorize_board(grid)
    
    assert profile["column_heights"] == [0] * 10
    assert profile["bumpiness"] == [0] * 9
    assert profile["holes_count"] == 0
    assert profile["holes"] == []
    
    # 20D feature vector should be all zeros
    assert len(profile["feature_vector"]) == 20
    assert profile["feature_vector"] == [0] * 20


def test_heights_and_bumpiness():
    """Verify heights are correctly extracted and bumpiness profile maps perfectly."""
    grid = [[0] * 10 for _ in range(40)]
    
    # Set heights:
    # Column 0: height 3
    grid[0][0] = 1
    grid[1][0] = 1
    grid[2][0] = 1
    
    # Column 1: height 1
    grid[0][1] = 1
    
    # Column 5: height 5
    grid[0][5] = 1
    grid[1][5] = 1
    grid[2][5] = 1
    grid[3][5] = 1
    grid[4][5] = 1
    
    heights = BoardVectorizer.get_column_heights(grid)
    assert heights[0] == 3
    assert heights[1] == 1
    assert heights[2] == 0
    assert heights[5] == 5
    assert heights[9] == 0
    
    # Bumpiness profile [h1 - h0, h2 - h1, ...]
    bumpiness = BoardVectorizer.get_bumpiness_profile(heights)
    # heights: [3, 1, 0, 0, 0, 5, 0, 0, 0, 0]
    # diffs: [1-3, 0-1, 0-0, 0-0, 5-0, 0-5, 0-0, 0-0, 0-0] -> [-2, -1, 0, 0, 5, -5, 0, 0, 0]
    assert bumpiness == [-2, -1, 0, 0, 5, -5, 0, 0, 0]


def test_holes_detection():
    """Verify that capped empty cells are correctly registered as holes."""
    grid = [[0] * 10 for _ in range(40)]
    
    # Column 3 has top block at row index 3 (height 4)
    grid[0][3] = 1
    grid[1][3] = 0  # Hole!
    grid[2][3] = 1
    grid[3][3] = 1
    
    # Column 7 has top block at row index 1 (height 2)
    grid[0][7] = 0  # Hole!
    grid[1][7] = 1
    
    heights = BoardVectorizer.get_column_heights(grid)
    holes_count, holes = BoardVectorizer.find_holes(grid, heights)
    
    assert holes_count == 2
    # Verify hole coordinates
    cols = {hole["column"] for hole in holes}
    rows = {hole["row"] for hole in holes}
    assert cols == {3, 7}
    assert rows == {0, 1}
