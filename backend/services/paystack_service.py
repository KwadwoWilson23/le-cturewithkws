import httpx
import os
import typing

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
BASE_URL = "https://api.paystack.co"

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
        "callback_url": os.getenv("PAYSTACK_CALLBACK_URL", "http://localhost:5173/dashboard"),
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
