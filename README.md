# 🔑 Simple FastAPI JWT Authentication Demo

A beginner-friendly, single-file FastAPI project showing how to implement user authentication with **JSON Web Tokens (JWT)** and basic role validation.

## 🚀 How to Run Locally

### 1. Set Up and Activate Environment
```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate

# Activate it (macOS/Linux)
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Server
```bash
uvicorn main:app --reload
```
The server will start running on **`http://127.0.0.1:8000`**.

---

## 👥 Demo Users

You can log in using these preset credentials:

| Username | Password | Role |
|---|---|---|
| **`admin`** | `1234` | admin |
| **`vinith`** | `password` | employee |

---

## 🔌 API Endpoints

Once the server is running, go to **`http://127.0.0.1:8000/docs`** to see the interactive Swagger UI and test these endpoints:

1. **`POST /login`**: Submits a form with username and password to get a bearer JWT token.
2. **`GET /dashboard`**: Access a generic dashboard profile (requires any valid token).
3. **`GET /admin`**: Access an admin panel (requires a token with the `admin` role claim).
