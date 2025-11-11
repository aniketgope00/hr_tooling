from fastapi import FastAPI, Depends, HTTPException, status, Request
import logging
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Optional, Dict, Any

# Local imports
from src.schemas import pydantic_schemas as schemas
from src.db import crud
from src.ai import ai_services

# App setup
app = FastAPI(title="AI-Powered HR Platform API")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

from fastapi import UploadFile, File
from src.db.dummy_data import init_dummy_data
import os
import tempfile
from pathlib import Path
import traceback

# PDF extraction - prefer PyPDF2 when available
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

# Initialize dummy data on startup
init_dummy_data()

# --- Hard-coded test credentials (simple demo mode) ---
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass"
TEST_TOKEN = "test-token-123"
TEST_USER = {
    "id": "test-user-1",
    "email": TEST_EMAIL,
    "full_name": "Test User",
    "org_id": "test-org-1",
    "is_active": True,
    "created_at": datetime.utcnow().isoformat(),
}

# Utility password helpers (in-memory demo)

def verify_password(plain_password: str, stored_password: Optional[str]) -> bool:
    if stored_password is None:
        return False
    return plain_password == stored_password


def hash_password(password: str) -> str:
    return password


# Authentication dependency
async def get_current_user(token: str = Depends(oauth2_scheme)) -> schemas.User:
    """Resolve token to a user. For demo: accept TEST_TOKEN or a user id stored in DB."""
    # Demo token path
    if token == TEST_TOKEN:
        return schemas.User(**TEST_USER)

    # Fallback: treat token as user id (legacy test behavior)
    user_data = crud.get_user_by_id(token)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials or token")
    if not user_data.get("is_active"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return schemas.User(**user_data)


# --- HTML pages ---
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def get_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse, include_in_schema=False)
async def get_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# --- Auth endpoints ---
@app.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate):
    logger.info(f"Registration attempt for email: {user.email}")
    if crud.get_user_by_email(user.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = hash_password(user.password)
    user_data = user.model_dump()
    user_data["password"] = hashed_password
    org_name = user_data.pop("org_name", None)
    if org_name:
        org_id = str(uuid4())
        crud.DATABASE.setdefault("organizations", {})
        crud.DATABASE["organizations"][org_id] = {"id": org_id, "name": org_name, "hr_contact_email": user.email}
        user_data["org_id"] = org_id
    db_user = crud.create_user(user_data)
    # sanitize
    result = dict(db_user)
    result.pop("password", None)
    result.pop("updated_at", None)
    return schemas.User(**result)
    from fastapi import UploadFile, File
    from src.db.dummy_data import init_dummy_data


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    """Simple login: accept the hard-coded test credentials or any user in the in-memory DB.
    Returns a demo access token string that the front-end uses as 'Bearer'.
    
    Also handles non-JS fallback: redirects to /dashboard if the accept header suggests HTML is wanted.
    """
    logger.info(f"Login attempt for username: {form_data.username}")

    # first: test credentials
    if form_data.username == TEST_EMAIL and form_data.password == TEST_PASSWORD:
        token_data = {"access_token": TEST_TOKEN, "token_type": "bearer"}
        # Check if this is a form submission (non-JS fallback) - redirect if so
        if request:
            accept = request.headers.get("accept", "").lower()
            if "text/html" in accept or not accept:
                # This is likely a form submission, redirect after setting cookie
                response = RedirectResponse(url="/dashboard", status_code=303)
                response.set_cookie(key="access_token", value=TEST_TOKEN, max_age=86400)
                return response
        return token_data

    # fallback: check DB user and plain equality password
    user = crud.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.get("password")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})

    # return user id as token for legacy compatibility
    token_data = {"access_token": user["id"], "token_type": "bearer"}
    if request:
        accept = request.headers.get("accept", "").lower()
        if "text/html" in accept or not accept:
            response = RedirectResponse(url="/dashboard", status_code=303)
            response.set_cookie(key="access_token", value=user["id"], max_age=86400)
            return response
    return token_data


@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user


