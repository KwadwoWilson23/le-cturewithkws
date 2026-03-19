from datetime import datetime, timedelta, timezone

def is_trial_active(signup_date_str: str) -> bool:
    signup_date = datetime.fromisoformat(signup_date_str.replace('Z', '+00:00'))
    expiration_date = signup_date + timedelta(days=7)
    return datetime.now(tz=timezone.utc) < expiration_date

def days_left_in_trial(signup_date_str: str) -> int:
    signup_date = datetime.fromisoformat(signup_date_str.replace('Z', '+00:00'))
    expiration_date = signup_date + timedelta(days=7)
    remaining = expiration_date - datetime.now(tz=timezone.utc)
    return max(0, remaining.days)

def trial_status(signup_date_str: str) -> dict:
    active = is_trial_active(signup_date_str)
    days = days_left_in_trial(signup_date_str)
    return {
        "is_active": active,
        "days_left": days,
        "expired": not active,
    }
