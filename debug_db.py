from database import init_db
try:
    init_db()
except Exception as e:
    print(f"Caught exception: {e}")