# --- Job posts (owners) ---
@app.post("/jobs", response_model=schemas.JobPost, status_code=status.HTTP_201_CREATED)
def create_job(job: schemas.JobPostCreate, current_user: schemas.User = Depends(get_current_user)):
    db_job_data = crud.create_job_post(job.model_dump(), current_user.org_id)
    return schemas.JobPost(**db_job_data)


@app.get("/jobs", response_model=List[schemas.JobPost])
def read_jobs(current_user: schemas.User = Depends(get_current_user)):
    jobs_data = crud.get_all_job_posts(current_user.org_id)
    return [schemas.JobPost(**job) for job in jobs_data]


@app.get("/jobs/{job_id}", response_model=schemas.JobPost)
def read_job(job_id: str, current_user: schemas.User = Depends(get_current_user)):
    db_job_data = crud.get_job_post(job_id)
    if not db_job_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job post not found")
    if db_job_data.get("org_id") != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to job post")
    return schemas.JobPost(**db_job_data)


@app.post("/jobs/{job_id}/activate")
def activate_job(job_id: str, current_user: schemas.User = Depends(get_current_user)):
    """Activate a job post (demo helper)."""
    db_job = crud.get_job_post(job_id)
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if db_job.get("org_id") != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    updated = crud.update_job_post(job_id, {"status": schemas.JobStatus.ACTIVE.value})
    return schemas.JobPost(**updated)


# --- Public application + AI feedback/ATS scoring ---
@app.post("/jobs/{job_id}/apply_public")
def apply_public(job_id: str, payload: Dict[str, Any]):
    """Public application endpoint that returns AI feedback & ATS score.
    Expects payload: {"full_name":..., "email":..., "cv_text": "..."}
    """
    job = crud.get_job_post(job_id)
    if not job or job.get("status") != schemas.JobStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or inactive Job Post ID")

    cv_text = payload.get("cv_text", "")
    candidate_data = {"full_name": payload.get("full_name"), "email": payload.get("email"), "job_post_id": job_id, "cv_text": cv_text}
    db_candidate = crud.create_candidate(candidate_data, job_id)

    # Run AI scoring
    ai_result = ai_services.score_cv(cv_text)

    # Attach AI result to candidate record (in-memory)
    crud.DATABASE.setdefault("candidates_ai", {})
    crud.DATABASE["candidates_ai"][db_candidate["id"]] = ai_result

    # sanitize datetime fields for JSON transport
    def _sanitize(obj):
        for k, v in list(obj.items()):
            if hasattr(v, 'isoformat'):
                obj[k] = v.isoformat()
        return obj

    resp_candidate = _sanitize(dict(db_candidate))
    response = {"candidate": resp_candidate, "ai": ai_result}
    return JSONResponse(content=response)


@app.post("/ai/generate_oa")
def generate_oa(payload: Dict[str, Any], current_user: Optional[schemas.User] = Depends(get_current_user)):
    """Generate an offer (OA) for a candidate based on their CV and the role.
    Payload: {"candidate_id": ..., "role": "..."} OR {"cv_text": ..., "role": "..."}
    """
    candidate_id = payload.get("candidate_id")
    role = payload.get("role", "")
    cv_text = payload.get("cv_text")

    if candidate_id:
        cand = crud.get_candidate(candidate_id)
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate not found")
        cv_text = cv_text or cand.get("cv_text", "")

    if not cv_text:
        raise HTTPException(status_code=400, detail="cv_text is required either directly or via candidate_id")

    oa = ai_services.generate_oa(cv_text, role)
    return JSONResponse(content=oa)


@app.post("/ai/schedule_interview")
def schedule_interview(payload: Dict[str, Any], current_user: Optional[schemas.User] = Depends(get_current_user)):
    """Schedule an interview with an AI conversational agent. Payload: {candidate_id, job_id, preferred_times: [..]}
    Returns session info and scheduled time.
    """
    candidate_id = payload.get("candidate_id")
    job_id = payload.get("job_id")
    preferred = payload.get("preferred_times", [])

    if not candidate_id or not job_id:
        raise HTTPException(status_code=400, detail="candidate_id and job_id are required")

    session = ai_services.schedule_ai_interview(candidate_id, job_id, preferred)
    return JSONResponse(content=session)


