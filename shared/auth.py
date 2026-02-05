import os
import sqlite3
from itsdangerous import URLSafeTimedSerializer

SECRET_KEY = "your-secret-key-change-in-production"
serializer = URLSafeTimedSerializer(SECRET_KEY)

def get_db_path():
    """Get the absolute path to bank.db, works both locally and on Render"""
    # Try several possible locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'bank.db'),  # Next to auth.py
        os.path.join(os.getcwd(), 'bank.db'),  # Current working directory
        '/opt/render/project/src/bank.db',  # Render's typical location
        'bank.db',  # Original relative path
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Found database at: {path}")
            return path
    
    # If not found, use the first location (will create it there)
    default_path = possible_paths[0]
    print(f"⚠️ Database not found, will create at: {default_path}")
    return default_path

def verify_magic_link(token: str, max_age=900, mark_used=True):
    """Verify magic link token"""
    
    print(f"🔍 VERIFY called with token: {token[:30]}...")
    
    # Handle test tokens (simple tokens used locally)
    if token.startswith("test_"):
        print(f"🔍 Test token detected, returning email after 'test_' prefix")
        return token[5:]  # Remove "test_" prefix
    
    # Handle JWT tokens (used on Render)
    try:
        print(f"🔍 Attempting JWT decode...")
        email = serializer.loads(token, salt="magic-link", max_age=max_age)
        print(f"🔍 JWT decoded to: {email}")
        
        # Check database
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute("SELECT used FROM magic_links WHERE token = ?", (token,))
        result = c.fetchone()
        
        if not result:
            print(f"🔍 Token not found in database!")
            conn.close()
            return None
            
        if result[0]:  # Already used
            print(f"🔍 Token already used")
            conn.close()
            return None
            
        # Mark as used if requested
        if mark_used:
            c.execute("UPDATE magic_links SET used = TRUE WHERE token = ?", (token,))
            conn.commit()
            print(f"🔍 Token marked as used")
        
        conn.close()
        print(f"🔍 SUCCESS! Verified: {email}")
        return email
        
    except Exception as e:
        print(f"🔍 ERROR in verification: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

def store_magic_token(email: str, token: str) -> bool:
    """Store a magic link token in database for later verification"""
    import datetime
    
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Ensure table exists
    c.execute('''CREATE TABLE IF NOT EXISTS magic_links
                 (token TEXT PRIMARY KEY, email TEXT, created DATETIME, used BOOLEAN)''')
    
    # Store the token
    try:
        c.execute("INSERT OR REPLACE INTO magic_links VALUES (?, ?, ?, ?)",
                  (token, email, datetime.datetime.utcnow(), False))
        conn.commit()
        print(f"📝 Stored token for {email}: {token[:30]}...")
        success = True
    except Exception as e:
        print(f"❌ Failed to store token: {e}")
        success = False
    finally:
        conn.close()
    
    return success

def create_magic_link(email: str) -> str:
    """Generate a magic link token"""
    import os
    
    # Detect environment
    is_render = os.getenv("RENDER") is not None
    
    if is_render:
        # PRODUCTION (Render): Use JWT tokens
        token = serializer.dumps(email, salt="magic-link")
        print(f"🔐 PRODUCTION: Created JWT token for {email}")
    else:
        # LOCAL DEVELOPMENT: Use simple tokens for debugging
        token = f"test_{email}"
        print(f"🔧 LOCAL: Created simple token for {email}")
    
    # Store in database (works for both)
    store_magic_token(email, token)
    return token

