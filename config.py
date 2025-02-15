import os
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Debug: Print environment variables to check if they're loaded
#print(f"DEBUG: OPENAI_API_KEY={os.getenv('OPENAI_API_KEY')}")
#print(f"DEBUG: ANTHROPIC_API_KEY={os.getenv('ANTHROPIC_API_KEY')}")
#print(f"DEBUG: GEMINI_API_KEY={os.getenv('GEMINI_API_KEY')}")

# ✅ Assign API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ Ensure they are loaded
if not OPENAI_API_KEY or not ANTHROPIC_API_KEY or not GEMINI_API_KEY:
    raise ValueError("🚨 API keys are missing! Make sure the .env file is correctly configured.")

#print("✅ API keys loaded successfully!")