"""Supabase client configuration."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables from .env file
load_dotenv()


@lru_cache
def get_supabase_client() -> Client:
    """Get a cached Supabase client instance.

    Returns:
        Supabase client configured with project credentials.

    Raises:
        ValueError: If required environment variables are not set.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment"
        )

    return create_client(url, key)
