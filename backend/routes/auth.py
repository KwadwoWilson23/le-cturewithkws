from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
import os

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None


class AuthRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/signup")
async def signup(request: AuthRequest):
    if not supabase:
        return {"message": "Supabase not configured — auth handled on frontend"}

    try:
        res = await asyncio.to_thread(
            supabase.auth.sign_up,
            {"email": request.email, "password": request.password}
        )
        if res.user:
            return {
                "message": "Account created. Please check your email to confirm.",
                "user_id": res.user.id,
                "email": res.user.email
            }
        raise HTTPException(status_code=400, detail="Could not create account.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login")
async def login(request: AuthRequest):
    if not supabase:
        return {"message": "Supabase not configured — auth handled on frontend"}

    try:
        res = await asyncio.to_thread(
            supabase.auth.sign_in_with_password,
            {"email": request.email, "password": request.password}
        )
        if res.session:
            return {
                "access_token": res.session.access_token,
                "user_id": res.user.id,
                "email": res.user.email
            }
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/logout")
async def logout():
    if supabase:
        try:
            await asyncio.to_thread(supabase.auth.sign_out)
        except Exception:
            pass
    return {"message": "Logged out successfully."}
