# Planning Specification: Ollama Chat Integration for Stats & Suggested Trainings

This plan details the implementation of an interactive AI Coach chat interface powered by local Ollama/Gemma. It allows the player to ask questions about their gameplay history, recent replay diagnostics, and recommended training routines.

## 1. Objectives & Use Cases
* **Interactive Coaching:** Players can query the AI: *"What are my biggest weaknesses across my last 5 matches?"*, *"Why is it suggesting Finesse Rewind?"*, or *"How can I improve my APM?"*.
* **Dynamic Context Injection:** The backend will automatically query the SQLite database (`scores` table) to compile a profile of the user's stats, history progression, and latest suggestions, injecting them as context into the prompt.
* **Resilient Fallbacks:** If the local Ollama instance is offline or timeouts, the assistant will fall back to a local rules-engine summary of the stats and training recommendations.

## 2. API Design
We will add a new endpoint `/chat` in the FastAPI backend:
* **Route:** `POST /api/v1/chat`
* **Payload:**
  ```json
  {
    "message": "User query here",
    "history": [
      {"role": "user", "content": "..."}
    ],
    "current_stats": { ... } // Optional: stats of the currently loaded replay
  }
  ```
* **Response:**
  ```json
  {
    "response": "AI coach response text here",
    "source": "Local Ollama (gemma:26b) / Fallback Engine"
  }
  ```

## 3. Core Logic & Prompt Engineering
A new class method or instance method will be added to `OllamaClient`:
* Compile history stats from the database (e.g., average PPS, total runs, max score, average finesse rate, last run stats).
* Include the latest suggestions computed for the player.
* Format the prompt with instructions for a helpful, concise, esports-focused coach.

## 4. UI Implementation (Dashboard Chat Widget)
* **Design:** A sleek, glassmorphic chat widget docked in the main dashboard (`index.html`).
* **Visuals:** Dark neon styling (cyan/magenta/purple), responsive scrolling, message bubble distinction, typing indicators, and a clean prompt interface.
* **Interactivity:** Pre-filled suggested questions (e.g., *"What is my main training priority?"*, *"How is my finesse progress?"*).

## 5. Development Steps
1. **Extend `OllamaClient`** in `backend/app/core/ollama_client.py` with generic chat and context assembly.
2. **Add `/chat` endpoint** in `backend/app/api/endpoints.py`.
3. **Integrate the Chat UI** into `backend/app/static/index.html`.
4. **Test the integration** with and without Ollama active.