@app.post("/ai/agent/{session_id}/message")
def ai_agent_message(session_id: str, payload: Dict[str, Any]):
    """Send a message to the AI conversational agent for a session and receive a reply."""
    message = payload.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    reply = ai_services.ai_agent_response(session_id, message)
    return JSONResponse(content={"reply": reply})


# Keep candidate retrieval endpoints for owners
@app.get("/jobs/{job_id}/candidates", response_model=List[schemas.Candidate])
def get_candidates_for_job(job_id: str, current_user: schemas.User = Depends(get_current_user)):
    db_job = crud.get_job_post(job_id)
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job post not found")
    if db_job.get("org_id") != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to view candidates for this job")
    candidates_data = crud.get_candidates_by_job(job_id)
    return [schemas.Candidate(**c) for c in candidates_data]


@app.get("/candidates/{candidate_id}")
def get_candidate_details(candidate_id: str, current_user: schemas.User = Depends(get_current_user)):
    db_candidate = crud.get_candidate(candidate_id)
    if not db_candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    db_job = crud.get_job_post(db_candidate.get("job_post_id", ""))
    if not db_job or db_job.get("org_id") != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to view this candidate")
    # include any ai data if present
    ai_data = crud.DATABASE.get("candidates_ai", {}).get(candidate_id)
    resp = dict(db_candidate)
    
    # Sanitize datetime fields
    def _sanitize(obj):
        result = {}
        for k, v in obj.items():
            if hasattr(v, 'isoformat'):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result
    
    resp = _sanitize(resp)
    if ai_data:
        resp["ai"] = ai_data
    return JSONResponse(content=resp)

# === CV Upload and Analysis ===
@app.post("/candidates/{job_id}/upload_cv")
async def upload_cv(job_id: str, file: UploadFile = File(...), full_name: str = "", email: str = "", current_user: Optional[schemas.User] = Depends(get_current_user)):
    """Upload a CV file for a candidate applying to a job. 
    Analyzes fit against job description and returns ATS score + feedback.
    """
    job = crud.get_job_post(job_id)
    if not job or job.get("status") != schemas.JobStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or inactive job posting")
    
    # Save uploaded file to a dedicated uploads directory (persistent for demo)
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    try:
        contents = await file.read()
        # sanitize filename
        filename = Path(file.filename or "upload").name
        unique_name = f"{uuid4().hex}_{filename}"
        saved_path = uploads_dir / unique_name
        with open(saved_path, "wb") as fh:
            fh.write(contents)

        # Try to extract text. If PDF and PyPDF2 is available, use it.
        cv_text = ""
        try:
            lower = filename.lower()
            is_pdf = lower.endswith(".pdf") or (contents[:4] == b"%PDF")
            if is_pdf and PyPDF2 is not None:
                try:
                    reader = PyPDF2.PdfReader(str(saved_path))
                    pages = []
                    for p in reader.pages:
                        try:
                            pages.append(p.extract_text() or "")
                        except Exception:
                            # best-effort per-page extraction
                            pages.append("")
                    cv_text = "\n\n".join(pages).strip()
                except Exception:
                    # fallback to binary->text best effort
                    cv_text = contents.decode("utf-8", errors="ignore")
            else:
                # Try decode as utf-8 otherwise fall back to ignore errors
                cv_text = contents.decode("utf-8", errors="ignore")
        except Exception:
            cv_text = contents.decode("utf-8", errors="ignore")

    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("Failed to save or read uploaded file")
        raise HTTPException(status_code=400, detail=f"Error saving or reading uploaded file: {str(e)}\n{tb}")

    # Compose candidate record and persist (store resume_url)
    candidate_data = {
        "full_name": full_name or f"Candidate {uuid4().hex[:8]}",
        "email": email or f"candidate+{uuid4().hex[:8]}@applicant.local",
        "job_post_id": job_id,
        "cv_text": cv_text,
        "resume_url": str(saved_path),
        "stage": "APPLIED",
        "application_date": datetime.now(),
    }
    db_candidate = crud.create_candidate(candidate_data, job_id)

    # Run AI analysis using the job description + extracted CV text (so Gemini gets both)
    job_desc = job.get("description", "")
    prompt_text = f"Job Description:\n{job_desc}\n\nCV Text:\n{cv_text}"
    ai_result = ai_services.score_cv(prompt_text)

    # Persist AI result as a screening_result record and in quick-access map
    screening = {
        "candidate_id": db_candidate["id"],
        "job_id": job_id,
        "ats_score": ai_result.get("ats_score"),
        "feedback": ai_result.get("feedback", ""),
        "detailed_feedback": ai_result.get("detailed_feedback"),
        "created_at": datetime.now(),
    }
    crud.create_screening_result(screening)
    crud.DATABASE.setdefault("candidates_ai", {})
    crud.DATABASE["candidates_ai"][db_candidate["id"]] = ai_result

    # Update candidate record in-place to set resume_url and cv_text (simple in-memory update)
    try:
        cand = crud.get_candidate(db_candidate["id"])
        if cand:
            cand["resume_url"] = str(saved_path)
            cand["cv_text"] = cv_text
            cand["updated_at"] = datetime.now()
            crud.DATABASE["candidates"][cand["id"]] = cand
    except Exception:
        logger.exception("Failed to update candidate with resume_url")

    def _sanitize(obj):
        result = {}
        for k, v in obj.items():
            if hasattr(v, 'isoformat'):
                result[k] = v.isoformat()
            elif k == 'cv_text' and v and len(v) > 500:
                # Include first 500 chars in response for preview; full text available via candidate API
                result[k] = v[:500] + "...[truncated for API response]"
            else:
                result[k] = v
        return result

    resp_candidate = _sanitize(dict(db_candidate))
    return JSONResponse(content={"candidate": resp_candidate, "ai": ai_result})


