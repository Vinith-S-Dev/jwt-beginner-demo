# FastAPI JWT Login Demo

A simple python backend demonstrating how to implement JWT authentication and basic role-based access control in FastAPI.

## How to Run:

1. Create and activate a python virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Start uvicorn development server:
   ```bash
   uvicorn main:app --reload
   ```
   Open your browser to `http://127.0.0.1:8000/docs` to test the API with Swagger UI.

## Test Credentials:

| Username | Password | Role |
|---|---|---|
| admin | 1234 | admin |
| vinith | password | employee |

## Endpoints:
- `POST /login` - Login with credentials and retrieve a bearer JWT token.
- `GET /dashboard` - Protected dashboard route (requires any authenticated token).
- `GET /admin` - Admin-only route (requires a token with the "admin" role).
