import os
import pytest
from backend.app.index.kdtree_index import KaggleGroundingIndex

def test_kdtree_initialization_and_cache():
    """Verify KDTree builds automatically and caches data successfully."""
    test_csv = "tests/mock_kaggle_index.csv"
    
    # Clean up previous runs if exist
    if os.path.exists(test_csv):
        os.remove(test_csv)
        
    try:
        # Initialize
        index = KaggleGroundingIndex(csv_path=test_csv)
        
        # Check standard generation rules
        assert len(index.raw_data) == 5000
        assert index.tree is not None
        assert index.feature_matrix.shape == (5000, 20)
        
        # Assert cache file was written
        assert os.path.exists(test_csv)
        
        # Test reloading works
        index2 = KaggleGroundingIndex(csv_path=test_csv)
        assert len(index2.raw_data) == 5000
        assert index2.tree is not None
        
    finally:
        # Clean up
        if os.path.exists(test_csv):
            os.remove(test_csv)


def test_nearest_neighbor_query():
    """Verify that querying the KDTree returns realistic and well-structured Grandmaster match details."""
    test_csv = "tests/mock_kaggle_index.csv"
    
    try:
        index = KaggleGroundingIndex(csv_path=test_csv)
        
        # Query with an empty playfield
        grid = [[0] * 10 for _ in range(40)]
        result = index.query_nearest_grandmaster(grid)
        
        assert "query_profile" in result
        assert "nearest_match" in result
        
        match = result["nearest_match"]
        assert "distance" in match
        assert "match_source" in match
        assert "grandmaster_action" in match
        assert "category" in match
        
        assert isinstance(match["distance"], float)
        assert isinstance(match["grandmaster_action"], str)
        assert len(match["grandmaster_action"]) > 0
        
    finally:
        if os.path.exists(test_csv):
            os.remove(test_csv)
