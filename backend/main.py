from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes.upload import router as upload_router
from routes.chat import router as chat_router
from routes.auth import router as auth_router
from routes.payments import router as payments_router
from routes.live_session import router as live_session_router

load_dotenv()

app = FastAPI(
    title="lecturewithkws API",
    description="AI-powered lecture assistant backend — PDF upload, Gemini AI chat, quiz generation, and Paystack payments.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "app://.",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, tags=["Upload"])
app.include_router(chat_router, tags=["Chat & Quiz"])
app.include_router(auth_router, tags=["Auth"])
app.include_router(payments_router, tags=["Payments"])
app.include_router(live_session_router, tags=["Live Session"])


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "lecturewithkws API is running 🎓",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}