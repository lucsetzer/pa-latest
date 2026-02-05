# test_consistency.py
import os
from shared.auth import get_db_path, verify_magic_link, create_magic_link

print("🔍 Checking database consistency...")

# 1. All functions should use the same path
db_path = get_db_path()
print(f"📁 Database path from get_db_path(): {db_path}")
print(f"📁 File exists: {os.path.exists(db_path)}")

# 2. Test creating and verifying a token
test_email = "local_test@example.com"
print(f"\n🔑 Testing auth flow for: {test_email}")

# Try to create a token
try:
    token = create_magic_link(test_email)
    print(f"✅ Token created: {token[:30]}...")
except Exception as e:
    print(f"❌ create_magic_link failed: {e}")
    token = "test_local_test@example.com"  # Fallback

# Try to verify it
try:
    result = verify_magic_link(token, mark_used=False)
    print(f"✅ Token verified, got email: {result}")
except Exception as e:
    print(f"❌ verify_magic_link failed: {e}")

# 3. Check what's actually in the database
import sqlite3
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT email, tokens FROM accounts")
accounts = cursor.fetchall()
print(f"\n📊 Accounts in database: {accounts}")

cursor.execute("SELECT COUNT(*) FROM magic_links")
magic_count = cursor.fetchone()[0]
print(f"📊 Magic links in database: {magic_count}")

conn.close()
