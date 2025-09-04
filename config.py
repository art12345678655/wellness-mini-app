import os
from dotenv import load_dotenv

# Load environment variables from .env file (only if it exists)
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Validate Supabase configuration
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required. Get it from your Supabase project settings.")
if not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_ANON_KEY environment variable is required. Get it from your Supabase project settings.")

# Mini App Configuration
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://your-mini-app.onrender.com")

# Port configuration for Render
PORT = int(os.getenv("PORT", 8080))