@app.post("/candidates/{candidate_id}/schedule_oa")
def schedule_oa(candidate_id: str, num_questions: int = 5, current_user: Optional[schemas.User] = Depends(get_current_user)):
    """Generate an online assessment (OA) for a candidate, store it and simulate sending by email.
    Returns assessment record with completion link. This uses Gemini (if available) via ai_services.generate_assessment_questions.
    """
    cand = crud.get_candidate(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    job = crud.get_job_post(cand.get("job_post_id"))
    if not job or job.get("org_id") != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied to generate OA for this candidate")

    cv_text = cand.get("cv_text", "")
    job_desc = job.get("description", "")
    questions = ai_services.generate_assessment_questions(cv_text, job_desc, n=num_questions)

    assessment_data = {
        "candidate_id": candidate_id,
        "job_id": job.get("id"),
        "generated_questions": questions,
        "status": "SENT",
    }
    assessment = crud.create_assessment(assessment_data)

    # update candidate stage
    crud.update_candidate_stage(candidate_id, "ASSESSMENT_SENT")

    # Simulate sending an email by logging. In production, integrate SMTP/transactional email service.
    org = crud.get_organization_by_id(job.get("org_id")) or {}
    hr_email = org.get("hr_contact_email") or "hr@example.local"
    logger.info(f"Simulated email: Sent OA to {cand.get('email')} (from {hr_email}) with link {assessment.get('completion_link')}")

    # Sanitize datetime fields for JSON response
    def _sanitize_assessment(obj):
        result = {}
        for k, v in obj.items():
            if hasattr(v, 'isoformat'):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result

    resp_assessment = _sanitize_assessment(dict(assessment))
    return JSONResponse(content={"assessment": resp_assessment})

# === Analytics & Metrics ===
@app.get("/analytics/summary")
def get_analytics_summary(current_user: schemas.User = Depends(get_current_user)):
    """Return summary analytics for the organization."""
    org_id = current_user.org_id
    
    # Get all jobs and candidates for org
    all_jobs = crud.get_all_job_posts(org_id)
    active_jobs = [j for j in all_jobs if j.get("status") == schemas.JobStatus.ACTIVE.value]
    
    total_candidates = 0
    candidates_by_stage = {}
    avg_ats_score = 0
    all_scores = []
    
    for job in all_jobs:
        candidates = crud.get_candidates_by_job(job["id"])
        total_candidates += len(candidates)
        for cand in candidates:
            stage = cand.get("stage", "APPLIED")
            candidates_by_stage[stage] = candidates_by_stage.get(stage, 0) + 1
            
            # Get AI score if available
            ai_data = crud.DATABASE.get("candidates_ai", {}).get(cand["id"])
            if ai_data and "ats_score" in ai_data:
                all_scores.append(ai_data["ats_score"])
    
    if all_scores:
        avg_ats_score = sum(all_scores) / len(all_scores)
    
    # Count assessments and interviews
    assessments = len(crud.DATABASE.get("assessments", {}))
    interviews = len(crud.DATABASE.get("interviews", {}))
    
    return JSONResponse(content={
        "total_jobs": len(all_jobs),
        "active_jobs": len(active_jobs),
        "total_candidates": total_candidates,
        "candidates_by_stage": candidates_by_stage,
        "avg_ats_score": round(avg_ats_score, 2),
        "assessments_sent": assessments,
        "interviews_scheduled": interviews,
    })

@app.get("/analytics/jobs/{job_id}")
def get_job_analytics(job_id: str, current_user: schemas.User = Depends(get_current_user)):
    """Get detailed analytics for a specific job posting."""
    job = crud.get_job_post(job_id)
    if not job or job.get("org_id") != current_user.org_id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidates = crud.get_candidates_by_job(job_id)
    candidates_by_stage = {}
    scores_distribution = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
    top_candidates = []
    
    for cand in candidates:
        stage = cand.get("stage", "APPLIED")
        candidates_by_stage[stage] = candidates_by_stage.get(stage, 0) + 1
        
        ai_data = crud.DATABASE.get("candidates_ai", {}).get(cand["id"])
        if ai_data:
            score = ai_data.get("ats_score", 0)
            if score <= 25:
                scores_distribution["0-25"] += 1
            elif score <= 50:
                scores_distribution["26-50"] += 1
            elif score <= 75:
                scores_distribution["51-75"] += 1
            else:
                scores_distribution["76-100"] += 1
            
            top_candidates.append({
                "id": cand["id"],
                "name": cand.get("full_name"),
                "email": cand.get("email"),
                "stage": stage,
                "ats_score": score,
            })
    
    top_candidates = sorted(top_candidates, key=lambda x: x["ats_score"], reverse=True)[:10]
    
    return JSONResponse(content={
        "job_title": job.get("title"),
        "job_status": job.get("status"),
        "total_applications": len(candidates),
        "candidates_by_stage": candidates_by_stage,
        "score_distribution": scores_distribution,
        "top_candidates": top_candidates,
    })

@app.get("/analytics/hiring_funnel")
def get_hiring_funnel(current_user: schemas.User = Depends(get_current_user)):
    """Get hiring pipeline funnel for the organization."""
    org_id = current_user.org_id
    all_jobs = crud.get_all_job_posts(org_id)
    
    funnel = {
        "applied": 0,
        "screening_passed": 0,
        "assessment_sent": 0,
        "assessment_completed": 0,
        "interview_scheduled": 0,
        "offer_extended": 0,
        "hired": 0,
    }
    
    for job in all_jobs:
        candidates = crud.get_candidates_by_job(job["id"])
        for cand in candidates:
            stage = cand.get("stage", "APPLIED").upper()
            if stage == "APPLIED":
                funnel["applied"] += 1
            elif stage == "SCREENING_PASSED":
                funnel["screening_passed"] += 1
            elif stage == "ASSESSMENT_SENT":
                funnel["assessment_sent"] += 1
            elif stage == "ASSESSMENT_COMPLETED":
                funnel["assessment_completed"] += 1
            elif stage == "INTERVIEW_SCHEDULED":
                funnel["interview_scheduled"] += 1
            elif stage == "OFFER_EXTENDED":
                funnel["offer_extended"] += 1
            elif stage == "HIRED":
                funnel["hired"] += 1
    
    return JSONResponse(content=funnel)
