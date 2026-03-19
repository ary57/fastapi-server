import os

from google import genai

API_KEY = os.getenv("GEMINI_KEY")
if not API_KEY:
    raise ValueError("GEMINI_KEY is missing. Set GEMINI_KEY in environment variables.")

client = genai.Client(api_key=API_KEY)

def generate_response(message: str) -> str:
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=message,
    )
    return response.text