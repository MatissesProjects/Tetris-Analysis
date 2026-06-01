import requests
from typing import List, Dict, Any, Optional

class OllamaClient:
    """
    Client for querying local Ollama instance running gemma:26b.
    Prepares advanced spatial prompt layouts and handles query fail-overs gracefully.
    """
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma:26b"):
        self.base_url = base_url
        self.model = model
        self.generate_url = f"{base_url}/api/generate"

    def compile_spatial_prompt(
        self,
        heights: List[int],
        bumpiness: List[int],
        holes_count: int,
        holes: List[Dict[str, Any]],
        active_piece: str,
        queue: List[str],
        grandmaster_anchor: Dict[str, Any]
    ) -> str:
        """
        Synthesize playfield vector metrics and closest KDTree Grandmaster matched play into a single prompt.
        """
        holes_description = "None"
        if holes:
            holes_description = "; ".join([
                f"Row {h['row']} Column {h['column']} is capped"
                for h in holes
            ])
            
        return f"""You are Aegis, an elite esports Tetris tactical spotter coach.
Analyze the spatial metrics of the playfield and the upcoming piece queue to deliver frame-perfect coaching.

[ACTIVE BOARD SPACIAL PROFILE]
- Column heights (10 columns): {heights}
- Surface bumpiness profile (column height differences): {bumpiness}
- Capped downstack holes count: {holes_count}
- Capped downstack holes coordinates: {holes_description}
- Active Held Piece: {active_piece}
- Next Piece Queue: {", ".join(queue[:5])}

[EMPIRICAL GRANDMASTER ANCHOR MATCH]
Our local SciPy KDTree matched this topology against a battle-tested professional play:
- Match source: {grandmaster_anchor.get('match_source', 'Unknown Match')}
- Pro Action Category: {grandmaster_anchor.get('category', 'General build')}
- Matched Grandmaster Action: {grandmaster_anchor.get('grandmaster_action', 'None')}

[INSTRUCTIONS]
Deliver exactly two concise, analytical, and actionable coaching sentences.
Instruct the player exactly how to placement-orient their active piece and queue, and warn them if they are about to cap a hole or spike their skyline heights. Do not include introductory phrases. Keep it strictly focused and esports-professional.
"""

    def query_spatial_advice(
        self,
        heights: List[int],
        bumpiness: List[int],
        holes_count: int,
        holes: List[Dict[str, Any]],
        active_piece: str,
        queue: List[str],
        grandmaster_anchor: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Query Ollama with a compiled prompt.
        If Ollama is offline or times out, automatically trigger the high-quality rule-based fallback.
        """
        prompt = self.compile_spatial_prompt(
            heights=heights,
            bumpiness=bumpiness,
            holes_count=holes_count,
            holes=holes,
            active_piece=active_piece,
            queue=queue,
            grandmaster_anchor=grandmaster_anchor
        )
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_k": 20
            }
        }
        
        try:
            # Query Ollama with a tight 3.0s timeout to maintain high frontend responsiveness
            response = requests.post(self.generate_url, json=payload, timeout=3.0)
            if response.status_code == 200:
                result = response.json()
                advice = result.get("response", "").strip()
                if advice:
                    return {
                        "advice": advice,
                        "source": f"Local Ollama ({self.model})",
                        "prompt_length": len(prompt)
                    }
        except Exception as e:
            # Silence connection warnings and log in result dict
            print(f"Ollama offline/connection error: {e}. Activating high-fidelity fallback...")

        # Trigger high-fidelity local rule-based spatial advisor fallback
        fallback_advice = self._generate_rule_based_fallback(
            heights=heights,
            holes_count=holes_count,
            holes=holes,
            active_piece=active_piece,
            grandmaster_anchor=grandmaster_anchor
        )

        return {
            "advice": fallback_advice,
            "source": "Aegis Rule-Based Local Fallback (KDTree Anchored)",
            "prompt_length": len(prompt)
        }

    def _generate_rule_based_fallback(
        self,
        heights: List[int],
        holes_count: int,
        holes: List[Dict[str, Any]],
        active_piece: str,
        grandmaster_anchor: Dict[str, Any]
    ) -> str:
        """
        Deterministic, highly professional rule-based spatial diagnostic generator.
        Combines spatial metrics and the matched Grandmaster action.
        """
        max_h = max(heights) if heights else 0
        gm_action = grandmaster_anchor.get('grandmaster_action', '')
        
        # Strip name from GM action if present to make advice look integrated
        if ":" in gm_action:
            gm_action = gm_action.split(":", 1)[1].strip()

        if max_h >= 14:
            return f"CRITICAL BOARD DANGER: Heights have crested at row {max_h}. Prioritize downstack lane safety and immediately swap to {active_piece} to clear lines and flatten your playfield skyline."
        elif holes_count > 0:
            first_hole = holes[0]
            col = first_hole["column"]
            return f"DOWNSTACK OBSTRUCTION: Capped hole detected in Column {col}. Follow the Grandmaster matched play to prioritize clearing capped rows over setting up T-spins: {gm_action}."
        else:
            return f"OPTIMAL SURFACE TOPOLOGY: Your playfield skyline is flat and stable. Maintain aggressive Back-to-Back status, and coordinate your upcoming pieces to execute clean wells."

# Singleton instance
ollama_client = OllamaClient()
