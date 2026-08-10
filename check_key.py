##checked the AI keyS
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
print("Key prefix:", key[:10])

client = genai.Client(api_key=key)

try:
    print("Listing models...")
    models = client.models.list()

    for model in models:
        print(model.name)
        break

    print("✅ Connection successful!")

except Exception as e:
    print("❌ Connection failed:")
    print(repr(e))