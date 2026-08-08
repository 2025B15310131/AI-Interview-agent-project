import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from groq import Groq
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
BREETH_API_KEY = os.environ.get("BREETH_API_KEY")

sessions = {}

class CandidateProfile(BaseModel):
    id: str
    name: Optional[str] = "Candidate"
    completed_missions: List[str]
    skipped_topics: List[str]

class InterviewRequest(BaseModel):
    sessionId: str
    candidate: Optional[CandidateProfile] = None
    message: Optional[str] = None

class InterviewResponse(BaseModel):
    reply: str
    done: bool
    feedback: Optional[dict] = None

def log_to_breeth(session_id: str, message: str):
    if not BREETH_API_KEY:
        return
    try:
        requests.post(
            "https://api.breeth.ai/v1/logs",
            headers={"Authorization": f"Bearer {BREETH_API_KEY}"},
            json={"session_id": session_id, "message": message},
            timeout=2
        )
    except Exception:
        pass

@app.post("/api/interview", response_model=InterviewResponse)
def handle_interview(req: InterviewRequest):
    session_id = req.sessionId
    
    if req.candidate is not None:
        try:
            with open("curriculum.json", "r") as f:
                curriculum_data = json.load(f)
        except Exception:
            curriculum_data = "Curriculum data missing."

        system_prompt = f"""You are a friendly, highly experienced Senior Engineering Manager at a top-tier tech company conducting a live technical interview.
        Candidate Name: {req.candidate.name}
        Profile: {json.dumps(req.candidate.dict())}
        Course Curriculum: {json.dumps(curriculum_data)}
        
        CRITICAL RULES FOR A WINNING INTERVIEW:
        1. THE WARM INTRO (TURN 1): Start by warmly welcoming the candidate by name. Briefly praise their specific background (e.g., mention their completed missions). Make them feel valued before starting.
        2. EXPLICIT NUMBERING: You MUST prefix every single question with **Question X:** (e.g., **Question 1:**). This is mandatory for formatting.
        3. EXTREME BREVITY: Keep your feedback to their previous answer short (1-2 sentences). Then ask the next question.
        4. HYPER-ADAPTIVE: Your next question MUST directly connect to their previous answer.
        5. SKIPPED QUESTIONS: If they say "[SKIPPED]", reply "No worries, let's pivot." and ask the next numbered question.
        """

        sessions[session_id] = {
            "turn_count": 1, # Start at 1 for Question 1
            "candidate": req.candidate,
            "history": [{"role": "system", "content": system_prompt}]
        }
        
        # 🚀 TRICK: Force the AI to introduce the candidate and ask Question 1
        initial_instruction = f"Hi, my name is {req.candidate.name}. Let's start the interview. Please introduce yourself, acknowledge my specific background from my profile, and then vividly write '**Question 1:**' to ask your first question."
        sessions[session_id]["history"].append({"role": "user", "content": initial_instruction})
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=sessions[session_id]["history"],
            temperature=0.7
        )
        
        reply = response.choices[0].message.content.strip()
        sessions[session_id]["history"].append({"role": "assistant", "content": reply})
        sessions[session_id]["turn_count"] += 1
        
        log_to_breeth(session_id, f"Interview Started. AI Asked: {reply}")
        return {"reply": reply, "done": False}

    if req.message and session_id in sessions:
        session = sessions[session_id]
        
        # 🚀 TRICK: Hidden prompt injection to force "Question X:" styling without the user seeing it
        if session["turn_count"] <= 8:
            hidden_instruction = f"\n\n(System Instruction: Briefly evaluate my answer above. Then, explicitly write '**Question {session['turn_count']}:**' and ask your next adaptive technical question.)"
            session["history"].append({"role": "user", "content": req.message + hidden_instruction})
        else:
            session["history"].append({"role": "user", "content": req.message})
            
        log_to_breeth(session_id, f"Candidate Answered: {req.message}")

        if session["turn_count"] > 8:
            feedback_prompt = """The interview is now complete. Act as an Engineering Hiring Committee. You MUST meticulously analyze the candidate's exact answers from the 8 turns. 
            Evaluate how many questions they answered correctly, incorrectly, or skipped (where they literally said "[SKIPPED]").
            
            Output ONLY a valid JSON object with EXACTLY these keys:
            - "score": A string like "6/8" representing their overall score.
            - "correct_count": Integer representing how many technical answers were largely correct.
            - "skipped_count": Integer representing how many times they explicitly skipped a question.
            - "summary": A 2-3 sentence honest assessment of their real performance today.
            - "strengths": Array of specific technical concepts they actually demonstrated well (keep concise, 3-5 words each).
            - "gaps": Array of specific areas where they hesitated or lacked depth (keep concise, 3-5 words each).
            - "next": Array of 2-3 concrete steps they should take to improve based on their gaps.
            """
            
            session["history"].append({"role": "system", "content": feedback_prompt})
            
            try:
                feedback_res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=session["history"],
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
                feedback_data = json.loads(feedback_res.choices[0].message.content)
            except Exception:
                feedback_data = {
                    "score": "0/8", "correct_count": 0, "skipped_count": 0,
                    "summary": "Completed the technical interview, demonstrating a functional understanding of core concepts.",
                    "strengths": ["Clear communication"], 
                    "gaps": ["Technical edge-cases"], 
                    "next": ["Review advanced architecture patterns"]
                }
            
            final_reply = "Awesome, that wraps up all 8 questions for today! You did a great job navigating those concepts. I've compiled a detailed evaluation report and your final score below."
            log_to_breeth(session_id, "Interview Completed. Feedback Generated.")
            
            return {"reply": final_reply, "done": True, "feedback": feedback_data}
            
        else:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=session["history"],
                temperature=0.6
            )
            
            reply = response.choices[0].message.content.strip()
            session["history"].append({"role": "assistant", "content": reply})
            session["turn_count"] += 1
            
            log_to_breeth(session_id, f"AI Follow-up: {reply}")
            return {"reply": reply, "done": False}

    raise HTTPException(status_code=400, detail="Invalid request payload.")

