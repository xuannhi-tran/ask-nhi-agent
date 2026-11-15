import os

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
VOYAGE_MODEL = "voyage-3.5"  # same embedding model as Ask Nhi (1024 dims)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")  # anon key has no access (RLS + revoked RPC)
TOP_K = 6
MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.3"))  # same cut-off as the website
