import os

from google import genai

API_KEY = os.getenv("GEMINI_KEY")

client = genai.Client(api_key=API_KEY)

def generate_response(message: str) -> str:
    response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=message
    )
    return response.text