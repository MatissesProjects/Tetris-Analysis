import json
from typing import Dict, Any, List, Optional
from app.core.rng import PieceGenerator

class TTRParser:
    """
    Resilient parser for TETR.IO solo (.ttr) and multiplayer (.ttrm) replay files.
    """

    @staticmethod
    def extract_seed(data: Dict[str, Any]) -> Optional[int]:
        """
        Traverse the JSON dictionary to find the seed.
        TETR.IO stores this in various paths depending on the game mode and version.
        """
        # Common paths for the seed
        paths = [
            ("data", "game", "seed"),
            ("data", "opts", "seed"),
            ("data", "seed"),
            ("game", "seed"),
            ("opts", "seed"),
            ("replay", "options", "seed"),
            ("replay", "options", "seed_random"),
            ("seed",),
        ]
        
        for path in paths:
            curr = data
            for key in path:
                if isinstance(curr, dict) and key in curr:
                    curr = curr[key]
                elif isinstance(curr, list) and len(curr) > 0 and isinstance(curr[0], dict) and key in curr[0]:
                    curr = curr[0][key]
                else:
                    curr = None
                    break
            if curr is not None and isinstance(curr, (int, float)):
                return int(curr)
                
        # If we have a list of replays, inspect the first one
        if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
            sub_data = data["data"][0]
            # Try recursive search in first game session
            return TTRParser.extract_seed(sub_data)
            
        return None

    @staticmethod
    def extract_events(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract the events array from the JSON tree.
        These are typically keydown/keyup keypress actions.
        """
        # Common paths to look for events
        paths = [
            ("data", "events"),
            ("events",),
            ("replay", "events"),
        ]
        
        for path in paths:
            curr = data
            for key in path:
                if isinstance(curr, dict) and key in curr:
                    curr = curr[key]
                else:
                    curr = None
                    break
            if isinstance(curr, list):
                return curr

        # Check in data.replays[0].events
        if "data" in data and isinstance(data["data"], dict):
            replays = data["data"].get("replays")
            if isinstance(replays, list) and len(replays) > 0:
                events = replays[0].get("events")
                if isinstance(events, list):
                    return events

        # Check inside multiplayer array data
        if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
            for item in data["data"]:
                if isinstance(item, dict):
                    # Check replays in player data
                    replays = item.get("replays")
                    if isinstance(replays, list) and len(replays) > 0:
                        events = replays[0].get("events")
                        if isinstance(events, list):
                            return events
                    # Check direct events
                    events = item.get("events")
                    if isinstance(events, list):
                        return events

        return []

    @staticmethod
    def extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract usernames and key gameplay metrics if present."""
        metadata = {}
        
        # User details
        user = data.get("user", {})
        if not user and "data" in data:
            if isinstance(data["data"], dict):
                user = data["data"].get("user", {})
            elif isinstance(data["data"], list) and len(data["data"]) > 0:
                user = data["data"][0].get("user", {})
                
        if isinstance(user, dict) and user:
            metadata["username"] = user.get("username", "Unknown Player")
        else:
            # Fallback to root level "users" list (e.g. from zenith replays)
            users = data.get("users", [])
            if isinstance(users, list) and len(users) > 0 and isinstance(users[0], dict):
                metadata["username"] = users[0].get("username", "Unknown Player")
            else:
                metadata["username"] = "Unknown Player"
            
        # Try to extract general match statistics
        stats = {}
        target_stats = ["score", "lines", "pieces", "pps", "apm", "time", "vsscore", "vs"]
        
        # Look in root or data.stats
        stats_source = data.get("stats", {})
        if not stats_source and "data" in data:
            if isinstance(data["data"], dict):
                stats_source = data["data"].get("stats", {})
            elif isinstance(data["data"], list) and len(data["data"]) > 0:
                stats_source = data["data"][0].get("stats", {})
                
        if isinstance(stats_source, dict):
            for k in target_stats:
                if k in stats_source:
                    stats[k] = stats_source[k]
            if "vs" in stats and "vsscore" not in stats:
                stats["vsscore"] = stats["vs"]

        # Look in replay.results.stats or replay.results.aggregatestats
        replay = data.get("replay", {})
        if isinstance(replay, dict):
            results = replay.get("results", {})
            if isinstance(results, dict):
                r_stats = results.get("stats", {})
                agg_stats = results.get("aggregatestats", {})
                if isinstance(r_stats, dict):
                    if "score" in r_stats:
                        stats["score"] = r_stats["score"]
                    if "lines" in r_stats:
                        stats["lines"] = r_stats["lines"]
                    if "piecesplaced" in r_stats:
                        stats["pieces"] = r_stats["piecesplaced"]
                    if "finesse" in r_stats and isinstance(r_stats["finesse"], dict):
                        stats["finesse_faults"] = r_stats["finesse"].get("faults")
                        stats["finesse_perfect_pieces"] = r_stats["finesse"].get("perfectpieces")
                    if "vsscore" in r_stats:
                        stats["vsscore"] = r_stats["vsscore"]
                    elif "vs" in r_stats:
                        stats["vsscore"] = r_stats["vs"]
                    if "clears" in r_stats:
                        stats["clears"] = r_stats["clears"]
                    if "topcombo" in r_stats:
                        stats["topcombo"] = r_stats["topcombo"]
                    elif "combo" in r_stats:
                        stats["topcombo"] = r_stats["combo"]
                    if "topbtb" in r_stats:
                        stats["topbtb"] = r_stats["topbtb"]
                    elif "btb" in r_stats:
                        stats["topbtb"] = r_stats["btb"]
                    if "tspins" in r_stats:
                        stats["tspins"] = r_stats["tspins"]
                if isinstance(agg_stats, dict):
                    if "pps" in agg_stats:
                        stats["pps"] = agg_stats["pps"]
                    if "apm" in agg_stats:
                        stats["apm"] = agg_stats["apm"]
                    if "vsscore" in agg_stats:
                        stats["vsscore"] = agg_stats["vsscore"]
                    elif "vs" in agg_stats:
                        stats["vsscore"] = agg_stats["vs"]
                    
        metadata["stats"] = stats
        return metadata

    @classmethod
    def parse_replay(cls, replay_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses a full replay JSON structure and returns:
        - seed
        - metadata
        - events (timeline inputs)
        - projected_queue (first 100 deterministic pieces)
        """
        seed = cls.extract_seed(replay_json)
        events = cls.extract_events(replay_json)
        metadata = cls.extract_metadata(replay_json)
        
        projected_queue = []
        if seed is not None:
            generator = PieceGenerator(seed)
            projected_queue = [generator.next_piece() for _ in range(100)]
            
        return {
            "seed": seed,
            "metadata": metadata,
            "events_count": len(events),
            "events": events,
            "projected_queue": projected_queue
        }
