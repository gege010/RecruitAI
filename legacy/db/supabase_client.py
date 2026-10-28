"""
Supabase client singleton and connection management.
"""
import os
from functools import lru_cache
from supabase import create_client, Client
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a singleton Supabase client instance."""
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_ANON_KEY", "")

    if not url or not key:
        raise EnvironmentError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env"
        )

    logger.info("Connecting to Supabase: {}", url)
    return create_client(url, key)


def check_connection() -> bool:
    """Verify Supabase connectivity by running a lightweight query."""
    try:
        client = get_supabase()
        client.table("job_vacancies").select("id").limit(1).execute()
        return True
    except Exception as exc:
        logger.error("Supabase connection failed: {}", exc)
        return False
