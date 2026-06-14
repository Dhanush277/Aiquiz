import os
from supabase import create_client, Client
from config.settings import Config

def get_supabase_client() -> Client:
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_ANON_KEY
    if not url or not key:
        print("Warning: Supabase credentials not found in environment. Database connection will fail.")
        # We allow it to pass here so the app can start and fail gracefully on db calls
        return None
    return create_client(url, key)

supabase: Client = get_supabase_client()
