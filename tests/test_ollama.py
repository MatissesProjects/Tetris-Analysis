import pytest
from unittest.mock import patch, MagicMock
from backend.app.core.ollama_client import OllamaClient

def test_prompt_compilation():
    """Verify that playfield details and Grandmaster anchors map correctly into spatial prompts."""
    client = OllamaClient()
    
    heights = [3, 2, 0, 0, 0, 0, 0, 0, 0, 0]
    bumpiness = [-1, -2, 0, 0, 0, 0, 0, 0, 0]
    holes = [{"row": 0, "column": 1}]
    anchor = {
        "match_source": "Kaggle Match #999",
        "category": "T-spin setup",
        "grandmaster_action": "Czsmall: Executed soft-drop vertical T-spin"
    }
    
    prompt = client.compile_spatial_prompt(
        heights=heights,
        bumpiness=bumpiness,
        holes_count=1,
        holes=holes,
        active_piece="T",
        queue=["I", "O", "S", "Z", "L"],
        grandmaster_anchor=anchor
    )
    
    # Assert features exist inside compiled prompt text
    assert "[ACTIVE BOARD SPACIAL PROFILE]" in prompt
    assert "[EMPIRICAL GRANDMASTER ANCHOR MATCH]" in prompt
    assert "Row 0 Column 1 is capped" in prompt
    assert "Czsmall: Executed soft-drop vertical T-spin" in prompt
    assert "T-spin setup" in prompt
    assert "I, O, S, Z, L" in prompt


def test_rule_based_fallback_danger():
    """Verify heights danger yields skyline panic coaching instructions."""
    client = OllamaClient()
    
    heights = [15, 14, 12, 10, 8, 6, 4, 2, 0, 0] # Height 15!
    holes = []
    anchor = {"grandmaster_action": "Czsmall: Clear flat"}
    
    advice = client._generate_rule_based_fallback(
        heights=heights,
        holes_count=0,
        holes=holes,
        active_piece="J",
        grandmaster_anchor=anchor
    )
    
    assert "CRITICAL BOARD DANGER" in advice
    assert "skyline" in advice
    assert "J" in advice


def test_rule_based_fallback_holes():
    """Verify holes yields cap-lane downstack clearing warnings."""
    client = OllamaClient()
    
    heights = [3, 3, 3, 0, 0, 0, 0, 0, 0, 0]
    holes = [{"row": 0, "column": 2}]
    anchor = {"grandmaster_action": "Czsmall: downstack priorities"}
    
    advice = client._generate_rule_based_fallback(
        heights=heights,
        holes_count=1,
        holes=holes,
        active_piece="I",
        grandmaster_anchor=anchor
    )
    
    assert "DOWNSTACK OBSTRUCTION" in advice
    assert "Column 2" in advice
    assert "downstack priorities" in advice


@patch("requests.post")
def test_ollama_http_success(mock_post):
    """Verify standard response when Ollama client successfully responds."""
    # Mock HTTP response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "Gemma advice: Setup vertical T-spin."}
    mock_post.return_value = mock_resp
    
    client = OllamaClient()
    result = client.query_spatial_advice(
        heights=[0]*10,
        bumpiness=[0]*9,
        holes_count=0,
        holes=[],
        active_piece="I",
        queue=["Z"],
        grandmaster_anchor={}
    )
    
    assert result["advice"] == "Gemma advice: Setup vertical T-spin."
    assert "Local Ollama" in result["source"]


@patch("requests.post")
def test_ollama_http_timeout_fallback(mock_post):
    """Verify client triggers resilient spatial fallbacks when HTTP request times out."""
    # Simulate HTTP connection failure
    mock_post.side_effect = Exception("Connection timed out")
    
    client = OllamaClient()
    result = client.query_spatial_advice(
        heights=[0]*10,
        bumpiness=[0]*9,
        holes_count=0,
        holes=[],
        active_piece="I",
        queue=["Z"],
        grandmaster_anchor={}
    )
    
    # Assert fallback is fully operational
    assert "OPTIMAL SURFACE TOPOLOGY" in result["advice"]
    assert "Fallback" in result["source"]
