import os
from dotenv import load_dotenv

# Load environment variables from .env file (only if it exists)
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# For production, use fallback values if Supabase is not configured
SUPABASE_AVAILABLE = bool(SUPABASE_URL and SUPABASE_ANON_KEY)
print(f"Supabase Available: {SUPABASE_AVAILABLE}")

# Default values for demo mode
if not SUPABASE_URL:
    SUPABASE_URL = "demo_url"
if not SUPABASE_ANON_KEY:
    SUPABASE_ANON_KEY = "demo_key"

# Mini App Configuration
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://your-mini-app.onrender.com")

# Port configuration for Render
PORT = int(os.getenv("PORT", 8080))
