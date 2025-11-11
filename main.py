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
    if ai_data:
        resp["ai"] = ai_data
    return JSONResponse(content=resp)
