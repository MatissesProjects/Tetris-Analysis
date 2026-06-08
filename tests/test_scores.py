import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import init_db, clear_scores, get_scores

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Make sure DB is initialized and clear before each test
    init_db()
    clear_scores()
    yield
    clear_scores()

def test_scores_crud():
    # 1. Fetch initial scores (should be empty)
    response = client.get("/api/v1/scores")
    assert response.status_code == 200
    assert response.json() == []

    # 2. Add a score
    score_data = {
        "username": "Matisse",
        "score": 500000,
        "pps": 2.5,
        "apm": 45.0,
        "finesse_faults": 10,
        "finesse_rate": 0.92,
        "pieces_placed": 250,
        "lines_cleared": 100,
        "replay_name": "match_1.ttr",
        "vsscore": 95.0,
        "topcombo": 5,
        "topbtb": 4,
        "tspins": 8,
        "quads": 12,
        "clears_json": '{"singles":2,"quads":12}'
    }
    response = client.post("/api/v1/scores", json=score_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    score_id = response.json()["id"]

    # 3. Retrieve scores again
    response = client.get("/api/v1/scores")
    assert response.status_code == 200
    scores = response.json()
    assert len(scores) == 1
    assert scores[0]["username"] == "Matisse"
    assert scores[0]["score"] == 500000
    assert scores[0]["vsscore"] == 95.0
    assert scores[0]["topcombo"] == 5
    assert scores[0]["topbtb"] == 4
    assert scores[0]["tspins"] == 8
    assert scores[0]["quads"] == 12
    assert scores[0]["clears_json"] == '{"singles":2,"quads":12}'
    assert scores[0]["id"] == score_id

    # 4. Delete the score
    response = client.delete(f"/api/v1/scores/{score_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 5. Check empty again
    response = client.get("/api/v1/scores")
    assert len(response.json()) == 0

def test_clear_scores():
    # Insert multiple scores
    for i in range(3):
        score_data = {
            "username": f"Player_{i}",
            "score": 100000 * (i + 1),
            "pps": 1.5 + (0.2 * i),
            "apm": 20.0 + (5 * i),
            "finesse_faults": 5,
            "finesse_rate": 0.95,
            "pieces_placed": 120,
            "lines_cleared": 40,
            "replay_name": f"game_{i}.ttr"
        }
        client.post("/api/v1/scores", json=score_data)
        
    response = client.get("/api/v1/scores")
    assert len(response.json()) == 3
    
    # Clear all
    response = client.delete("/api/v1/scores/clear")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    response = client.get("/api/v1/scores")
    assert len(response.json()) == 0


def test_chat_coaching_endpoint():
    # Test chatting with current stats
    chat_payload = {
        "message": "Should I focus on speed?",
        "history": [],
        "current_stats": {
            "pps": 1.2,
            "finesse_faults": 15,
            "pieces_placed": 100,
            "score": 10000
        }
    }
    response = client.post("/api/v1/chat", json=chat_payload)
    assert response.status_code == 200
    json_data = response.json()
    assert "advice" in json_data
    assert "source" in json_data


def test_get_single_score():
    # 1. Add a score
    score_data = {
        "username": "Matisse",
        "score": 500000,
        "pps": 2.5,
        "apm": 45.0,
        "finesse_faults": 10,
        "finesse_rate": 0.92,
        "pieces_placed": 250,
        "lines_cleared": 100,
        "replay_name": "match_1.ttr",
        "vsscore": 95.0,
        "topcombo": 5,
        "topbtb": 4,
        "tspins": 8,
        "quads": 12,
        "clears_json": '{"singles":2,"quads":12}'
    }
    post_res = client.post("/api/v1/scores", json=score_data)
    assert post_res.status_code == 200
    score_id = post_res.json()["id"]

    # 2. Get the single score (no file in Downloads, should use DB fallback)
    get_res = client.get(f"/api/v1/scores/{score_id}")
    assert get_res.status_code == 200
    res_data = get_res.json()
    
    assert res_data["score_id"] == score_id
    assert res_data["metadata"]["username"] == "Matisse"
    assert res_data["extracted_stats"]["score"] == 500000
    assert res_data["extracted_stats"]["vsscore"] == 95.0
    assert res_data["extracted_stats"]["clears"] == {"singles": 2, "quads": 12}
    assert "suggestions" in res_data
    assert len(res_data["suggestions"]) > 0

    # 3. Write a mock replay file to Downloads to test dynamic parsing path
    import os
    import json
    downloads_dir = os.path.expanduser("~/Downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    temp_file_path = os.path.join(downloads_dir, "match_1.ttr")
    
    mock_replay_content = {
        "data": {
            "user": {
                "username": "MatisseDynamic"
            },
            "stats": {
                "score": 125000,
                "pps": 2.1,
                "apm": 32.5,
                "lines": 40
            },
            "game": {
                "seed": 12345
            },
            "events": [
                {"frame": 10, "type": "keydown", "data": {"key": "moveLeft", "subframe": 0.2}},
                {"frame": 12, "type": "keyup", "data": {"key": "moveLeft", "subframe": 0.8}},
                {"frame": 20, "type": "keydown", "data": {"key": "hardDrop", "subframe": 0.0}}
            ]
        }
    }
    
    try:
        with open(temp_file_path, "w", encoding="utf-8") as f:
            json.dump(mock_replay_content, f)
            
        # 4. Fetch the score again (should parse file dynamically)
        get_dynamic_res = client.get(f"/api/v1/scores/{score_id}")
        assert get_dynamic_res.status_code == 200
        dynamic_data = get_dynamic_res.json()
        
        assert dynamic_data["score_id"] == score_id
        assert dynamic_data["metadata"]["username"] == "MatisseDynamic"
        assert dynamic_data["extracted_stats"]["score"] == 125000
        assert dynamic_data["extracted_stats"]["pps"] == 2.1
        assert dynamic_data["extracted_stats"]["apm"] == 32.5
        
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    # 5. Request a non-existent score ID
    failed_res = client.get("/api/v1/scores/99999")
    assert failed_res.status_code == 404
