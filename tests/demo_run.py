import sys
sys.path.insert(0, r'C:\Users\anike\OneDrive\Desktop\Projects\HR_TOOLING\hr_tooling')
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print('Testing login with hard-coded credentials')
resp = client.post('/token', data={'username':'test@example.com','password':'testpass','grant_type':'password'})
print(resp.status_code, resp.json())

token = resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

print('Calling /users/me')
me = client.get('/users/me', headers=headers)
print(me.status_code, me.json())

print('Creating a job (as test user)')
job_payload = {'title':'Software Engineer','description':'Work with Python and FastAPI','location':'Remote','status':'ACTIVE','required_skills':['python','fastapi'],'min_experience_years':2}
create = client.post('/jobs', json=job_payload, headers=headers)
print('create job:', create.status_code, create.json())
job_id = create.json().get('id')

# Activate the job (crud may default to DRAFT)
activate = client.post(f'/jobs/{job_id}/activate', json={}, headers=headers)
print('activate:', activate.status_code, activate.json())

print('Applying to public job')
apply_payload = {'full_name':'Alice','email':'alice@example.com','cv_text':'Alice is a Python developer with experience in FastAPI and AWS.'}
apply = client.post(f'/jobs/{job_id}/apply_public', json=apply_payload)
print('apply status:', apply.status_code)
print('apply response:', apply.json())
