import sys
import pytest
sys.path.insert(0, r'C:\Users\anike\OneDrive\Desktop\Projects\HR_TOOLING\hr_tooling')
from fastapi.testclient import TestClient
from main import app
from src.db import crud

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_demo_data():
    # Ensure a clean in-memory DB for each test run
    crud.DATABASE['users'].clear()
    crud.DATABASE['organizations'].clear()
    crud.DATABASE['jobs'].clear()
    crud.DATABASE['candidates'].clear()
    yield


def test_register_and_login_and_dashboard_flow():
    demo = {'full_name':'Int Test','email':'int.test@example.com','password':'s3cret','org_name':'Int Org'}
    r = client.post('/register', json=demo)
    assert r.status_code == 201
    user = r.json()
    assert user['email'] == demo['email']
    assert 'id' in user

    # login using form-encoded data (simulate browser OAuth2 form)
    r2 = client.post('/token', data={'username': demo['email'], 'password': demo['password'], 'grant_type': 'password'}, headers={'Content-Type':'application/x-www-form-urlencoded'})
    assert r2.status_code == 200
    token = r2.json().get('access_token')
    assert token

    # call protected endpoint
    headers = {'Authorization': f'Bearer {token}'}
    r3 = client.get('/users/me', headers=headers)
    assert r3.status_code == 200
    me = r3.json()
    assert me['email'] == demo['email']


def test_job_and_candidate_endpoints():
    # create user and login
    demo = {'full_name':'JobTest','email':'job.test@example.com','password':'pw','org_name':'Job Org'}
    r = client.post('/register', json=demo)
    assert r.status_code == 201
    token = client.post('/token', data={'username': demo['email'], 'password': demo['password'], 'grant_type':'password'}).json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    # create job
    job_payload = {
        'title':'Integration Role',
        'description':'Test role',
        'required_skills':['x'],
        'min_experience_years':0,
    }
    r2 = client.post('/jobs', json=job_payload, headers=headers)
    assert r2.status_code == 201
    job = r2.json()

    # set job active
    r3 = client.put(f"/jobs/{job['id']}", json={'status':'ACTIVE'}, headers=headers)
    assert r3.status_code == 200

    # public jobs should list it
    r4 = client.get('/public/jobs')
    assert r4.status_code == 200
    jobs = r4.json()
    assert any(j['id'] == job['id'] for j in jobs)

    # candidate applies
    cand = {'full_name':'Applicant','email':'app@x.com','resume_url':'http://x','job_post_id':job['id']}
    r5 = client.post('/candidates', json=cand)
    assert r5.status_code == 201
    c = r5.json()

    # owner retrieves candidates
    r6 = client.get(f"/jobs/{job['id']}/candidates", headers=headers)
    assert r6.status_code == 200
    cs = r6.json()
    assert any(ci['id'] == c['id'] for ci in cs)
