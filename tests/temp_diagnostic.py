import sys
sys.path.insert(0, r'C:\Users\anike\OneDrive\Desktop\Projects\HR_TOOLING\hr_tooling')
from fastapi.testclient import TestClient
from main import app
import jwt

client = TestClient(app)

# Test 1: Signup
print('=== TEST 1: Signup ===')
signup_data = {
    'full_name': 'Test User',
    'email': 'test123@example.com',
    'password': 'secret123'
}
r = client.post('/register', json=signup_data)
print(f'Status: {r.status_code}')
print(f'Response: {r.json()}')
print()

# Test 2: Login
print('=== TEST 2: Login ===')
login_data = {
    'username': 'test123@example.com',
    'password': 'secret123',
    'grant_type': 'password'
}
r2 = client.post('/token', data=login_data)
print(f'Status: {r2.status_code}')
print(f'Response: {r2.json()}')

if r2.status_code == 200:
    token = r2.json().get('access_token')
    try:
        payload = jwt.decode(token, 'change_this_to_a_secure_random_value', algorithms=['HS256'])
        print('Decoded JWT payload:', payload)
        # Call /users/me
        headers = {'Authorization': f'Bearer {token}'}
        me = client.get('/users/me', headers=headers)
        print('/users/me status:', me.status_code)
        print('/users/me response:', me.json())
    except Exception as e:
        print('JWT decode error', e)
else:
    print('Login failed, skipping /users/me')
