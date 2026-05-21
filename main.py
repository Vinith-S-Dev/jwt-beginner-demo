import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from jose import JWTError, jwt
import bcrypt

# Create FastAPI app
app = FastAPI(
    title="JWT Auth Portal",
    description="A sleek and secure JWT Authentication demo with Role-Based Access Control.",
    version="1.0.0"
)

# =========================================================
# CORS MIDDLEWARE
# =========================================================
# Allows frontend applications to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo purposes; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# JWT CONFIG
# =========================================================
SECRET_KEY = os.getenv("SECRET_KEY", "my_super_secret_key_world_class_jwt_portal")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# =========================================================
# PASSWORD HASHING
# =========================================================
def get_password_hash(password: str) -> str:
    # Hash password using native bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verify password using native bcrypt
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# =========================================================
# OAUTH2 SCHEME
# =========================================================
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/login"
)

# =========================================================
# FAKE DATABASE
# =========================================================
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@gmail.com",
        "hashed_password": get_password_hash("1234"),
        "role": "admin",
    },
    "vinith": {
        "username": "vinith",
        "full_name": "Vinith S",
        "email": "vinith@gmail.com",
        "hashed_password": get_password_hash("password"),
        "role": "employee",
    },
}

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    return fake_users_db.get(username)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({
        "exp": expire
    })
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return encoded_jwt

# =========================================================
# AUTHENTICATION ROUTE
# =========================================================
@app.post("/api/login")
async def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ]
):
    user = authenticate_user(
        form_data.username,
        form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "role": user["role"]
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

# =========================================================
# TOKEN VERIFICATION / CURRENT USER DEPENDENCY
# =========================================================
async def get_current_user(
    token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise credentials_exception
        return {
            "username": username,
            "role": role
        }
    except JWTError:
        raise credentials_exception

# =========================================================
# PROTECTED ROUTE
# =========================================================
@app.get("/api/dashboard")
async def dashboard(
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    return {
        "message": f"Welcome {current_user['username']}!",
        "role": current_user["role"],
        "server_time": datetime.now(timezone.utc).isoformat()
    }

# =========================================================
# ADMIN ONLY ROUTE
# =========================================================
@app.get("/api/admin")
async def admin_panel(
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin privileges required"
        )
    return {
        "message": "Welcome Admin to the Secure Command Console",
        "user": current_user,
        "system_status": "All systems operational",
        "database_users": list(fake_users_db.keys())
    }

# =========================================================
# STATIC FILE SERVING / FRONTEND
# =========================================================
# Mount static files (HTML, CSS, JS)
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def read_index():
    index_file = os.path.join(static_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "JWT Auth API operational. Static frontend not found."}
