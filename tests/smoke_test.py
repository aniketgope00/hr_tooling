from fastapi.testclient import TestClient
from main import app
from src.db import crud

client = TestClient(app)


def run_smoke_test():
    print('Starting smoke test: register -> login -> users/me')

    # Prepare a deterministic demo user
    demo_email = 'demo.user@example.com'
    demo = {
        'full_name': 'Demo User',
        'email': demo_email,
        'password': 'secret123',
        'org_name': 'Demo Org'
    }

    # Clean up any existing demo user/org if present
    existing = crud.get_user_by_email(demo_email)
    if existing:
        print('Removing existing demo user before test')
        try:
            del crud.DATABASE['users'][existing['id']]
        except Exception:
            pass

    # Register
    r = client.post('/register', json=demo)
    assert r.status_code == 201, f"Register failed: {r.status_code} {r.text}"
    user = r.json()
    print('Registered user:', user.get('email'), 'id=', user.get('id'))

    org_id = user.get('org_id')
    assert org_id, 'User should have org_id'
    org = crud.get_organization_by_id(org_id)
    assert org, 'Organization should exist'
    print('Organization created:', org.get('name'), 'id=', org.get('id'))

    # Login (form-encoded)
    # DEBUG: inspect stored user in DB
    stored = crud.get_user_by_email(demo_email)
    print('Stored DB user entry:', stored)
    print('Stored password (DB):', stored.get('password'))

    data = {'username': demo_email, 'password': demo['password'], 'grant_type': 'password'}
    r2 = client.post('/token', data=data)
    assert r2.status_code == 200, f"Login failed: {r2.status_code} {r2.text}"
    token_payload = r2.json()
    print('Login token payload:', token_payload)
    token = token_payload.get('access_token')
    assert token, 'No access_token returned'

    # Call protected endpoint
    headers = {'Authorization': f'Bearer {token}'}
    r3 = client.get('/users/me', headers=headers)
    assert r3.status_code == 200, f"users/me failed: {r3.status_code} {r3.text}"
    me = r3.json()
    print('users/me returned:', me.get('email'), 'org_id=', me.get('org_id'))

    print('Smoke test passed ✅')


if __name__ == '__main__':
    run_smoke_test()
