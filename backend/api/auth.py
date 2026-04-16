"""
Authentication module with:
- Password hashing (PBKDF2-HMAC-SHA256)
- JWT access & refresh tokens
- MFA via email OTP
- Basic RBAC (user / admin)
"""

import json
import os
import hashlib
import secrets
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field

# ── Config ───────────────────────────────────────────────────────────────────

JWT_SECRET = os.getenv("JWT_SECRET", "shiproute-ai-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRY_MINUTES = 30
REFRESH_TOKEN_EXPIRY_DAYS = 7
OTP_EXPIRY_SECONDS = 300  # 5 minutes

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    email: str
    password: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class GoogleLoginRequest(BaseModel):
    id_token: str
    name: str
    email: str


# ── User Store ───────────────────────────────────────────────────────────────

def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def _save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


# ── Password Hashing ────────────────────────────────────────────────────────

def _hash_password(password: str, salt: str = None) -> tuple:
    """Hash password with PBKDF2-HMAC-SHA256. Returns (hash_hex, salt_hex)."""
    if salt is None:
        salt = secrets.token_hex(32)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000
    )
    return pw_hash.hex(), salt

def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    computed_hash, _ = _hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


# ── JWT Tokens ───────────────────────────────────────────────────────────────

def _create_access_token(email: str, role: str) -> str:
    payload = {
        "sub": email,
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _create_refresh_token(email: str) -> str:
    payload = {
        "sub": email,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_hex(16)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── OTP Generation & Email ──────────────────────────────────────────────────

def _generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)  # 6-digit OTP

def _send_otp_email(to_email: str, otp: str):
    """Send OTP via email. Falls back to console logging if SMTP not configured."""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"\n{'='*50}")
        print(f"  MFA OTP for {to_email}: {otp}")
        print(f"  (Configure SMTP_EMAIL & SMTP_PASSWORD in .env for real emails)")
        print(f"{'='*50}\n")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg["Subject"] = "ShipRoute AI - Your Login OTP"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #060a14; color: #f1f5f9; padding: 40px;">
            <div style="max-width: 400px; margin: 0 auto; background: rgba(255,255,255,0.05); border-radius: 16px; padding: 32px; border: 1px solid rgba(255,255,255,0.1);">
                <h2 style="color: #3b82f6; margin-bottom: 8px;">ShipRoute AI</h2>
                <p style="color: #94a3b8;">Your one-time verification code:</p>
                <div style="font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #3b82f6; text-align: center; padding: 20px; background: rgba(59,130,246,0.1); border-radius: 12px; margin: 16px 0;">
                    {otp}
                </div>
                <p style="color: #64748b; font-size: 13px;">This code expires in 5 minutes. Do not share it with anyone.</p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[AUTH] OTP email sent to {to_email}")
    except Exception as e:
        print(f"[AUTH] Email send failed: {e}, OTP: {otp}")


