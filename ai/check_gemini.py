"""
check_gemini.py

Run this from your project root to diagnose whether Milo's Gemini
connection is set up correctly:

    python check_gemini.py

Uses the google-genai SDK (from google import genai), matching what
ai/assistant.py now uses.
"""

import os
import sys

print("=" * 50)
print("Gemini Connection Diagnostic")
print("=" * 50)

# 1. Check python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK]   python-dotenv is installed, .env loaded")
except ImportError:
    print("[FAIL] python-dotenv is NOT installed.")
    print("       Fix: pip install python-dotenv")
    sys.exit(1)

# 2. Check for the API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("[FAIL] GEMINI_API_KEY not found in your .env file.")
    print("       Fix: add this line to .env (no quotes, no spaces around =):")
    print("       GEMINI_API_KEY=your_actual_key_here")
    sys.exit(1)
else:
    masked = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
    print(f"[OK]   GEMINI_API_KEY found: {masked}")

# 3. Check google-genai is installed (the NEW unified SDK)
try:
    from google import genai
    print("[OK]   google-genai is installed")
except ImportError:
    print("[FAIL] google-genai is NOT installed.")
    print("       Fix: pip install google-genai")
    print("       (Note: this is different from the old 'google-generativeai' package —")
    print("        if you have that one instead, uninstall it and install google-genai.)")
    sys.exit(1)

# 4. Try an actual API call
print("\nAttempting a real request to Gemini...")

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
       model="gemini-flash-latest",
        contents="Reply with exactly: Connection successful"
    )

    if response and response.text:
        print(f"[OK]   Gemini responded: {response.text.strip()}")
        print("\n✅ Everything is working — Milo should be using Gemini for fallback replies.")
    else:
        print("[FAIL] Gemini returned an empty response.")

except Exception as e:
    print(f"[FAIL] API call failed with an error:\n       {type(e).__name__}: {e}")
    print("\nCommon causes:")
    print("  - Invalid or expired API key")
    print("  - No internet connection")
    print("  - Model name 'gemini-2.0-flash' unavailable on your account/region")