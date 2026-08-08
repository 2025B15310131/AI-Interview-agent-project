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
# --- MASTER PREMIUM FRONTEND UI (Voice, Timer, Start Screen, Report) ---
# --- MASTER PREMIUM FRONTEND UI (Safe Mode - No Emojis) ---
# --- FOOLPROOF STABLE UI (No Parsing Errors) ---
# --- ULTIMATE WINNING UI (Start Screen, Voice, Timer, Report Download) ---
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
            body { background: radial-gradient(circle at top left, #0f172a, #020617); color: #f8fafc; height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
            
            .container { background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; width: 100%; max-width: 900px; height: 92vh; display: flex; flex-direction: column; box-shadow: 0 30px 60px rgba(0,0,0,0.6); overflow: hidden; position: relative; }
            
            /* Start Screen Overlay */
            #startScreen { position: absolute; inset: 0; background: #0f172a; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 50; padding: 20px; text-align: center; }
            #startScreen h1 { font-size: 32px; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }
            #startScreen p { color: #94a3b8; margin-bottom: 30px; font-size: 16px; }
            .toggles { display: flex; gap: 20px; margin-bottom: 40px; background: rgba(255,255,255,0.05); padding: 15px 25px; border-radius: 12px; }
            .toggles label { display: flex; align-items: center; gap: 10px; cursor: pointer; font-weight: 500; color: #cbd5e1; font-size: 14px; }
            .toggles input[type="checkbox"] { width: 18px; height: 18px; cursor: pointer; accent-color: #0ea5e9; }
            .start-btn { background: linear-gradient(90deg, #10b981, #059669); color: white; border: none; font-weight: 600; font-size: 18px; padding: 15px 40px; border-radius: 30px; box-shadow: 0 10px 20px rgba(16, 185, 129, 0.3); cursor: pointer; transition: 0.3s; }
            .start-btn:hover { transform: translateY(-3px); }

            /* Timer Bar */
            #timerBarContainer { height: 4px; background: rgba(255,255,255,0.1); width: 100%; display: none; }
            #timerFill { height: 100%; width: 100%; background: #ef4444; transition: width 1s linear; }

            /* Header & Chat Layout */
            .header { padding: 20px 30px; background: rgba(255, 255, 255, 0.02); border-bottom: 1px solid rgba(255, 255, 255, 0.08); display: flex; justify-content: space-between; align-items: center; }
            .header-left { display: flex; align-items: center; gap: 15px; }
            .header h2 { font-size: 20px; font-weight: 700; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .badge { background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; }
            
            .chat-area { flex: 1; padding: 30px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; scroll-behavior: smooth; display: none; }
            .msg-wrapper { display: flex; align-items: flex-end; gap: 12px; animation: slideUp 0.4s ease-out forwards; width: 100%; }
            .msg-wrapper.user { justify-content: flex-end; flex-direction: row-reverse; }
            .avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 14px; font-weight: 700; flex-shrink: 0; }
            .ai-avatar { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; }
            .user-avatar { background: linear-gradient(135deg, #0ea5e9, #38bdf8); color: white; }
            .msg { max-width: 75%; padding: 16px 22px; font-size: 15px; line-height: 1.6; border-radius: 20px; color: #f1f5f9; }
            .msg.ai { background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(255,255,255,0.05); border-bottom-left-radius: 4px; }
            .msg.user { background: linear-gradient(135deg, #0284c7, #2563eb); border-bottom-right-radius: 4px; color: white; }

            /* Input Area & Mic */
            .input-area { padding: 20px 30px; background: rgba(15, 23, 42, 0.8); border-top: 1px solid rgba(255, 255, 255, 0.08); display: none; gap: 10px; align-items: center; }
            textarea { flex: 1; background: rgba(0, 0, 0, 0.2); color: #f8fafc; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 16px 20px; font-size: 15px; outline: none; resize: none; height: 55px; }
            
            .icon-btn { background: #1e293b; border: 1px solid rgba(255,255,255,0.1); color: white; width: 55px; height: 55px; border-radius: 14px; font-size: 13px; cursor: pointer; transition: 0.3s; display: flex; justify-content: center; align-items: center; font-weight: 700; }
            .icon-btn.recording { background: #ef4444; animation: pulseRed 1.5s infinite; border: none; }
            .submit-btn { background: linear-gradient(90deg, #0ea5e9, #6366f1); color: white; border: none; padding: 0 25px; height: 55px; border-radius: 14px; font-size: 15px; font-weight: 600; cursor: pointer; transition: 0.3s; }
            button:disabled { opacity: 0.5; cursor: not-allowed; }

            /* Typing & Feedback */
            .typing { display: none; align-items: center; padding: 15px 22px; background: rgba(30, 41, 59, 0.8); border-radius: 20px; border-bottom-left-radius: 4px; }
            .dot { display: inline-block; width: 6px; height: 6px; background: #94a3b8; border-radius: 50%; margin: 0 3px; animation: bounce 1.4s infinite ease-in-out both; }
            .dot:nth-child(1) { animation-delay: -0.32s; }
            .dot:nth-child(2) { animation-delay: -0.16s; }

            .feedback-card { background: linear-gradient(145deg, #1e293b, #0f172a); border: 1px solid #38bdf8; border-radius: 20px; padding: 30px; margin-top: 20px; width: 100%; }
            .fb-title { font-size: 24px; font-weight: 700; color: #38bdf8; margin-bottom: 20px; }
            .dl-btn { background: #f59e0b; color: white; border: none; padding: 12px 20px; border-radius: 10px; cursor: pointer; font-weight: 600; margin-top: 20px; width: 100%; transition: 0.3s; }
            .dl-btn:hover { background: #d97706; }

            @keyframes slideUp { to { opacity: 1; transform: translateY(0); } }
            @keyframes pulseRed { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } }
            @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- START SCREEN -->
            <div id="startScreen">
                <h1>AI Interview Agent</h1>
                <p>ABTalks Cohort Enterprise Edition</p>
                <div class="toggles">
                    <label><input type="checkbox" id="voiceToggle" checked> AI Voice Output</label>
                    <label><input type="checkbox" id="timerToggle"> Pressure Timer (60s)</label>
                </div>
                <button class="start-btn" onclick="initExperience()">Start Interview</button>
            </div>

            <div id="timerBarContainer"><div id="timerFill"></div></div>

            <div class="header">
                <div class="header-left"><h2>AI Interview Agent</h2></div>
                <span class="badge" id="turnBadge">Waiting to Start</span>
            </div>
            
            <div class="chat-area" id="chatBox">
                <div class="msg-wrapper ai" id="typingIndicator" style="display: none;">
                    <div class="avatar ai-avatar">AI</div>
                    <div class="typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
                </div>
            </div>

            <div class="input-area" id="inputContainer">
                <button id="micBtn" class="icon-btn" onclick="toggleMic()">MIC</button>
                <textarea id="answerInput" placeholder="Type or speak your response..."></textarea>
                <button id="sendBtn" class="submit-btn" onclick="sendMsg()">SUBMIT</button>
            </div>
        </div>

        <script>
            const sessionId = "sess-" + Math.random().toString(36).substr(2, 9);
            let turns = 0, timerInterval, timeLeft = 60;
            let useTimer = false, useVoice = true;
            let finalReportData = "";
            let recognition;
            let isRecording = false;

            try {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if(SpeechRecognition) {
                    recognition = new SpeechRecognition();
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    recognition.onresult = (e) => {
                        document.getElementById('answerInput').value += " " + e.results[0][0].transcript;
                        toggleMic(true);
                    };
                    recognition.onerror = () => toggleMic(true);
                    recognition.onend = () => toggleMic(true);
                }
            } catch(e) { console.log("Speech API not supported."); }

            function toggleMic(forceStop = false) {
                const micBtn = document.getElementById('micBtn');
                if(!recognition) return alert("Speech recognition not supported in this browser. Please type.");
                
                if(isRecording || forceStop) {
                    try { recognition.stop(); } catch(err) {}
                    micBtn.classList.remove('recording');
                    micBtn.innerText = "MIC";
                    isRecording = false;
                } else {
                    try { recognition.start(); } catch(err) {}
                    micBtn.classList.add('recording');
                    micBtn.innerText = "REC";
                    isRecording = true;
                }
            }

            function speakText(text) {
                if(!useVoice || !window.speechSynthesis) return;
                window.speechSynthesis.cancel();
                const ut = new SpeechSynthesisUtterance(text);
                ut.rate = 1.05;
                window.speechSynthesis.speak(ut);
            }

            function startTimerCount() {
                if(!useTimer) return;
                clearInterval(timerInterval);
                timeLeft = 60;
                document.getElementById('timerBarContainer').style.display = 'block';
                document.getElementById('timerFill').style.width = '100%';
                
                timerInterval = setInterval(() => {
                    timeLeft--;
                    document.getElementById('timerFill').style.width = (timeLeft / 60 * 100) + '%';
                    if(timeLeft <= 0) {
                        clearInterval(timerInterval);
                        document.getElementById('answerInput').value = "[Time expired. Moving forward.]";
                        sendMsg();
                    }
                }, 1000);
            }

            function stopTimer() {
                clearInterval(timerInterval);
                document.getElementById('timerBarContainer').style.display = 'none';
            }

            function initExperience() {
                useVoice = document.getElementById('voiceToggle').checked;
                useTimer = document.getElementById('timerToggle').checked;
                
                document.getElementById('startScreen').style.display = 'none';
                document.getElementById('chatBox').style.display = 'flex';
                document.getElementById('inputContainer').style.display = 'flex';
                
                startInterview();
            }

          function showTyping(show) {
                const chatBox = document.getElementById('chatBox');
                let typingWrapper = document.getElementById('dynamicTyping');
                
                if (show) {
                    stopTimer();
                    if (!typingWrapper) {
                        typingWrapper = document.createElement('div');
                        typingWrapper.className = 'msg-wrapper ai';
                        typingWrapper.id = 'dynamicTyping';
                        typingWrapper.innerHTML = `
                            <div class="avatar ai-avatar">AI</div>
                            <div class="typing" style="display: flex; align-items: center; padding: 15px 22px; background: rgba(30, 41, 59, 0.8); border-radius: 20px; border-bottom-left-radius: 4px;">
                                <span class="dot"></span><span class="dot"></span><span class="dot"></span>
                            </div>`;
                        chatBox.appendChild(typingWrapper);
                    } else {
                        typingWrapper.style.display = 'flex';
                    }
                } else {
                    if (typingWrapper) {
                        typingWrapper.style.display = 'none';
                    }
                }
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            function addMessage(role, text) {
                const wrapper = document.createElement('div');
                wrapper.className = `msg-wrapper ${role}`;
                const avatar = `<div class="avatar ${role === 'ai' ? 'ai-avatar' : 'user-avatar'}">${role === 'ai' ? 'AI' : 'YOU'}</div>`;
                const msgBubble = `<div class="msg ${role}">${text}</div>`;
                wrapper.innerHTML = role === 'ai' ? avatar + msgBubble : msgBubble + avatar;
                
                const chatBox = document.getElementById('chatBox');
                chatBox.insertBefore(wrapper, document.getElementById('typingIndicator'));
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            async function startInterview() {
                showTyping(true);
                document.getElementById('turnBadge').innerText = "Connecting...";
                
                const dummyCandidate = { "id": "c-001", "completed_missions": ["RAG", "Vector Databases"], "skipped_topics": ["MCP"] };
                
                try {
                    const res = await fetch('/api/interview', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sessionId: sessionId, candidate: dummyCandidate })
                    });
                    const data = await res.json();
                    showTyping(false);
                    addMessage('ai', data.reply);
                    speakText(data.reply);
                    document.getElementById('turnBadge').innerText = "Question 1 of 8";
                    startTimerCount();
                } catch(e) { 
                    showTyping(false); 
                    addMessage('ai', "Error connecting to backend server."); 
                }
            }

            function downloadReport() {
                const blob = new Blob([finalReportData], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = 'Interview_Report.txt';
                a.click(); window.URL.revokeObjectURL(url);
            }

            function renderFeedback(feedback) {
                const wrapper = document.createElement('div');
                wrapper.className = 'msg-wrapper ai';
                
                finalReportData = `--- FINAL INTERVIEW REPORT ---\n\nSummary: ${feedback.summary}\n\nStrengths:\n- ${feedback.strengths.join('\\n- ')}\n\nGaps:\n- ${feedback.gaps.join('\\n- ')}\n\nNext Steps:\n- ${feedback.next.join('\\n- ')}`;
                
                wrapper.innerHTML = `<div class="avatar ai-avatar">AI</div>
                    <div class="feedback-card">
                        <div class="fb-title">Final Assessment Report</div>
                        <p style="color:#e2e8f0; margin-bottom:15px">${feedback.summary}</p>
                        <button class="dl-btn" onclick="downloadReport()">Download Full Report (TXT)</button>
                    </div>`;
                
                document.getElementById('chatBox').insertBefore(wrapper, document.getElementById('typingIndicator'));
                document.getElementById('chatBox').scrollTop = document.getElementById('chatBox').scrollHeight;
                stopTimer();
            }

            async function sendMsg() {
                const input = document.getElementById('answerInput');
                const btn = document.getElementById('sendBtn');
                const msg = input.value.trim();
                
                if (!msg) return;
                if(isRecording) toggleMic(true);

                addMessage('user', msg);
                input.value = '';
                btn.disabled = true;
                showTyping(true);

                try {
                    const res = await fetch('/api/interview', {
                        model: "llama-3.3-70b-versatile",
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sessionId: sessionId, message: msg })
                    });
                    const data = await res.json();
                    showTyping(false);
                    addMessage('ai', data.reply);
                    speakText(data.reply);
                    turns++;

                    if (data.done) {
                        document.getElementById('inputContainer').style.display = 'none';
                        document.getElementById('turnBadge').innerText = "Interview Completed";
                        renderFeedback(data.feedback);
                    } else {
                        document.getElementById('turnBadge').innerText = `Question ${turns + 1} of 8`;
                        btn.disabled = false;
                        input.focus();
                        startTimerCount();
                    }
                } catch (e) {
                    showTyping(false);
                    btn.disabled = false;
                }
            }
            
            document.getElementById('answerInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
            });
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
            model="llama-3.1-8b-instant",
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
                    model="llama-3.1-8b-instant",
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
                model="llama-3.1-8b-instant",
                messages=session["history"]
            )
            
            reply = response.choices[0].message.content.strip()
            session["history"].append({"role": "assistant", "content": reply})
            session["turn_count"] += 1
            
            log_to_breeth(session_id, f"AI Follow-up: {reply}")
            return {"reply": reply, "done": False}

    raise HTTPException(status_code=400, detail="Invalid request payload or session not initialized.")