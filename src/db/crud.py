from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

# Assuming the Pydantic schemas are available via the 'schemas' import
# from . import schemas # Use if in a larger package structure
# For this self-contained example, we'll just use Dict and Any for data structures.

# --- Simulated In-Memory Database Collections ---
# In a real application, these would be calls to Firestore, MongoDB, etc.
DATABASE: Dict[str, Dict[str, Dict[str, Any]]] = {
    "users": {},
    "organizations": {},
    "jobs": {},
    "candidates": {},
    "screening_results": {},
    "assessments": {},
    "assessment_results": {},
    "interviews": {},
    "interview_transcripts": {},
}


# --- Utility Functions ---

def _generate_id() -> str:
    """Generates a new unique identifier."""
    return str(uuid4())

def _simulate_save(collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Simulates saving a document to a collection."""
    doc_id = data.get("id") or _generate_id()
    now = datetime.now()
    
    # Set mandatory fields if new record
    if "id" not in data:
        data["id"] = doc_id
        data["created_at"] = now
    
    # Always update 'updated_at' for changes
    data["updated_at"] = now
    
    DATABASE[collection_name][doc_id] = data
    return DATABASE[collection_name][doc_id]


# --- 1. User & Auth CRUD ---

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user by their unique ID."""
    return DATABASE["users"].get(user_id)

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user by their email address."""
    for user in DATABASE["users"].values():
        if user["email"].lower() == email.lower():
            return user
    return None

def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new user in the database."""
    # Note: password hash would be handled here in a real app
    user_data.setdefault("is_active", True)
    user_data.setdefault("org_id", "default-org") # Placeholder for now
    return _simulate_save("users", user_data)

def get_organization_by_id(org_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an organization by ID."""
    # Assuming organization records are pre-populated for simplicity
    if org_id == "default-org":
        return {"id": "default-org", "name": "Gemini Innovations", "hr_contact_email": "hr@gemini-innovations.com"}
    return DATABASE["organizations"].get(org_id)


# --- 2. Job Post CRUD ---

def create_job_post(job_data: Dict[str, Any], org_id: str) -> Dict[str, Any]:
    """Creates a new job post."""
    job_data["org_id"] = org_id
    job_data.setdefault("status", "DRAFT")
    return _simulate_save("jobs", job_data)

def get_job_post(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a specific job post by ID."""
    return DATABASE["jobs"].get(job_id)

def get_all_job_posts(org_id: str) -> List[Dict[str, Any]]:
    """Retrieves all job posts for a given organization."""
    return [
        job for job in DATABASE["jobs"].values() 
        if job["org_id"] == org_id
    ]

def update_job_post(job_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates one or more fields of an existing job post."""
    job = get_job_post(job_id)
    if job:
        job.update(update_data)
        return _simulate_save("jobs", job)
    return None


# --- 3. Candidate CRUD ---

def create_candidate(candidate_data: Dict[str, Any], job_post_id: str) -> Dict[str, Any]:
    """Creates a new candidate application."""
    candidate_data["job_post_id"] = job_post_id
    candidate_data.setdefault("stage", "APPLIED")
    candidate_data.setdefault("application_date", datetime.now())
    return _simulate_save("candidates", candidate_data)

def get_candidate(candidate_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a specific candidate by ID."""
    return DATABASE["candidates"].get(candidate_id)

def get_candidates_by_job(job_id: str) -> List[Dict[str, Any]]:
    """Retrieves all candidates for a specific job post."""
    return [
        candidate for candidate in DATABASE["candidates"].values() 
        if candidate["job_post_id"] == job_id
    ]

def update_candidate_stage(candidate_id: str, new_stage: str) -> Optional[Dict[str, Any]]:
    """Updates the recruitment stage of a candidate."""
    candidate = get_candidate(candidate_id)
    if candidate:
        candidate["stage"] = new_stage
        return _simulate_save("candidates", candidate)
    return None

# --- 4. AI Screening Result CRUD ---

def create_screening_result(result_data: Dict[str, Any]) -> Dict[str, Any]:
    """Saves the AI screening result for a candidate."""
    return _simulate_save("screening_results", result_data)

def get_screening_result(candidate_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the screening result for a candidate."""
    for result in DATABASE["screening_results"].values():
        if result["candidate_id"] == candidate_id:
            return result
    return None


# --- 5. Assessment and Interview CRUD (Creation) ---

def create_assessment(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new online assessment record."""
    assessment_data.setdefault("status", "SENT")
    assessment_data.setdefault("sent_at", datetime.now())
    # Placeholder: In a real app, generated_questions would be set by the AI agent
    assessment_data.setdefault("generated_questions", []) 
    # Placeholder: Completion link would be dynamically generated
    assessment_data.setdefault("completion_link", f"/assessments/{_generate_id()}") 
    return _simulate_save("assessments", assessment_data)

def create_interview(interview_data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new interview record."""
    interview_data.setdefault("status", "PENDING")
    # Placeholder: meeting_link and scheduled_time set by a scheduling agent
    interview_data.setdefault("meeting_link", None)
    interview_data.setdefault("scheduled_time", None)
    return _simulate_save("interviews", interview_data)

def get_assessments_by_candidate(candidate_id: str) -> List[Dict[str, Any]]:
    """Retrieves all assessments for a candidate."""
    return [
        a for a in DATABASE["assessments"].values() 
        if a["candidate_id"] == candidate_id
    ]

def get_interviews_by_candidate(candidate_id: str) -> List[Dict[str, Any]]:
    """Retrieves all interviews for a candidate."""
    return [
        i for i in DATABASE["interviews"].values() 
        if i["candidate_id"] == candidate_id
    ]