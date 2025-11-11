#!/usr/bin/env python
"""Quick test of the CV upload and Schedule OA flow"""
import sys
sys.path.insert(0, r'C:\Users\anike\OneDrive\Desktop\Projects\HR_TOOLING\hr_tooling')

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 1. Login
print("1. Login with hard-coded credentials")
resp = client.post('/token', data={'username': 'test@example.com', 'password': 'testpass', 'grant_type': 'password'})
print(f"   Status: {resp.status_code}")
token = resp.json().get('access_token')
print(f"   Token: {token}")
headers = {'Authorization': f'Bearer {token}'}

# 2. Create a job
print("\n2. Create a job")
job_payload = {
    'title': 'Python Developer',
    'description': 'Work with Python, FastAPI, and AWS',
    'location': 'Remote',
    'required_skills': ['python', 'fastapi', 'aws'],
    'min_experience_years': 2
}
resp = client.post('/jobs', json=job_payload, headers=headers)
print(f"   Status: {resp.status_code}")
job_id = resp.json().get('id')
print(f"   Job ID: {job_id}")

# 3. Activate the job
print("\n3. Activate the job")
resp = client.post(f'/jobs/{job_id}/activate', json={}, headers=headers)
print(f"   Status: {resp.status_code}")

# 4. Upload a CV
print("\n4. Upload a CV")
cv_text = "John Doe\nPython Developer with 5 years experience\nSkills: Python, FastAPI, AWS, Docker, SQL"
# Create a simple text file-like object
from io import BytesIO
from fastapi import UploadFile

files = {'file': ('resume.txt', BytesIO(cv_text.encode()), 'text/plain')}
data = {'full_name': 'John Doe', 'email': 'john@example.com'}
resp = client.post(
    f'/candidates/{job_id}/upload_cv',
    files=files,
    data=data,
    headers={'Authorization': f'Bearer {token}'}
)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    result = resp.json()
    candidate = result.get('candidate', {})
    candidate_id = candidate.get('id')
    ai = result.get('ai', {})
    print(f"   Candidate ID: {candidate_id}")
    print(f"   Candidate Name: {candidate.get('full_name')}")
    print(f"   Candidate Email: {candidate.get('email')}")
    print(f"   CV Text (first 100 chars): {candidate.get('cv_text', '')[:100]}")
    print(f"   AI Score: {ai.get('ats_score')}")
    print(f"   AI Feedback: {ai.get('feedback')}")
    print(f"   AI Highlights: {ai.get('highlights')}")
else:
    print(f"   Error: {resp.text}")

# 5. Schedule OA for the candidate
print("\n5. Schedule OA (Generate Assessment)")
resp = client.post(
    f'/candidates/{candidate_id}/schedule_oa',
    json={'num_questions': 3},
    headers=headers
)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    assessment = resp.json().get('assessment', {})
    print(f"   Assessment ID: {assessment.get('id')}")
    print(f"   Completion Link: {assessment.get('completion_link')}")
    questions = assessment.get('generated_questions', [])
    print(f"   Number of Questions: {len(questions)}")
    for i, q in enumerate(questions[:2], 1):
        print(f"      Q{i}: {q.get('question', 'N/A')} (Type: {q.get('type', 'N/A')})")
else:
    print(f"   Error: {resp.text}")

# 6. Get candidate details to verify all data
print("\n6. Get candidate details")
resp = client.get(f'/candidates/{candidate_id}', headers=headers)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    candidate = resp.json()
    print(f"   Name: {candidate.get('full_name')}")
    print(f"   Stage: {candidate.get('stage')}")
    print(f"   Has AI data: {'ai' in candidate}")
    if candidate.get('ai'):
        print(f"   ATS Score: {candidate['ai'].get('ats_score')}")
else:
    print(f"   Error: {resp.text}")

print("\n✅ All tests completed!")
