# 💡 AI Collaboration & Prompt Engineering Log

This document outlines the structured prompt engineering process used to build, debug, and refine the **AI Interview Agent** for the ABTalks Hackathon in collaboration with an AI assistant.

---

## Phase 1: Core Architecture & Backend Logic
* **Goal:** Set up a robust FastAPI backend handling multi-turn interview sessions using Groq SDK (`llama-3.3-70b-versatile`) while complying with curriculum constraints and candidate profiles.
* **Prompt Used:**
  > "Design a FastAPI backend that maintains session state, ingests candidate JSON profiles (completed missions and skipped topics), and enforces the 4-day rule across an exact 8-turn technical interview. Integrate Groq API for responses."

## Phase 2: Dynamic UI & Glassmorphism Design
* **Goal:** Build a sleek, responsive, and modern frontend without heavy external frameworks.
* **Prompt Used:**
  > "Create a single-file HTML/CSS/JS frontend featuring a dark glassmorphism layout, a start screen for candidate name input, toggles for AI voice output (TTS) and a 60-second pressure timer, along with a live chat interface."

## Phase 3: Conversational Humanized Prompt Engineering
* **Goal:** Prevent the AI from sounding robotic or generating long walls of text, turning it into a realistic Senior Engineering Manager.
* **Prompt Used:**
  > "Refine the system prompt to enforce extreme brevity (max 2-3 sentences), hyper-adaptive flow (connecting the next question directly to the candidate's previous answer), and explicit question numbering (`**Question X:**`). Ensure it warmly acknowledges the candidate's specific background on turn 1."

## Phase 4: Interactive Controls (Skip & Speech-to-Text)
* **Goal:** Add robust fallback mechanisms and accessibility features for candidates during live testing.
* **Prompt Used:**
  > "Implement browser-based Web Speech API for voice recognition (MIC button) and a dedicated 'SKIP' button that records the turn as `[SKIPPED]`, triggers an AI explanation, and seamlessly moves to the next numbered question."

## Phase 5: Scoreboard & Assessment Report Generation
* **Goal:** Deliver a 100% accurate, visually rich evaluation report at the end of the 8 turns.
* **Prompt Used:**
  > "Update the final turn logic to enforce strict JSON output evaluating correct answers vs. skipped questions. Build an on-screen Scoreboard UI with dynamic color-coded tags for *Strengths*, *Gaps*, and *Next Steps*, alongside a formatted TXT download option."