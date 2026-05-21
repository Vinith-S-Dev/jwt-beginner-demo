from datetime import datetime, timedelta, timezone
from typing import Annotated
import bcrypt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

app = FastAPI()

# =========================================================
# CONFIGURATION
# =========================================================
SECRET_KEY = "my_super_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# =========================================================
# OAUTH2 PASSWORD BEARER
# =========================================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# =========================================================
# PASSWORD HASHING (Native Bcrypt)
# =========================================================
def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# =========================================================
# MOCK DATABASE
# =========================================================
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("1234"),
        "role": "admin",
    },
    "vinith": {
        "username": "vinith",
        "hashed_password": get_password_hash("password"),
        "role": "employee",
    },
}

# =========================================================
# JWT TOKEN GENERATION
# =========================================================
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# =========================================================
# GET CURRENT USER (Dependency)
# =========================================================
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise credentials_exception
        return {"username": username, "role": role}
    except JWTError:
        raise credentials_exception

# =========================================================
# API ROUTES
# =========================================================

@app.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/dashboard")
async def dashboard(current_user: Annotated[dict, Depends(get_current_user)]):
    return {
        "message": f"Welcome {current_user['username']}",
        "role": current_user["role"],
    }

@app.get("/admin")
async def admin_panel(current_user: Annotated[dict, Depends(get_current_user)]):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return {
        "message": "Welcome Admin",
        "user": current_user,
    }
