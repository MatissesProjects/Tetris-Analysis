from fastapi.testclient import TestClient
from app.main import app

def test_websocket_telemetry():
    """Verify WebSocket connection accepts telemetry events and responds with flashing commands."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/telemetry") as websocket:
        # Piece 1: 1 moveLeft, 1 hardDrop
        websocket.send_json({"frame": 6, "type": "keydown", "data": {"key": "moveLeft", "subframe": 0.0}})
        websocket.send_json({"frame": 18, "type": "keydown", "data": {"key": "hardDrop", "subframe": 0.0}})

        # Piece 2: 1 rotateCW, 1 hardDrop
        websocket.send_json({"frame": 27, "type": "keydown", "data": {"key": "rotateCW", "subframe": 0.0}})
        websocket.send_json({"frame": 48, "type": "keydown", "data": {"key": "hardDrop", "subframe": 0.0}})

        # Piece 3: 1 moveRight, 1 hardDrop (reaches count 3, which triggers unmask flash)
        websocket.send_json({"frame": 54, "type": "keydown", "data": {"key": "moveRight", "subframe": 0.0}})
        websocket.send_json({"frame": 66, "type": "keydown", "data": {"key": "hardDrop", "subframe": 0.0}})

        # We should receive the unmask flash instruction
        response = websocket.receive_json()
        assert response["action"] == "flash_unmask"


def test_websocket_double_rotation_intervention():
    """Verify that double 90° rotations on multiple pieces trigger a tactical intervention message."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/telemetry") as websocket:
        # We need pieces_placed >= 10 to evaluate double rotations triggers or general stats.
        # But wait: rule 10 check for suggestions runs on the stats returned by parse_events_for_stats.
        # Let's send 2 pieces with double rotations, and let's send 8 standard pieces to reach 10 pieces.
        # Piece 1 (double rotation): 2 rotateCW, 1 hardDrop
        websocket.send_json({"frame": 10, "type": "keydown", "data": {"key": "rotateCW", "subframe": 0.0}})
        websocket.send_json({"frame": 12, "type": "keydown", "data": {"key": "rotateCW", "subframe": 0.0}})
        websocket.send_json({"frame": 15, "type": "keydown", "data": {"key": "hardDrop", "subframe": 0.0}})

        # Piece 2 (double rotation): 2 rotateCCW, 1 hardDrop
        websocket.send_json({"frame": 20, "type": "keydown", "data": {"key": "rotateCCW", "subframe": 0.0}})
        websocket.send_json({"frame": 22, "type": "keydown", "data": {"key": "rotateCCW", "subframe": 0.0}})
        websocket.send_json({"frame": 25, "type": "keydown", "data": {"key": "hardDrop", "subframe": 0.0}})

        # Pieces 3-10: standard placements
        for i in range(3, 11):
            frame_offset = i * 10
            websocket.send_json({"frame": frame_offset, "type": "keydown", "data": {"key": "moveLeft", "subframe": 0.0}})
            websocket.send_json({"frame": frame_offset + 5, "type": "keydown", "data": {"key": "hardDrop", "subframe": 0.0}})

        # We should get a flash_unmask (since 10 pieces were placed, 9th piece sent one, etc. but let's check for intervention)
        # The websocket loops over all received messages. Since we sent 10 hardDrops:
        # On the 10th hardDrop, double_rotations = 2, and pieces_placed = 10, triggering the intervention.
        # Depending on message ordering, we might receive some flash_unmask messages first. Let's read until we get the intervention.
        received_intervention = False
        for _ in range(5):  # Read up to 5 messages
            try:
                msg = websocket.receive_json()
                if msg.get("action") == "intervention":
                    assert "Finesse alert" in msg.get("message")
                    received_intervention = True
                    break
            except Exception:
                break
        assert received_intervention is True
