from typing import List, Dict, Any

class OpeningMatcher:
    """
    Classic Tournament Opening Pattern Matcher.
    Recognizes classic opening sequences listed on the TETR.IO Wiki 
    based on the landing columns of the first bag (first 6 piece placements).
    """

    # Target column mappings for standard classic openings (column list for first 5 pieces)
    OPENING_PATTERNS = {
        "TKI 3 (Flat Top)": {
            "cols": [0, 8, 3, 5, 2],
            "pieces": ["J", "L", "I", "S", "Z"],
            "desc": "TKI 3 (Flat Top variation): A highly reliable, flexible opening that sets up an immediate Column 3 T-spin slot."
        },
        "DT Cannon": {
            "cols": [0, 1, 8, 9, 3],
            "pieces": ["J", "L", "Z", "S", "O"],
            "desc": "DT Cannon: A powerful opening that constructs a nested T-Spin Double and T-Spin Triple combo, sending 10 lines of garbage."
        },
        "MKO Stacking": {
            "cols": [0, 7, 2, 4, 8],
            "pieces": ["I", "O", "J", "L", "T"],
            "desc": "MKO Stacking: An aggressive flat-stacking setup designed to maintain active Back-to-Back structures."
        }
    }

    @classmethod
    def match_opening(
        cls,
        pieces_placed: List[str],
        columns_placed: List[int]
    ) -> Dict[str, Any]:
        """
        Match first bag placement logs against classic TETR.IO openings.
        
        pieces_placed: List of tetromino symbols in order of placement
        columns_placed: List of landing columns in order of placement
        """
        if len(pieces_placed) < 4 or len(columns_placed) < 4:
            return {
                "opening_recognized": False,
                "matched_name": "Generic Open Stacking",
                "matching_percentage": 0.0,
                "coaching_tip": "Place at least 5 pieces to allow Aegis to analyze your opening pattern book."
            }

        # Check subsegment matching
        best_match = "Generic Stacking"
        best_score = 0.0
        best_desc = "Standard open board stack."
        
        for name, pattern in cls.OPENING_PATTERNS.items():
            match_hits = 0
            p_len = min(len(pieces_placed), len(pattern["cols"]))
            
            for i in range(p_len):
                # Check if piece type and target landing column aligns
                if pieces_placed[i] == pattern["pieces"][i] and columns_placed[i] == pattern["cols"][i]:
                    match_hits += 1
            
            score = (match_hits / len(pattern["cols"])) * 100.0
            if score > best_score:
                best_score = score
                best_match = name
                best_desc = pattern["desc"]

        recognized = best_score >= 60.0 # Match at least 3 out of 5 pieces aligned
        
        if recognized:
            tip = (
                f"Opening Match Confirmed: {best_match} ({int(best_score)}% alignment). "
                f"{best_desc} Focus on perfect finesse to execute the remainder of the bag."
            )
        else:
            tip = "Generic Open Stacking detected. To secure early game advantage, practice standard TKI 3 or DT Cannon opening configurations."
            
        return {
            "opening_recognized": recognized,
            "matched_name": best_match if recognized else "Generic Open Stacking",
            "matching_percentage": round(best_score, 1),
            "coaching_tip": tip
        }
