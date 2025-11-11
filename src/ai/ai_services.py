from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import uuid4

# Optional integration: gemini_workflows for richer feedback if available
try:
    from src.gemini_workflows import get_gemini_response
except Exception:
    get_gemini_response = None

# Very small deterministic "AI" helpers for demo/testing. Replace with real models later.

KEYWORDS = ["python", "fastapi", "sql", "docker", "aws", "react", "lead", "machine learning", "nlp"]


def score_cv(cv_text: str) -> Dict[str, Any]:
    """Return a simple ATS-like score and human-readable feedback.
    Scoring is deterministic so tests are stable.
    """
    text = (cv_text or "").lower()
    if not text.strip():
        return {"ats_score": 10, "feedback": "CV empty or not provided.", "highlights": []}

    matches = [k for k in KEYWORDS if k in text]
    keyword_count = len(matches)
    length_score = min(100, max(10, len(text) // 10))
    keyword_score = min(100, keyword_count * 20)
    # Weighted
    ats = int((0.6 * keyword_score) + (0.4 * length_score))
    ats = max(0, min(100, ats))

    feedback_lines: List[str] = []
    if keyword_count:
        feedback_lines.append(f"Found relevant skills: {', '.join(matches)}.")
    else:
        feedback_lines.append("No strong keyword matches found. Consider highlighting technical skills.")

    if ats > 80:
        feedback_lines.append("Strong match for this role based on keywords and CV length.")
    elif ats > 50:
        feedback_lines.append("Moderate match — could be improved by including more role-specific keywords and measurable achievements.")
    else:
        feedback_lines.append("Low match — suggest tailoring the CV to the job description and adding concrete examples.")

    base = {"ats_score": ats, "feedback": " ".join(feedback_lines), "highlights": matches}
    # If gemini is available, generate a richer feedback paragraph
    if get_gemini_response:
        try:
            prompt = f"Provide a concise recruitment-style feedback for the following CV:\n\n{cv_text}\n\nInclude strengths, weaknesses, and suggested next steps in 3 short bullets."
            detailed = get_gemini_response(prompt)
            base["detailed_feedback"] = detailed
        except Exception:
            # ignore external failures, return base
            pass
    return base


def generate_oa(cv_text: str, role: str) -> Dict[str, Any]:
    """Generate a short offer/offer-assessment text and feedback based on CV and role."""
    name = "Candidate"
    # try to extract a name very naively
    lines = (cv_text or "").strip().splitlines()
    if lines:
        first = lines[0].strip()
        if len(first.split()) <= 4 and any(c.isalpha() for c in first):
            name = first

    salary_suggestion = "Competitive (depends on experience)"
    if "senior" in (cv_text or "").lower() or "lead" in (cv_text or "").lower():
        salary_suggestion = "Senior-level compensation suggested"

    offer_text = f"Dear {name},\n\nWe are pleased to invite you to join as a {role}. {salary_suggestion}.\n\nBest regards,\n{ 'Recruiting Team' }"
    feedback = "Generated offer letter template and compensation guidance." 

    return {"offer_text": offer_text, "feedback": feedback}


def generate_assessment_questions(cv_text: str, job_description: str, n: int = 5) -> List[Dict[str, Any]]:
    """Generate assessment questions tailored to the candidate CV and job description.
    If Gemini is available use it; otherwise fall back to deterministic templates.
    Returns list of {question, type} dicts.
    """
    if get_gemini_response:
        try:
            prompt = (
                f"You are an expert hiring manager. Generate {n} concise assessment questions for a candidate applying to this role."
                f" Job description:\n{job_description}\n\nCandidate CV:\n{cv_text}\n\nRespond with a JSON array of objects with keys 'question' and 'type' (coding, open-ended, technical, experience)."
            )
            resp = get_gemini_response(prompt)
            # Try to parse JSON from response; be tolerant
            import json
            try:
                parsed = json.loads(resp)
                if isinstance(parsed, list):
                    return parsed[:n]
            except Exception:
                # fallback: wrap the text into a single open-ended question
                pass
        except Exception:
            pass

    # Deterministic fallback: generate template questions from keywords
    jd = (job_description or "").lower()
    questions = []
    if "python" in jd or "fastapi" in jd:
        questions.append({"question": "Explain how you would design a FastAPI endpoint to handle file uploads and background processing.", "type": "technical"})
        questions.append({"question": "Write a short function to parse and validate JSON payloads in Python.", "type": "coding"})
    if "react" in jd or "frontend" in jd:
        questions.append({"question": "Build a React component that fetches and displays paginated data.", "type": "coding"})
        questions.append({"question": "Explain approaches to state management in a large React app.", "type": "technical"})

    # fill with generic questions
    while len(questions) < n:
        questions.append({"question": "Describe a challenging problem you solved recently and how you approached it.", "type": "open-ended"})

    return questions[:n]


def schedule_ai_interview(candidate_id: str, job_id: str, preferred_times: List[str]) -> Dict[str, Any]:
    """Return a scheduled slot and a session id for an AI conversational agent."""
    # naive scheduling: pick preferred[0] if provided, else schedule 48 hours from now at 10:00
    if preferred_times:
        scheduled = preferred_times[0]
    else:
        scheduled_dt = datetime.utcnow() + timedelta(days=2)
        scheduled = scheduled_dt.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()

    session_id = str(uuid4())
    return {"session_id": session_id, "scheduled_time": scheduled, "agent": "HR-AI-Agent"}


# Simple conversational agent mock

def ai_agent_response(session_id: str, message: str) -> str:
    m = (message or "").lower()
    if any(g in m for g in ["hello", "hi", "hey"]):
        return "Hello! I'm the HR-AI agent. How can I help with the interview or scheduling today?"
    if "schedule" in m or "available" in m:
        return "I can schedule the interview. Please provide a preferred date/time and your timezone."
    if "tell me about" in m or "feedback" in m:
        return "I can provide feedback on the candidate's CV or assessment — please upload the CV text or candidate ID."
    # default echo with helpful nudge
    return f"AI-Agent received: '{message}'. (This is a mock. In production, connect to an LLM.)"
