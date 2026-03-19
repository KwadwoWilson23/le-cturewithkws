from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.paystack_service import initialize_payment, verify_payment
import os
import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

router = APIRouter()

supabase = None
_supabase_url = os.getenv("SUPABASE_URL", "")

# Note: Admin operations (like updating user metadata) REQUIRE the SERVICE_ROLE_KEY.
# Using the ANON_KEY will result in permission denied errors for admin tasks.
_supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")

if _supabase_url and _supabase_key:
    try:
        from supabase import create_client
        supabase = create_client(_supabase_url, _supabase_key)
        
        # Check if we actually have a service role key if we plan to use admin features
        if not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
            print("⚠️ WARNING: SUPABASE_SERVICE_ROLE_KEY is missing. Premium upgrades will fail.")
    except Exception as e:
        print(f"❌ Supabase initialization error: {str(e)}")
        supabase = None


class PaymentRequest(BaseModel):
    email: str
    amount: int
    metadata: dict = {}


def send_upgrade_email(to_email: str, plan_name: str):
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not all([smtp_host, smtp_user, smtp_pass]):
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🎓 You're now Premium on lecturewithkws!"
        msg["From"] = f"lecturewithkws <{smtp_user}>"
        msg["To"] = to_email

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px;">
            <div style="max-width: 560px; margin: 0 auto; background: #1e293b; border-radius: 16px; padding: 40px; border: 1px solid #334155;">
                <h1 style="color: #10b981; font-size: 28px; margin-bottom: 8px;">Welcome to Premium! 🎉</h1>
                <p style="color: #94a3b8; font-size: 16px; margin-bottom: 24px;">
                    Your <strong style="color: #e2e8f0;">{plan_name}</strong> plan is now active.
                </p>
                <hr style="border-color: #334155; margin: 24px 0;" />
                <h3 style="color: #e2e8f0;">What you now have access to:</h3>
                <ul style="color: #94a3b8; line-height: 2;">
                    <li>✅ Unlimited PDF Uploads</li>
                    <li>✅ Unlimited AI Chat with Professor KWS</li>
                    <li>✅ Unlimited Quiz Generation</li>
                    <li>✅ Voice Input</li>
                    <li>✅ Advanced Deep Explanations</li>
                </ul>
                <a href="http://localhost:5173/dashboard"
                   style="display: inline-block; margin-top: 28px; padding: 14px 32px;
                          background: #10b981; color: white; border-radius: 10px;
                          text-decoration: none; font-weight: 700; font-size: 16px;">
                    Go to Dashboard →
                </a>
                <p style="margin-top: 32px; font-size: 12px; color: #475569;">
                    lecturewithkws · Your AI Study Partner
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())

    except Exception:
        pass


@router.post("/payments/initialize")
async def pay_init(request: PaymentRequest):
    if request.amount < 100:
        raise HTTPException(status_code=400, detail="Minimum amount is 1 GHC (100 pesewas).")

    res = await initialize_payment(request.email, request.amount, request.metadata)

    if res.get("status"):
        return {
            "authorization_url": res["data"]["authorization_url"],
            "reference": res["data"]["reference"],
            "access_code": res["data"]["access_code"],
        }

    raise HTTPException(status_code=400, detail=res.get("message", "Could not initialize payment."))


@router.get("/payments/verify/{reference}")
async def pay_verify(reference: str):
    res = await verify_payment(reference)

    if res.get("status"):
        data = res["data"]
        paid = data.get("status") == "success"
        customer_email = data.get("customer", {}).get("email", "")
        plan_name = data.get("metadata", {}).get("plan_name", "Premium")

        if paid:
            if supabase:
                try:
                    user_id = data.get("metadata", {}).get("user_id")
                    if user_id:
                        await asyncio.to_thread(
                            supabase.auth.admin.update_user_by_id,
                            user_id,
                            {"user_metadata": {"is_premium": True, "plan": plan_name}}
                        )
                except Exception as e:
                    print(f"❌ Failed to update Supabase metadata: {str(e)}")

            if customer_email:
                await asyncio.to_thread(send_upgrade_email, customer_email, plan_name)

        return {
            "paid": paid,
            "amount": data.get("amount"),
            "currency": data.get("currency"),
            "email": customer_email,
            "reference": data.get("reference"),
            "paid_at": data.get("paid_at"),
            "plan": plan_name,
        }

    raise HTTPException(status_code=400, detail="Payment verification failed.")
