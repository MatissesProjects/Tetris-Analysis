import requests
from typing import List, Dict, Any, Optional

class OllamaClient:
    """
    Client for querying local Ollama instance running gemma:26b.
    Prepares advanced spatial prompt layouts and handles query fail-overs gracefully.
    """
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma:26b"):
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
        self.model = self._detect_best_model(default_model=model)

    def _detect_best_model(self, default_model: str) -> str:
        try:
            tags_url = f"{self.base_url}/api/tags"
            response = requests.get(tags_url, timeout=2.0)
            if response.status_code == 200:
                available_models = [m.get("name") for m in response.json().get("models", [])]
                
                # Check preferred list of models in order of capability/preference
                preferred = [
                    "gemma4:26b",
                    "gemma4:26b-a4b-it-q4_K_M",
                    default_model,
                    "gemma4:latest",
                    "gemma4:e4b",
                    "gemma3:4b",
                    "qwen3:8b"
                ]
                for p_model in preferred:
                    if p_model in available_models:
                        print(f"OllamaClient: detected and selected model '{p_model}'")
                        return p_model
                
                # Fallback to the first available model if none of preferred models match
                if available_models:
                    print(f"OllamaClient: fallback to first available model '{available_models[0]}'")
                    return available_models[0]
        except Exception as e:
            print(f"OllamaClient: failed to detect local models (Ollama offline/connection error: {e})")
        
        return default_model

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

    def query_chat_coaching(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        current_stats: Optional[Dict[str, Any]] = None,
        all_scores: Optional[List[Dict[str, Any]]] = None,
        suggestions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Query Ollama with user's stats, history, and suggestions as prompt context.
        Falls back to rule-based responses if Ollama is offline or times out.
        """
        all_scores = all_scores or []
        suggestions = suggestions or []
        
        total_runs = len(all_scores)
        max_score = max([s.get("score", 0) for s in all_scores]) if all_scores else 0
        avg_pps = sum([s.get("pps", 0.0) for s in all_scores]) / total_runs if total_runs else 0.0
        avg_apm = sum([s.get("apm", 0.0) for s in all_scores]) / total_runs if total_runs else 0.0
        avg_vsscore = sum([s.get("vsscore", 0.0) for s in all_scores]) / total_runs if total_runs else 0.0
        avg_finesse = sum([s.get("finesse_rate", 1.0) for s in all_scores]) / total_runs if total_runs else 1.0

        suggestions_summary = "None"
        if suggestions:
            suggestions_summary = "\n".join([
                f"- Priority #{s['priority']}: {s['training_id'].replace('_', ' ').title()} - {s['reason']}"
                for s in suggestions
            ])
            
        current_run_summary = "No active run loaded."
        if current_stats:
            current_run_summary = f"""- Score: {current_stats.get('score', 0):,}
- PPS: {current_stats.get('pps', 0.0):.2f}
- APM: {current_stats.get('apm', 0.0):.2f}
- Finesse Rate: {current_stats.get('finesse_rate', 1.0)*100:.1f}% ({current_stats.get('finesse_faults', 0)} faults)
- Lines Cleared: {current_stats.get('lines_cleared', 0) or current_stats.get('lines', 0)}"""

        system_prompt = f"""You are Aegis, an elite esports Tetris tactical coach and sports psychologist.
The player is chatting with you about their performance statistics and recommended trainings.

[PLAYER PROFILE & HISTORICAL STATISTICS]
- Total recorded sessions: {total_runs}
- Personal Best Score: {max_score:,}
- Average speed (PPS): {avg_pps:.2f}
- Average offense (APM): {avg_apm:.2f}
- Average VS Score: {avg_vsscore:.2f}
- Average finesse rate: {avg_finesse*100:.1f}%

[CURRENT REPLAY ANALYSIS]
{current_run_summary}

[CURRENT TRAINING RECOMMENDATIONS]
{suggestions_summary}

[INSTRUCTIONS]
Provide a highly professional, encouraging, and esports-focused coaching response to the player's message.
Keep your response concise (usually 1-3 sentences or a short bulleted tip) and extremely action-oriented. Do not mention system coordinates or internal prompt headers. Talk directly to the player.
"""

        # Build prompt with history
        prompt_parts = [system_prompt, "\n[CHAT HISTORY]"]
        for msg in history:
            role = "Player" if msg.get("role") == "user" else "Aegis"
            prompt_parts.append(f"{role}: {msg.get('content')}")
        
        prompt_parts.append(f"Player: {user_message}")
        prompt_parts.append("Aegis:")
        
        prompt = "\n".join(prompt_parts)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.5,
                "top_k": 20
            }
        }
        
        try:
            response = requests.post(self.generate_url, json=payload, timeout=4.0)
            if response.status_code == 200:
                result = response.json()
                advice = result.get("response", "").strip()
                if advice:
                    return {
                        "advice": advice,
                        "source": f"Local Ollama ({self.model})"
                    }
        except Exception as e:
            print(f"Ollama offline/connection error: {e}. Activating chat fallback...")

        # Fallback response
        fallback_advice = self._generate_chat_fallback(
            user_message=user_message,
            current_stats=current_stats,
            all_scores=all_scores,
            suggestions=suggestions
        )
        return {
            "advice": fallback_advice,
            "source": "Aegis AI Fallback Engine (Offline)"
        }

    def _generate_chat_fallback(
        self,
        user_message: str,
        current_stats: Optional[Dict[str, Any]],
        all_scores: List[Dict[str, Any]],
        suggestions: List[Dict[str, Any]]
    ) -> str:
        """
        Rule-based chatbot response to answer questions about stats & suggestions offline.
        """
        msg = user_message.lower()
        
        total_runs = len(all_scores)
        max_score = max([s.get("score", 0) for s in all_scores]) if all_scores else 0
        avg_pps = sum([s.get("pps", 0.0) for s in all_scores]) / total_runs if total_runs else 0.0
        avg_apm = sum([s.get("apm", 0.0) for s in all_scores]) / total_runs if total_runs else 0.0
        avg_finesse = sum([s.get("finesse_rate", 1.0) for s in all_scores]) / total_runs if total_runs else 1.0
        
        top_suggestion = suggestions[0]["reason"] if suggestions else "No suggestions available yet."
        
        # Check greeting
        if any(w in msg for w in ["hello", "hi", "hey", "greet", "who are you"]):
            return "Hello player! I am Aegis, your offline tactical coach. I can help analyze your speeds, finesse execution, or explain your recommended training regimens. What would you like to review?"
            
        # Check training or recommendations
        if any(w in msg for w in ["train", "suggest", "routine", "practice", "recommend", "priority"]):
            if suggestions:
                recs = []
                for s in suggestions[:3]:
                    name = s['training_id'].replace('_', ' ').title()
                    recs.append(f"• **{name}**: {s['reason']}")
                return "Your prioritized training recommendations based on your gameplay profile are:\n" + "\n".join(recs)
            return "No runs are loaded to draw suggestions from. Upload a replay file or play a session first!"
            
        # Check weakness or mistakes
        if any(w in msg for w in ["weakness", "bad", "worst", "fail", "mistake", "improve", "help"]):
            if suggestions:
                return f"Your primary improvement area right now is: {top_suggestion}"
            return "You have no recorded stats to analyze yet. Upload a replay to diagnose potential mechanical issues."
            
        # Check speed
        if any(w in msg for w in ["speed", "pps", "fast", "slow"]):
            current_pps_str = ""
            if current_stats:
                current_pps_str = f" In your current run, you achieved {current_stats.get('pps', 0.0):.2f} PPS."
            return f"Your historical average speed is **{avg_pps:.2f} PPS** (Personal Best score: {max_score:,}).{current_pps_str} To improve your speed, focus on lookahead queue planning and minimize input hesitation at the spawn zone."
            
        # Check finesse
        if any(w in msg for w in ["finesse", "fault", "key", "kpp"]):
            current_fin_str = ""
            if current_stats:
                current_fin_str = f" In your current run, your finesse rate was {current_stats.get('finesse_rate', 1.0)*100:.1f}% with {current_stats.get('finesse_faults', 0)} faults."
            return f"Your historical average finesse rate is **{avg_finesse*100:.1f}%**.{current_fin_str} To minimize faults, practice the Finesse Rewind module to reset the board when double-tapping or making improper rotations."

        # Check offense
        if any(w in msg for w in ["offense", "apm", "attack", "combo", "quad", "tspin"]):
            current_apm_str = ""
            if current_stats:
                current_apm_str = f" In your current run, you had {current_stats.get('apm', 0.0):.1f} APM."
            return f"Your historical average offensive output is **{avg_apm:.2f} APM**.{current_apm_str} To maximize attack efficiency, try to stack cleanly for Back-to-Back Quads and T-Spins rather than random single clears."

        # Default fallback summary
        summary = f"I am currently offline from Ollama, but analyzing your profile of {total_runs} runs:\n"
        summary += f"• **Personal Best**: {max_score:,}\n"
        summary += f"• **Average Speed**: {avg_pps:.2f} PPS\n"
        summary += f"• **Finesse Rate**: {avg_finesse*100:.1f}%\n"
        if suggestions:
            summary += f"• **Top Priority Training**: {suggestions[0]['training_id'].replace('_', ' ').title()}"
        return summary

# Singleton instance
ollama_client = OllamaClient()