# --- FRONTEND UI ---
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
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
            body { background: radial-gradient(circle at top left, #0f172a, #020617); color: #f8fafc; height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
            .container { background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; width: 100%; max-width: 900px; height: 92vh; display: flex; flex-direction: column; box-shadow: 0 30px 60px rgba(0,0,0,0.6); overflow: hidden; position: relative; }
            #startScreen { position: absolute; inset: 0; background: #0f172a; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 50; padding: 20px; text-align: center; }
            #startScreen h1 { font-size: 32px; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }
            #startScreen p { color: #94a3b8; margin-bottom: 25px; font-size: 16px; }
            .name-input { width: 100%; max-width: 320px; padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.05); color: white; font-size: 16px; outline: none; margin-bottom: 20px; text-align: center; }
            .name-input:focus { border-color: #38bdf8; }
            .toggles { display: flex; gap: 20px; margin-bottom: 30px; background: rgba(255,255,255,0.05); padding: 15px 25px; border-radius: 12px; }
            .toggles label { display: flex; align-items: center; gap: 10px; cursor: pointer; font-weight: 500; color: #cbd5e1; font-size: 14px; }
            .toggles input[type="checkbox"] { width: 18px; height: 18px; cursor: pointer; accent-color: #0ea5e9; }
            .start-btn { background: linear-gradient(90deg, #10b981, #059669); color: white; border: none; font-weight: 600; font-size: 18px; padding: 15px 40px; border-radius: 30px; box-shadow: 0 10px 20px rgba(16, 185, 129, 0.3); cursor: pointer; transition: 0.3s; }
            .start-btn:hover { transform: translateY(-3px); }
            #timerBarContainer { height: 4px; background: rgba(255,255,255,0.1); width: 100%; display: none; }
            #timerFill { height: 100%; width: 100%; background: #ef4444; transition: width 1s linear; }
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
            .msg { max-width: 85%; padding: 16px 22px; font-size: 15px; line-height: 1.6; border-radius: 20px; color: #f1f5f9; }
            .msg.ai { background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(255,255,255,0.05); border-bottom-left-radius: 4px; }
            .msg.ai strong { color: #38bdf8; font-weight: 600; }
            .msg.user { background: linear-gradient(135deg, #0284c7, #2563eb); border-bottom-right-radius: 4px; color: white; }
            .input-area { padding: 20px 30px; background: rgba(15, 23, 42, 0.8); border-top: 1px solid rgba(255, 255, 255, 0.08); display: none; gap: 10px; align-items: center; }
            textarea { flex: 1; background: rgba(0, 0, 0, 0.2); color: #f8fafc; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 16px 20px; font-size: 15px; outline: none; resize: none; height: 55px; }
            
            .icon-btn { background: #1e293b; border: 1px solid rgba(255,255,255,0.1); color: white; width: 55px; height: 55px; border-radius: 14px; font-size: 12px; cursor: pointer; transition: 0.3s; display: flex; justify-content: center; align-items: center; font-weight: 700; }
            .icon-btn:hover { background: #334155; }
            .icon-btn.recording { background: #ef4444; animation: pulseRed 1.5s infinite; border: none; }
            .skip-btn { background: #475569; }
            .skip-btn:hover { background: #64748b; }
            
            .submit-btn { background: linear-gradient(90deg, #0ea5e9, #6366f1); color: white; border: none; padding: 0 25px; height: 55px; border-radius: 14px; font-size: 15px; font-weight: 600; cursor: pointer; transition: 0.3s; }
            button:disabled { opacity: 0.5; cursor: not-allowed; }
            .dot { display: inline-block; width: 6px; height: 6px; background: #94a3b8; border-radius: 50%; margin: 0 3px; animation: bounce 1.4s infinite ease-in-out both; }
            .dot:nth-child(1) { animation-delay: -0.32s; }
            .dot:nth-child(2) { animation-delay: -0.16s; }
            
            .feedback-card { background: linear-gradient(145deg, #1e293b, #0f172a); border: 1px solid #38bdf8; border-radius: 20px; padding: 30px; margin-top: 10px; width: 100%; max-width: 650px; }
            .fb-title { font-size: 24px; font-weight: 700; color: #38bdf8; margin-bottom: 20px; text-align: center; }
            
            .score-board { display: flex; gap: 15px; margin-bottom: 25px; }
            .score-card { flex: 1; padding: 15px; border-radius: 14px; text-align: center; }
            .score-card.primary { background: rgba(14, 165, 233, 0.15); border: 1px solid rgba(14, 165, 233, 0.3); color: #38bdf8; }
            .score-card.success { background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; }
            .score-card.danger { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; }
            .score-value { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
            .score-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; opacity: 0.9; }

            .report-section { margin-top: 20px; }
            .report-section h3 { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
            .tag-container { display: flex; flex-wrap: wrap; gap: 8px; }
            .tag { padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; }
            .tag-strength { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
            .tag-gap { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
            .tag-next { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
            
            .dl-btn { background: #0ea5e9; color: white; border: none; padding: 14px 20px; border-radius: 12px; cursor: pointer; font-weight: 600; margin-top: 30px; width: 100%; transition: 0.3s; display: flex; justify-content: center; align-items: center; gap: 8px;}
            .dl-btn:hover { background: #0284c7; }
            
            @keyframes slideUp { to { opacity: 1; transform: translateY(0); } }
            @keyframes pulseRed { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } }
            @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        </style>
    </head>
    <body>
        <div class="container">
            <div id="startScreen">
                <h1>AI Interview Agent</h1>
                <p>ABTalks Cohort Enterprise Edition</p>
                <input type="text" id="candidateName" class="name-input" placeholder="Enter your full name">
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
            <div class="chat-area" id="chatBox"></div>
            <div class="input-area" id="inputContainer">
                <button id="micBtn" class="icon-btn" onclick="toggleMic()">MIC</button>
                <button id="skipBtn" class="icon-btn skip-btn" onclick="skipQuestion()">SKIP</button>
                <textarea id="answerInput" placeholder="Type or speak your response..."></textarea>
                <button id="sendBtn" class="submit-btn" onclick="sendMsg()">SUBMIT</button>
            </div>
        </div>

        <script>
            const sessionId = "sess-" + Math.random().toString(36).substr(2, 9);
            let turns = 0, timerInterval, timeLeft = 60;
            let useTimer = false, useVoice = true;
            let candidateName = "Candidate";
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
            } catch(e) {}

            function toggleMic(forceStop = false) {
                const micBtn = document.getElementById('micBtn');
                if(!recognition) return alert("Speech recognition not supported.");
                
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
                const cleanText = text.replace(/\\*\\*/g, '').replace(/\\*/g, '');
                const ut = new SpeechSynthesisUtterance(cleanText);
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
                const nameField = document.getElementById('candidateName').value.trim();
                if(nameField) candidateName = nameField;

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
                            <div class="msg ai" style="display: flex; align-items: center; gap: 4px; padding: 16px 22px;">
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
                const chatBox = document.getElementById('chatBox');
                const typingWrapper = document.getElementById('dynamicTyping');
                if(typingWrapper) typingWrapper.style.display = 'none';

                const wrapper = document.createElement('div');
                wrapper.className = `msg-wrapper ${role}`;
                const avatar = `<div class="avatar ${role === 'ai' ? 'ai-avatar' : 'user-avatar'}">${role === 'ai' ? 'AI' : 'YOU'}</div>`;
                
                const displayTxt = text === "[SKIPPED]" ? "<i>User skipped this question</i>" : text;
                const formattedText = role === 'ai' ? marked.parse(displayTxt) : displayTxt;
                
                const msgBubble = `<div class="msg ${role}">${formattedText}</div>`;
                wrapper.innerHTML = role === 'ai' ? avatar + msgBubble : msgBubble + avatar;
                
                chatBox.appendChild(wrapper);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            async function startInterview() {
                showTyping(true);
                document.getElementById('turnBadge').innerText = "Connecting...";
                
                const candidateProfile = { "id": "c-001", "name": candidateName, "completed_missions": ["RAG", "Vector Databases"], "skipped_topics": ["MCP"] };
                
                try {
                    const res = await fetch('/api/interview', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sessionId: sessionId, candidate: candidateProfile })
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

            function skipQuestion() {
                document.getElementById('answerInput').value = "[SKIPPED]";
                sendMsg();
            }

            function downloadReport() {
                const blob = new Blob([finalReportData], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = `${candidateName.replace(/ /g, '_')}_Interview_Report.txt`;
                a.click(); window.URL.revokeObjectURL(url);
            }

            function renderFeedback(feedback) {
                const chatBox = document.getElementById('chatBox');
                const wrapper = document.createElement('div');
                wrapper.className = 'msg-wrapper ai';
                
                // Construct text for download
                finalReportData = `--- FINAL INTERVIEW REPORT FOR ${candidateName.toUpperCase()} ---\n\nSCORE: ${feedback.score} (Correct: ${feedback.correct_count} | Skipped: ${feedback.skipped_count})\n\nSummary:\n${feedback.summary}\n\nStrengths:\n- ${feedback.strengths.join('\\n- ')}\n\nGaps:\n- ${feedback.gaps.join('\\n- ')}\n\nActionable Next Steps:\n- ${feedback.next.join('\\n- ')}`;
                
                // Construct HTML tags for UI
                const strengthsHtml = feedback.strengths.map(s => `<span class="tag tag-strength">${s}</span>`).join('');
                const gapsHtml = feedback.gaps.map(g => `<span class="tag tag-gap">${g}</span>`).join('');
                const nextHtml = feedback.next.map(n => `<span class="tag tag-next">${n}</span>`).join('');

                wrapper.innerHTML = `
                    <div class="avatar ai-avatar">AI</div>
                    <div class="feedback-card">
                        <div class="fb-title">Performance Report</div>
                        
                        <div class="score-board">
                            <div class="score-card primary">
                                <div class="score-value">${feedback.score}</div>
                                <div class="score-label">Final Score</div>
                            </div>
                            <div class="score-card success">
                                <div class="score-value">${feedback.correct_count}</div>
                                <div class="score-label">Correct</div>
                            </div>
                            <div class="score-card danger">
                                <div class="score-value">${feedback.skipped_count}</div>
                                <div class="score-label">Skipped</div>
                            </div>
                        </div>

                        <p style="color:#e2e8f0; font-size: 15px; line-height: 1.6;">${feedback.summary}</p>
                        
                        <div class="report-section">
                            <h3>Demonstrated Strengths</h3>
                            <div class="tag-container">${strengthsHtml}</div>
                        </div>

                        <div class="report-section">
                            <h3>Areas for Improvement</h3>
                            <div class="tag-container">${gapsHtml}</div>
                        </div>

                        <div class="report-section">
                            <h3>Actionable Next Steps</h3>
                            <div class="tag-container">${nextHtml}</div>
                        </div>

                        <button class="dl-btn" onclick="downloadReport()">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                            Download Full Report
                        </button>
                    </div>`;
                
                chatBox.appendChild(wrapper);
                chatBox.scrollTop = chatBox.scrollHeight;
                stopTimer();
            }

            async function sendMsg() {
                const input = document.getElementById('answerInput');
                const btn = document.getElementById('sendBtn');
                const skipBtn = document.getElementById('skipBtn');
                const msg = input.value.trim();
                
                if (!msg) return;
                if(isRecording) toggleMic(true);

                addMessage('user', msg);
                input.value = '';
                btn.disabled = true;
                skipBtn.disabled = true;
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
                    speakText(data.reply);
                    turns++;

                    if (data.done) {
                        document.getElementById('inputContainer').style.display = 'none';
                        document.getElementById('turnBadge').innerText = "Interview Completed";
                        renderFeedback(data.feedback);
                    } else {
                        document.getElementById('turnBadge').innerText = `Question ${turns + 1} of 8`;
                        btn.disabled = false;
                        skipBtn.disabled = false;
                        input.focus();
                        startTimerCount();
                    }
                } catch (e) {
                    showTyping(false);
                    btn.disabled = false;
                    skipBtn.disabled = false;
                }
            }
            
            document.getElementById('answerInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
            });
        </script>
    </body>
    </html>
    """