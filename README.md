# 🤖 AI Interview Agent | ABTalks Hackathon Enterprise Edition

An advanced, conversational AI-powered technical interview agent built for the ABTalks Hackathon. It simulates a realistic senior engineering interview, adapts dynamically to candidate profiles, enforces curriculum requirements, tracks performance with a 60s pressure timer, and generates a structured scoreboard report.

---

## 🚀 Key Features

* **Real-time Conversational AI:** Powered by Llama models via Groq SDK, behaving like a senior engineering manager.
* **Smart Profile Targeting:** Automatically reads candidate data (completed missions & skipped topics) to personalize the interview.
* **The 4-Day Rule & 8-Turn Limit:** Strictly manages the interview flow to cover at least 4 different days across 8 precise questions.
* **Explicit Question Numbering:** Formatted dynamically as `**Question X:**` for clear tracking.
* **Interactive Controls:**
  * **AI Voice Output (TTS):** Reads questions aloud with auto-stripped markdown.
  * **Speech-to-Text (MIC):** Allows users to speak their answers directly.
  * **Pressure Timer (60s):** Optional countdown bar for interview simulation.
  * **Skip Button:** Allows candidates to skip tricky questions while tracking skipped counts.
* **Comprehensive Performance Report:** End-of-interview breakdown featuring:
  * **Scoreboard:** Final score (e.g., 6/8), Correct count, and Skipped count.
  * **Visual Tags:** Color-coded badges for *Demonstrated Strengths*, *Areas for Improvement*, and *Actionable Next Steps*.
  * **Download Report:** One-click option to download a formatted `.txt` assessment summary.

---

## 🛠️ Tech Stack

* **Backend:** FastAPI, Python, Pydantic
* **AI Engine:** Groq API (`llama-3.3-70b-versatile` / `llama3-8b-8192`)
* **Frontend:** Responsive Glassmorphism UI, Vanilla JavaScript, Marked.js (Markdown parsing), Web Speech API
* **Deployment:** Render / Vercel

---

## ⚙️ Local Setup & Installation

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/your-username/AI-Interview-agent-project.git](https://github.com/your-username/AI-Interview-agent-project.git)
   cd AI-Interview-agent-project