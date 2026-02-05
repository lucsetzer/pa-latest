from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import secrets
from datetime import datetime, timedelta
from shared.auth import get_db_path

app = FastAPI()

# Bank database setup
def init_bank():
    from shared.auth import get_db_path
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts
                 (email TEXT PRIMARY KEY, tokens INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id TEXT, email TEXT, amount INTEGER, description TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

init_bank()

class Deposit(BaseModel):
    email: str
    tokens: int
    payment_id: str  # From Stripe

class SpendRequest(BaseModel):
    email: str
    app_id: str
    tokens: int
    description: str

@app.post("/deposit")
def deposit_funds(deposit: Deposit):
    """When user buys tokens via Stripe"""
    from shared.auth import get_db_path
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    # Add to balance
    c.execute('INSERT OR IGNORE INTO accounts (email, tokens) VALUES (?, 0)', (deposit.email,))
    c.execute('UPDATE accounts SET tokens = tokens + ? WHERE email = ?', 
              (deposit.tokens, deposit.email))
    
    # Record transaction
    tx_id = secrets.token_hex(8)
    c.execute('INSERT INTO transactions VALUES (?, ?, ?, ?, ?)',
              (tx_id, deposit.email, deposit.tokens, 
               f"Purchase via {deposit.payment_id}", datetime.utcnow()))
    
    conn.commit()
    conn.close()
    return {"status": "deposited", "new_balance": get_balance(deposit.email)}

@app.post("/spend")
def spend_tokens(spend: SpendRequest):
    """When an AI app uses tokens"""
    from shared.auth import get_db_path
    conn = sqlite3.connect(get_db_path())   
    c = conn.cursor()
    
    # Check balance
    c.execute('SELECT tokens FROM accounts WHERE email = ?', (spend.email,))
    result = c.fetchone()
    if not result or result[0] < spend.tokens:
        raise HTTPException(status_code=402, detail="Insufficient tokens")
    
    # Deduct
    c.execute('UPDATE accounts SET tokens = tokens - ? WHERE email = ?',
              (spend.tokens, spend.email))
    
    # Record spend
    tx_id = secrets.token_hex(8)
    c.execute('INSERT INTO transactions VALUES (?, ?, ?, ?, ?)',
              (tx_id, spend.email, -spend.tokens, 
               f"{spend.app_id}: {spend.description}", datetime.utcnow()))
    
    conn.commit()
    conn.close()
    return {"status": "spent", "remaining": get_balance(spend.email)}

def get_balance(email: str) -> int:
    from shared.auth import get_db_path
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    # Check if exists
    c.execute('SELECT tokens FROM accounts WHERE email = ?', (email,))
    result = c.fetchone()
    
    if result:
        balance = result[0]
    else:
        # Create account with free plan tokens (15)
        c.execute('INSERT INTO accounts (email, tokens) VALUES (?, ?)', (email, 15))
        conn.commit()
        balance = 15
        print(f"💰 Created new account for {email} with {balance} tokens")
    
    conn.close()
    return balance

@app.get("/test")
def test():
    return {"status": "bank is working"}

@app.get("/")
def root():
    return {"message": "AI Wizards Bank API", "docs": "/docs"}

# Alias for compatibility with dashboard
get_user_balance = get_balance
