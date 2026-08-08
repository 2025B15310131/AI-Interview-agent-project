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
# --- NEW PREMIUM FRONTEND UI (Glassmorphism & Dashboard) ---
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Interview Agent | ABTalks Hackathon</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
            body { 
                background: radial-gradient(circle at top left, #0f172a, #020617); 
                color: #f8fafc; height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; 
            }
            
            /* Main Container */
            .container { 
                background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; width: 100%; max-width: 900px; 
                height: 92vh; display: flex; flex-direction: column; box-shadow: 0 30px 60px rgba(0,0,0,0.6); overflow: hidden; 
            }
            
            /* Header */
            .header { 
                padding: 20px 30px; background: rgba(255, 255, 255, 0.02); border-bottom: 1px solid rgba(255, 255, 255, 0.08); 
                display: flex; justify-content: space-between; align-items: center; 
            }
            .header-left { display: flex; align-items: center; gap: 15px; }
            .header h2 { font-size: 20px; font-weight: 700; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .status-dot { width: 10px; height: 10px; background-color: #34d399; border-radius: 50%; box-shadow: 0 0 10px #34d399; animation: pulse 2s infinite; }
            .badge { background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
            
            /* Chat Area */
            .chat-area { flex: 1; padding: 30px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; scroll-behavior: smooth; }
            .msg-wrapper { display: flex; align-items: flex-end; gap: 12px; animation: slideUp 0.4s ease-out forwards; opacity: 0; transform: translateY(15px); width: 100%; }
            .msg-wrapper.user { justify-content: flex-end; flex-direction: row-reverse; }
            
            /* Avatars */
            .avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 14px; font-weight: 700; flex-shrink: 0; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
            .ai-avatar { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; border: 2px solid rgba(255,255,255,0.1); }
            .user-avatar { background: linear-gradient(135deg, #0ea5e9, #38bdf8); color: white; border: 2px solid rgba(255,255,255,0.1); }
            
            /* Message Bubbles */
            .msg { max-width: 75%; padding: 16px 22px; font-size: 15px; line-height: 1.6; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
            .msg.ai { background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(255,255,255,0.05); border-bottom-left-radius: 4px; color: #f1f5f9; }
            .msg.user { background: linear-gradient(135deg, #0284c7, #2563eb); border-bottom-right-radius: 4px; color: white; }
            
            /* Input Area */
            .input-area { padding: 24px 30px; background: rgba(15, 23, 42, 0.8); border-top: 1px solid rgba(255, 255, 255, 0.08); display: flex; gap: 15px; align-items: flex-end; }
            textarea { flex: 1; background: rgba(0, 0, 0, 0.2); color: #f8fafc; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 16px 20px; font-size: 15px; outline: none; resize: none; height: 60px; transition: all 0.3s; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1); }
            textarea:focus { border-color: #38bdf8; background: rgba(0,0,0,0.3); box-shadow: inset 0 2px 4px rgba(0,0,0,0.1), 0 0 0 3px rgba(56, 189, 248, 0.1); }
            button { background: linear-gradient(90deg, #0ea5e9, #6366f1); color: white; border: none; padding: 0 32px; height: 60px; border-radius: 14px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.3s; text-transform: uppercase; letter-spacing: 1px; }
            button:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(99, 102, 241, 0.4); }
            button:disabled { background: #334155; color: #94a3b8; cursor: not-allowed; transform: none; box-shadow: none; }

            /* Typing Indicator */
            /* Typing Indicator */
.typing { display: flex; align-items: center; padding: 15px 22px; background: rgba(30, 41, 59, 0.8); border-radius: 20px; border-bottom-left-radius: 4px; border: 1px solid rgba(255,255,255,0.05); width: fit-content; }
.dot { display: inline-block; width: 6px; height: 6px; background: #94a3b8; border-radius: 50%; margin: 0 3px; animation: bounce 1.4s infinite ease-in-out both; }
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
            /* Feedback Dashboard (The 20k Winner UI) */
            .feedback-card { background: linear-gradient(145deg, #1e293b, #0f172a); border: 1px solid #38bdf8; border-radius: 20px; padding: 30px; margin-top: 20px; box-shadow: 0 20px 40px rgba(56, 189, 248, 0.15); animation: slideUp 0.8s ease-out forwards; }
            .fb-header { display: flex; align-items: center; gap: 15px; margin-bottom: 25px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
            .fb-icon { font-size: 28px; }
            .fb-title { font-size: 24px; font-weight: 700; background: linear-gradient(90deg, #34d399, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .fb-summary { color: #e2e8f0; font-size: 15px; line-height: 1.6; margin-bottom: 25px; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 12px; border-left: 4px solid #818cf8; }
            
            .fb-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .fb-section { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 20px; border-radius: 16px; }
            .fb-section.full { grid-column: span 2; }
            .fb-label { font-size: 13px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }
            
            .tags { display: flex; flex-wrap: wrap; gap: 10px; }
            .tag { padding: 8px 16px; border-radius: 20px; font-size: 13.5px; font-weight: 500; line-height: 1.4; }
            .tag.strength { background: rgba(56, 189, 248, 0.1); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.3); }
            .tag.gap { background: rgba(244, 63, 94, 0.1); color: #fda4af; border: 1px solid rgba(244, 63, 94, 0.3); }
            .tag.next { background: rgba(16, 185, 129, 0.1); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3); }

            /* Animations */
            @keyframes slideUp { to { opacity: 1; transform: translateY(0); } }
            @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(52, 211, 153, 0); } 100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); } }
            @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
            
            /* Scrollbar */
            ::-webkit-scrollbar { width: 8px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
            ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
            /* --- MOBILE RESPONSIVENESS (Media Queries) --- */
            @media (max-width: 768px) {
                body { padding: 10px; }
                .container { height: 95vh; border-radius: 16px; }
                .header { padding: 15px 20px; }
                .header h2 { font-size: 18px; }
                .badge { font-size: 10px; padding: 4px 10px; }
                
                .chat-area { padding: 20px 15px; gap: 18px; }
                .msg { max-width: 90%; padding: 14px 18px; font-size: 14px; }
                .avatar { width: 30px; height: 30px; font-size: 12px; }
                
                .input-area { padding: 15px; flex-direction: column; gap: 10px; }
                textarea { width: 100%; height: 50px; padding: 12px 15px; }
                button { width: 100%; height: 50px; font-size: 14px; }
                
                /* Make Feedback Dashboard stack vertically on mobile */
                .feedback-card { padding: 20px; }
                .fb-grid { grid-template-columns: 1fr; gap: 15px; }
                .fb-section.full { grid-column: span 1; }
                .fb-title { font-size: 20px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-left">
                    <div class="status-dot"></div>
                    <h2>AI Interview Agent</h2>
                </div>
                <span class="badge" id="turnBadge">System Booting...</span>
            </div>
            
            <div class="chat-area" id="chatBox">
                <!-- Messages will render here -->
                <div class="msg-wrapper ai" id="typingIndicator" style="display: none;">
                    <div class="avatar ai-avatar">AI</div>
                    <div class="typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
                </div>
            </div>

            <div class="input-area" id="inputContainer">
                <textarea id="answerInput" placeholder="Type your technical response here..."></textarea>
                <button id="sendBtn" onclick="sendMsg()">Submit</button>
            </div>
        </div>

        <script>
            const sessionId = "sess-" + Math.random().toString(36).substr(2, 9);
            const chatBox = document.getElementById('chatBox');
            const typingIndicator = document.getElementById('typingIndicator');
            let turns = 0;

            function showTyping(show) {
                typingIndicator.style.display = show ? 'flex' : 'none';
                if(show) chatBox.appendChild(typingIndicator);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            function addMessage(role, text) {
                const wrapper = document.createElement('div');
                wrapper.className = `msg-wrapper ${role}`;
                
                const avatar = `<div class="avatar ${role === 'ai' ? 'ai-avatar' : 'user-avatar'}">${role === 'ai' ? 'AI' : 'YOU'}</div>`;
                const msgBubble = `<div class="msg ${role}">${text}</div>`;
                
                wrapper.innerHTML = role === 'ai' ? avatar + msgBubble : msgBubble + avatar;
                
                chatBox.insertBefore(wrapper, typingIndicator);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            function renderFeedback(feedback) {
                const wrapper = document.createElement('div');
                wrapper.className = 'msg-wrapper ai';
                
                let html = `<div class="avatar ai-avatar">AI</div>`;
                html += `<div class="feedback-card">
                    <div class="fb-header">
                        <span class="fb-icon">📊</span>
                        <div class="fb-title">Final Assessment Report</div>
                    </div>
                    <div class="fb-summary">${feedback.summary}</div>
                    
                    <div class="fb-grid">
                        <div class="fb-section">
                            <div class="fb-label">🌟 Core Strengths</div>
                            <div class="tags">`;
                feedback.strengths.forEach(s => html += `<span class="tag strength">${s}</span>`);
                html += `</div></div>
                        <div class="fb-section">
                            <div class="fb-label">⚠️ Areas to Improve</div>
                            <div class="tags">`;
                feedback.gaps.forEach(g => html += `<span class="tag gap">${g}</span>`);
                html += `</div></div>
                        <div class="fb-section full">
                            <div class="fb-label">🚀 Next Steps & Recommendations</div>
                            <div class="tags">`;
                feedback.next.forEach(n => html += `<span class="tag next">${n}</span>`);
                html += `</div></div></div></div>`;

                wrapper.innerHTML = html;
                chatBox.insertBefore(wrapper, typingIndicator);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            async function startInterview() {
                showTyping(true);
                document.getElementById('turnBadge').innerText = "Initializing...";
                
                // Using the exact structure from candidates.json screenshot
                const dummyCandidate = {
                    "id": "c-001",
                    "completed_missions": ["Retrieval-Augmented Generation (RAG)", "Vector Databases"],
                    "skipped_topics": ["Model Context Protocol (MCP)"]
                };

                const res = await fetch('/api/interview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sessionId: sessionId, candidate: dummyCandidate })
                });
                
                const data = await res.json();
                showTyping(false);
                addMessage('ai', data.reply);
                document.getElementById('turnBadge').innerText = "Question 1 of 8";
            }

            async function sendMsg() {
                const input = document.getElementById('answerInput');
                const btn = document.getElementById('sendBtn');
                const msg = input.value.trim();
                
                if (!msg) return;

                addMessage('user', msg);
                input.value = '';
                btn.disabled = true;
                btn.innerText = 'Analyzing...';
                showTyping(true);

                try {
                    const res = await fetch('/api/interview', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sessionId: sessionId, message: msg })
                    });
                    
                    const data = await res.json();
                    showTyping(false);
                    addMessage('ai', data.reply);
                    turns++;

                    if (data.done) {
                        document.getElementById('inputContainer').style.display = 'none';
                        document.getElementById('turnBadge').innerText = "Interview Completed";
                        document.getElementById('turnBadge').style.background = "rgba(52, 211, 153, 0.2)";
                        document.getElementById('turnBadge').style.color = "#34d399";
                        document.getElementById('turnBadge').style.borderColor = "#34d399";
                        renderFeedback(data.feedback);
                    } else {
                        document.getElementById('turnBadge').innerText = "Question " + (turns + 1) + " of 8";
                        btn.disabled = false;
                        btn.innerText = 'Submit';
                        input.focus();
                    }
                } catch (e) {
                    showTyping(false);
                    addMessage('ai', "System encountered a network anomaly. Please try again.");
                    btn.disabled = false;
                    btn.innerText = 'Submit';
                }
            }

            // Enter key to submit
            document.getElementById('answerInput').addEventListener('keypress', function (e) {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
            });

            window.onload = startInterview;
        </script>
    </body>
    </html>
    """

# --- HACKATHON REQUIRED ENDPOINT ---
# --- HACKATHON REQUIRED ENDPOINT ---
# --- HACKATHON REQUIRED ENDPOINT (WINNING BUILD) ---
@app.post("/api/interview", response_model=InterviewResponse)
def handle_interview(req: InterviewRequest):
    session_id = req.sessionId
    
    # 1. START INTERVIEW
    if req.candidate is not None:
        try:
            with open("curriculum.json", "r") as f:
                curriculum_data = json.load(f)
        except Exception:
            curriculum_data = "Curriculum data missing."

        # THE 20K PRIZE WINNING PROMPT 🏆
        system_prompt = f"""You are an elite, highly realistic AI engineering interviewer for an enterprise cohort.
        Candidate Profile: {json.dumps(req.candidate)}
        Course Curriculum: {json.dumps(curriculum_data)}
        
        CRITICAL RULES FOR THE INTERVIEW:
        1. DEEP PROFILE TARGETING: Analyze the candidate's profile. Naturally weave in their 'completed_missions' (praise them and dig deep) and 'skipped_topics' (gently test if they know the basics of what they missed).
        2. ADAPTIVE DIFFICULTY: If they answer well, ask a tougher follow-up. If they struggle or say 'I don't know', do not fail them immediately; give a brief hint and pivot to a related, easier concept.
        3. THE 4-DAY RULE: You MUST ask exactly 8 questions across the interview. These questions MUST cover topics from at least 4 DIFFERENT DAYS in the curriculum. 
        4. CONVERSATIONAL FLOW: Behave exactly like a senior human engineer. Ask ONE short, clear question at a time. No robotic lists.
        """

        sessions[session_id] = {
            "turn_count": 0,
            "candidate": req.candidate,
            "history": [{"role": "system", "content": system_prompt}]
        }
        
        sessions[session_id]["history"].append({"role": "user", "content": "Hello, I am ready for my interview."})
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=sessions[session_id]["history"],
            temperature=0.7 # Perfect balance of logic and natural conversation
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
            # 3. END INTERVIEW & GENERATE HIGH-QUALITY FEEDBACK
            feedback_prompt = "The interview is now over. Generate a highly professional, structured evaluation of the candidate based on the 8 turns. Output ONLY a valid JSON object with EXACTLY these keys: 'summary' (overall performance), 'strengths' (array of strings), 'gaps' (array of strings), and 'next' (array of actionable next steps)."
            
            session["history"].append({"role": "system", "content": feedback_prompt})
            
            try:
                feedback_res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=session["history"],
                    response_format={"type": "json_object"}
                )
                feedback_data = json.loads(feedback_res.choices[0].message.content)
            except Exception:
                feedback_data = {
                    "summary": "The candidate completed the 8-turn technical interview, demonstrating a solid foundational understanding of the AI cohort topics.",
                    "strengths": ["Clear communication", "Good grasp of core concepts"], 
                    "gaps": ["Needs more focus on skipped modules"], 
                    "next": ["Review curriculum documentation", "Practice building end-to-end pipelines"]
                }
            
            final_reply = "Thank you for your time and effort today. That concludes our technical interview! I have compiled your final feedback."
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