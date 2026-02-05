# quick_check.py
import sys
import inspect
sys.path.insert(0, '.')  # Make sure current directory is in path

from shared import auth

print("📋 Functions in shared.auth:")
for name in dir(auth):
    if not name.startswith('_'):
        print(f"  {name}")

print("\n📄 Checking for specific functions...")
for func_name in ['verify_magic_link', 'create_magic_link', 'get_db_path', 'store_magic_token']:
    has_func = hasattr(auth, func_name)
    print(f"  {func_name}: {'✅' if has_func else '❌'}")
