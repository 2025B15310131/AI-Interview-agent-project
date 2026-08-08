from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
from dotenv import load_dotenv
from groq import Groq
import os
import json
import requests

# Load Environment Variables
load_dotenv()
BREETH_API_KEY = os.getenv("BREETH_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)
app = FastAPI(title="AI Interview Agent - Hackathon Build")

# --- DATA MODELS ---
class InterviewRequest(BaseModel):
    sessionId: str
    candidate: Optional[Dict] = None
    message: Optional[str] = None

class FeedbackModel(BaseModel):
    summary: str
    strengths: List[str]
    gaps: List[str]
    next: List[str]

class InterviewResponse(BaseModel):
    reply: str
    done: bool
    feedback: Optional[FeedbackModel] = None

# --- IN-MEMORY STATE ---
sessions = {}

def log_to_breeth(session_id: str, content: str):
    try:
        url = "https://api.thebreeth.com/v1/episodes"
        headers = {
            "Authorization": f"Bearer {BREETH_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"content": f"[Session: {session_id}] {content}"}
        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"Breeth Error: {e}")

# --- NEW FRONTEND UI (Chat Interface) ---
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Interview Agent</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
            body { background: #020617; color: #f8fafc; height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
            .container { background: #0f172a; border: 1px solid #334155; border-radius: 20px; width: 100%; max-width: 800px; height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 50px rgba(0,0,0,0.5); overflow: hidden; }
            .header { padding: 20px 30px; background: #1e293b; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
            .header h2 { font-size: 20px; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .badge { background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
            
            .chat-area { flex: 1; padding: 30px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; }
            .msg { max-width: 80%; line-height: 1.5; font-size: 15px; padding: 15px 20px; border-radius: 12px; }
            .msg.ai { background: #1e293b; border: 1px solid #334155; border-top-left-radius: 2px; align-self: flex-start; }
            .msg.user { background: #38bdf8; color: #020617; border-top-right-radius: 2px; align-self: flex-end; font-weight: 500; }
            
            .input-area { padding: 20px; background: #1e293b; border-top: 1px solid #334155; display: flex; gap: 15px; }
            textarea { flex: 1; background: #0f172a; color: #f8fafc; border: 1px solid #334155; border-radius: 10px; padding: 15px; font-size: 14px; outline: none; resize: none; height: 60px; transition: 0.2s; }
            textarea:focus { border-color: #38bdf8; }
            button { background: linear-gradient(90deg, #0ea5e9, #6366f1); color: white; border: none; padding: 0 30px; border-radius: 10px; font-weight: 600; cursor: pointer; transition: 0.2s; }
            button:hover { opacity: 0.9; }
            button:disabled { background: #334155; color: #94a3b8; cursor: not-allowed; }

            .feedback-box { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 25px; border-radius: 12px; margin-top: 20px; }
            .feedback-title { color: #34d399; font-weight: bold; margin-bottom: 15px; font-size: 18px; }
            .fb-section { margin-bottom: 15px; }
            .fb-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
            .fb-text { color: #e2e8f0; font-size: 14px; line-height: 1.6; }
            .fb-list { padding-left: 20px; font-size: 14px; color: #e2e8f0; line-height: 1.6; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Interview Session</h2>
                <span class="badge" id="turnBadge">Initializing...</span>
            </div>
            
            <div class="chat-area" id="chatBox">
                <!-- Messages will appear here -->
            </div>

            <div class="input-area" id="inputContainer">
                <textarea id="answerInput" placeholder="Type your response..."></textarea>
                <button id="sendBtn" onclick="sendMsg()">Send</button>
            </div>
        </div>

        <script>
            // Generate a random session ID
            const sessionId = "sess-" + Math.random().toString(36).substr(2, 9);
            const chatBox = document.getElementById('chatBox');
            let turns = 0;

            function addMessage(role, text) {
                const div = document.createElement('div');
                div.className = 'msg ' + (role === 'ai' ? 'ai' : 'user');
                div.innerText = text;
                chatBox.appendChild(div);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            function renderFeedback(feedback) {
                const div = document.createElement('div');
                div.className = 'feedback-box';
                
                let html = `<div class="feedback-title">Final Interview Feedback</div>`;
                html += `<div class="fb-section"><div class="fb-label">Summary</div><div class="fb-text">${feedback.summary}</div></div>`;
                
                html += `<div class="fb-section"><div class="fb-label">Strengths</div><ul class="fb-list">`;
                feedback.strengths.forEach(s => html += `<li>${s}</li>`);
                html += `</ul></div>`;

                html += `<div class="fb-section"><div class="fb-label">Areas to Improve</div><ul class="fb-list">`;
                feedback.gaps.forEach(g => html += `<li>${g}</li>`);
                html += `</ul></div>`;

                div.innerHTML = html;
                chatBox.appendChild(div);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            async function startInterview() {
                const dummyCandidate = {
                    "id": "c-001",
                    "completed_missions": ["RAG", "Vector Databases"],
                    "skipped_topics": ["Model Context Protocol"]
                };

                const res = await fetch('/api/interview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sessionId: sessionId, candidate: dummyCandidate })
                });
                
                const data = await res.json();
                addMessage('ai', data.reply);
                document.getElementById('turnBadge').innerText = "Turn 1 of 8";
            }

            async function sendMsg() {
                const input = document.getElementById('answerInput');
                const btn = document.getElementById('sendBtn');
                const msg = input.value.trim();
                
                if (!msg) return;

                addMessage('user', msg);
                input.value = '';
                btn.disabled = true;
                btn.innerText = 'Wait...';

                try {
                    const res = await fetch('/api/interview', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sessionId: sessionId, message: msg })
                    });
                    
                    const data = await res.json();
                    addMessage('ai', data.reply);
                    turns++;

                    if (data.done) {
                        document.getElementById('inputContainer').style.display = 'none';
                        document.getElementById('turnBadge').innerText = "Interview Completed";
                        renderFeedback(data.feedback);
                    } else {
                        document.getElementById('turnBadge').innerText = "Turn " + (turns + 1) + " of 8";
                        btn.disabled = false;
                        btn.innerText = 'Send';
                        input.focus();
                    }
                } catch (e) {
                    addMessage('ai', "Error connecting to server.");
                    btn.disabled = false;
                    btn.innerText = 'Send';
                }
            }

            // Start automatically when page loads
            window.onload = startInterview;
        </script>
    </body>
    </html>
    """

# --- HACKATHON REQUIRED ENDPOINT ---
# --- HACKATHON REQUIRED ENDPOINT ---
@app.post("/api/interview", response_model=InterviewResponse)
def handle_interview(req: InterviewRequest):
    session_id = req.sessionId
    
    # 1. START INTERVIEW
    if req.candidate is not None:
        # Load Curriculum data
        try:
            with open("curriculum.json", "r") as f:
                curriculum_data = json.load(f)
        except Exception:
            curriculum_data = "Curriculum data missing."

        # SMART SYSTEM PROMPT: Enforcing the 4-days rule
        system_prompt = f"""You are an expert AI engineering interviewer. 
        Candidate profile: {json.dumps(req.candidate)}.
        Course Curriculum: {json.dumps(curriculum_data)}.
        
        STRICT RULES:
        1. Ask exactly 1 technical question at a time. Do not provide the answer.
        2. You will ask a total of 8 questions. You MUST cover topics from at least 4 DIFFERENT DAYS from the provided curriculum.
        3. Generate intelligent follow-up questions if the user gives a partial answer.
        4. Keep the tone conversational, realistic, and concise."""

        sessions[session_id] = {
            "turn_count": 0,
            "candidate": req.candidate,
            "history": [{"role": "system", "content": system_prompt}]
        }
        
        sessions[session_id]["history"].append({"role": "user", "content": "Hello, I am ready to begin my technical interview."})
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=sessions[session_id]["history"]
        )
        
        reply = response.choices[0].message.content.strip()
        sessions[session_id]["history"].append({"role": "assistant", "content": reply})
        sessions[session_id]["turn_count"] += 1
        
        log_to_breeth(session_id, f"Interview Started. AI Asked: {reply}")
        return {"reply": reply, "done": False}

    # 2. CONVERSATION TURN
    if req.message and session_id in sessions:
        session = sessions[session_id]
        session["history"].append({"role": "user", "content": req.message})
        
        log_to_breeth(session_id, f"Candidate Answered: {req.message}")

        if session["turn_count"] >= 8:
            # 3. END INTERVIEW & FEEDBACK
            feedback_prompt = "The interview is over. Output a JSON object evaluating the candidate based on the 8 turns. Use exactly these keys: 'summary' (string), 'strengths' (array of strings), 'gaps' (array of strings), and 'next' (array of strings). Keep points concise and actionable."
            
            session["history"].append({"role": "system", "content": feedback_prompt})
            
            try:
                feedback_res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=session["history"],
                    response_format={"type": "json_object"}
                )
                feedback_data = json.loads(feedback_res.choices[0].message.content)
            except Exception as e:
                feedback_data = {
                    "summary": "Interview completed successfully. The candidate demonstrated a solid foundational understanding.",
                    "strengths": ["Clear communication", "Attempted all questions"], 
                    "gaps": ["Needs deeper dive into specific implementation details"], 
                    "next": ["Review skipped topics", "Practice hands-on coding"]
                }
            
            final_reply = "Thank you for your time today. That concludes our technical interview! I have analyzed your responses and generated your feedback."
            log_to_breeth(session_id, "Interview Completed. Feedback Generated.")
            
            return {"reply": final_reply, "done": True, "feedback": feedback_data}
            
        else:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=session["history"]
            )
            
            reply = response.choices[0].message.content.strip()
            session["history"].append({"role": "assistant", "content": reply})
            session["turn_count"] += 1
            
            log_to_breeth(session_id, f"AI Follow-up: {reply}")
            return {"reply": reply, "done": False}

    raise HTTPException(status_code=400, detail="Invalid request payload or session not initialized.")