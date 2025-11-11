from fastapi.testclient import TestClient
import sys
sys.path.insert(0, r'C:\Users\anike\OneDrive\Desktop\Projects\HR_TOOLING\hr_tooling')
from main import app
from src.db import crud

client = TestClient(app)


def run_features_smoke():
    print('Features smoke test: register -> login -> create job -> activate -> public list -> apply -> retrieve candidates')
    email = 'feature.demo@example.com'
    demo = {'full_name':'Feature Demo','email':email,'password':'pass1234','org_name':'Feature Org'}

    # cleanup existing
    existing = crud.get_user_by_email(email)
    if existing:
        try:
            del crud.DATABASE['users'][existing['id']]
        except Exception:
            pass

    # register
    r = client.post('/register', json=demo)
    assert r.status_code == 201, r.text
    user = r.json()
    print('Registered', user.get('email'), 'id=', user.get('id'))

    # login
    r2 = client.post('/token', data={'username':email,'password':demo['password'],'grant_type':'password'})
    assert r2.status_code == 200, r2.text
    token = r2.json().get('access_token')
    assert token
    headers = {'Authorization':f'Bearer {token}'}

    # create job
    job_payload = {
        'title':'Feature Engineer',
        'description':'Work on features',
        'required_skills':['python','fastapi'],
        'min_experience_years':1.0,
        'salary_range_min':50000
    }
    r3 = client.post('/jobs', json=job_payload, headers=headers)
    assert r3.status_code == 201, r3.text
    job = r3.json()
    print('Created job', job.get('id'))

    # activate job
    r4 = client.put(f"/jobs/{job.get('id')}", json={'status':'ACTIVE'}, headers=headers)
    assert r4.status_code == 200, r4.text

    # public jobs list
    r5 = client.get('/public/jobs')
    assert r5.status_code == 200, r5.text
    pubs = r5.json()
    assert any(j['id'] == job.get('id') for j in pubs), 'Job not in public list'
    print('Public jobs includes created job')

    # candidate apply (public)
    cand = {'full_name':'Applicant A','email':'applicant@example.com','resume_url':'http://example.com/resume.pdf','job_post_id':job.get('id')}
    r6 = client.post('/candidates', json=cand)
    assert r6.status_code == 201, r6.text
    created_cand = r6.json()
    print('Candidate applied id=', created_cand.get('id'))

    # retrieve candidates for job (auth)
    r7 = client.get(f"/jobs/{job.get('id')}/candidates", headers=headers)
    assert r7.status_code == 200, r7.text
    cands = r7.json()
    assert any(c['id'] == created_cand.get('id') for c in cands), 'Candidate not found in job candidates'
    print('Candidates retrieval OK')

    print('Features smoke test passed ✅')


if __name__ == '__main__':
    run_features_smoke()
