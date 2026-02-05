# test_balance_fixed.py
import sys
sys.path.insert(0, '.')

print("💰 Testing fixed balance system...")
print("=" * 60)

try:
    # Test 1: Check import
    from central_bank import get_user_balance
    print("✅ Import successful")
    
    # Test 2: Get your balance
    balance = get_user_balance("lucsetzer@gmail.com")
    print(f"💰 Your balance: {balance} tokens")
    
    # Test 3: Check new user (should create account with 0)
    balance2 = get_user_balance("test-new@example.com")
    print(f"💰 New user balance: {balance2} tokens")
    
    # Test 4: Check that get_db_path is being used
    print(f"\n🔍 Checking database consistency...")
    from shared.auth import get_db_path
    db_path = get_db_path()
    print(f"   Database path: {db_path}")
    
    import os
    print(f"   File exists: {os.path.exists(db_path)}")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
