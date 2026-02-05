from central_bank import app, get_balance
import secrets
from itsdangerous import URLSafeTimedSerializer

serializer = URLSafeTimedSerializer('your-secret-key-here')

@app.post("/issue-passport")
def issue_passport(email: str, app_id: str):
    """Create a session token that includes spending authority"""
    balance = get_balance(email)
    
    # Limit how much can be spent in this session (e.g., 20% of balance or max 1000)
    session_budget = min(1000, balance // 5) if balance > 0 else 0
    
    passport = {
        "email": email,
        "app_id": app_id,
        "budget": session_budget,
        "issued_at": datetime.utcnow().isoformat(),
        "passport_id": secrets.token_hex(16)
    }
    
    # Encrypt the passport
    encrypted_passport = serializer.dumps(passport, salt=f'passport-{app_id}')
    
    return {
        "passport": encrypted_passport,
        "session_budget": session_budget,
        "total_balance": balance
    }
