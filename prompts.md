# AI Usage Logs & Prompts

During the development of this AI Interview Agent for the ABTalks Hackathon, AI (Gemini) was used as a collaborative pair-programmer to design, debug, and refine the architecture. Below are the key prompts and stages used during development:

1. **Backend API & Session Setup:**
   * *Prompt:* "Create a FastAPI backend that handles interview turns using Groq API (`llama-3.3-70b-versatile`), integrating curriculum data and tracking 8 turns."

2. **UI & Glassmorphism Design:**
   * *Prompt:* "Design a dark-themed glassmorphism chat interface with a start screen, voice output toggle, and a 60-second pressure timer."

3. **Dynamic Typing Indicator Fix:**
   * *Prompt:* "Fix the typing indicator so that bouncing dots appear smoothly when the AI is generating a response."

4. **Human-Like Adaptive Prompting:**
   * *Prompt:* "Refine the system prompt so the AI acts like a senior engineering manager, asks short scenario-based questions, acknowledges previous answers, and enforces explicit `**Question X:**` numbering."

5. **Scoreboard & Report UI:**
   * *Prompt:* "Add a skip button, track correct vs skipped counts, and display a visual tag-based scoreboard in the final assessment report with a TXT download option."