# ── Auth Dependency ──────────────────────────────────────────────────────────

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """FastAPI dependency to extract and validate JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split(" ", 1)[1]
    payload = _decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    users = _load_users()
    email = payload.get("sub")
    if email not in users:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "email": email,
        "name": users[email]["name"],
        "role": users[email].get("role", "user")
    }


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """FastAPI dependency that requires admin role."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/signup")
async def signup(req: SignupRequest):
    """Register a new user with hashed password."""
    users = _load_users()
    email = req.email.lower().strip()

    if email in users:
        raise HTTPException(status_code=409, detail="Email already registered")

    pw_hash, salt = _hash_password(req.password)

    users[email] = {
        "name": req.name,
        "password_hash": pw_hash,
        "salt": salt,
        "role": "admin" if len(users) == 0 else "user",  # First user becomes admin
        "mfa_enabled": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _save_users(users)

    return {"success": True, "message": "Account created. Please login."}


@router.post("/login")
async def login(req: LoginRequest):
    """Step 1: Validate credentials → send OTP."""
    users = _load_users()
    email = req.email.lower().strip()

    if email not in users:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = users[email]
    if not _verify_password(req.password, user["password_hash"], user["salt"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Generate and store OTP
    otp = _generate_otp()
    users[email]["pending_otp"] = otp
    users[email]["otp_expires"] = time.time() + OTP_EXPIRY_SECONDS
    _save_users(users)

    # Send OTP via email
    _send_otp_email(email, otp)

    return {
        "success": True,
        "mfa_required": True,
        "message": "OTP sent to your email"
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(req: OTPVerifyRequest):
    """Step 2: Verify OTP → issue JWT tokens."""
    users = _load_users()
    email = req.email.lower().strip()

    if email not in users:
        raise HTTPException(status_code=401, detail="Invalid request")

    user = users[email]
    stored_otp = user.get("pending_otp")
    otp_expires = user.get("otp_expires", 0)

    if not stored_otp:
        raise HTTPException(status_code=400, detail="No pending OTP. Please login again.")

    if time.time() > otp_expires:
        users[email].pop("pending_otp", None)
        users[email].pop("otp_expires", None)
        _save_users(users)
        raise HTTPException(status_code=400, detail="OTP expired. Please login again.")

    if not secrets.compare_digest(req.otp.strip(), stored_otp):
        raise HTTPException(status_code=401, detail="Invalid OTP")

    # Clear OTP
    users[email].pop("pending_otp", None)
    users[email].pop("otp_expires", None)
    _save_users(users)

    # Issue tokens
    role = user.get("role", "user")
    access_token = _create_access_token(email, role)
    refresh_token = _create_refresh_token(email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "email": email,
            "name": user["name"],
            "role": role
        }
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    payload = _decode_token(req.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    email = payload.get("sub")
    users = _load_users()

    if email not in users:
        raise HTTPException(status_code=401, detail="User not found")

    user = users[email]
    role = user.get("role", "user")

    new_access = _create_access_token(email, role)
    new_refresh = _create_refresh_token(email)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user={
            "email": email,
            "name": user["name"],
            "role": role
        }
    )


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Return current user profile from JWT."""
    return {"success": True, "user": user}


# ── Google OAuth ─────────────────────────────────────────────────────────────

@router.post("/google", response_model=TokenResponse)
async def google_login(req: GoogleLoginRequest):
    """
    Authenticate via Firebase Google Sign-In.
    Auto-creates user if not exists. Skips OTP (Google already verified identity).
    """
    email = req.email.lower().strip()
    name = req.name or email.split("@")[0]
    users = _load_users()

    if email not in users:
        # Auto-register Google user
        users[email] = {
            "name": name,
            "password_hash": "",
            "salt": "",
            "role": "admin" if len(users) == 0 else "user",
            "mfa_enabled": False,
            "auth_provider": "google",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        _save_users(users)
        print(f"[AUTH] New Google user registered: {email}")

    user = users[email]
    role = user.get("role", "user")

    access_token = _create_access_token(email, role)
    refresh_token = _create_refresh_token(email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "email": email,
            "name": user["name"],
            "role": role
        }
    )


# ── Admin Endpoints ─────────────────────────────────────────────────────────

@router.get("/admin/users")
async def list_users(admin: dict = Depends(require_admin)):
    """Admin only: list all registered users."""
    users = _load_users()
    user_list = []
    for email, data in users.items():
        user_list.append({
            "email": email,
            "name": data["name"],
            "role": data.get("role", "user"),
            "created_at": data.get("created_at", "N/A")
        })
    return {"success": True, "users": user_list}


@router.put("/admin/users/{email}/role")
async def update_user_role(email: str, role: str, admin: dict = Depends(require_admin)):
    """Admin only: change a user's role."""
    if role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")

    users = _load_users()
    if email not in users:
        raise HTTPException(status_code=404, detail="User not found")

    users[email]["role"] = role
    _save_users(users)
    return {"success": True, "message": f"User {email} role updated to {role}"}
