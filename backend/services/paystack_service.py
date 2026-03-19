import httpx
import os
import typing

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
if not PAYSTACK_SECRET_KEY:
    print("⚠️ WARNING: PAYSTACK_SECRET_KEY is missing. Payment transfers will fail.")

BASE_URL = "https://api.paystack.co"

PAYSTACK_CALLBACK_URL = os.getenv("PAYSTACK_CALLBACK_URL")
if not PAYSTACK_CALLBACK_URL or "localhost" in PAYSTACK_CALLBACK_URL:
    print("⚠️ WARNING: PAYSTACK_CALLBACK_URL may be pointing to localhost in production")

def _headers():
    return {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

async def initialize_payment(email: str, amount: int, metadata: typing.Optional[dict] = None):
    payload: typing.Dict[str, typing.Any] = {
        "email": email,
        "amount": amount,
        "currency": "GHS",
        "callback_url": PAYSTACK_CALLBACK_URL or "http://localhost:5173/dashboard",
    }
    if metadata:
        payload["metadata"] = metadata

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{BASE_URL}/transaction/initialize", headers=_headers(), json=payload)
    return response.json()

async def verify_payment(reference: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/transaction/verify/{reference}", headers=_headers())
    return response.json()

async def get_transaction(transaction_id: int):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/transaction/{transaction_id}", headers=_headers())
    return response.json()
