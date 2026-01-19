import sys
import os

# Set up path to include project root
sys.path.append(os.getcwd())

try:
    from funboost.funboost_web_manager.user_models import (
        query_user_by_name,
        query_user_by_id,
    )
    from funboost.funboost_web_manager.database import get_db_url

    print(f"DB URL: {get_db_url()}")

    # Test query by name
    user = query_user_by_name("admin")
    print(f"Query 'admin' by name result: {user is not None}")
    if user:
        print(f"User data: {user.keys()}")

        # Test query by ID (which is user_name in this app apparently, based on auth.py lines 76/138 where curr_user.id = user_name)
        # auth.py: curr_user.id = user_name
        # app.py: load_user(user_id) -> query_user_by_id(user_id)
        # user_models.py: need to check if query_user_by_id takes name or int id?

        # Let's inspect retrieval by ID using the name 'admin'
        user_by_id = query_user_by_id("admin")
        print(f"Query 'admin' by id result: {user_by_id is not None}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
