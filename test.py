import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()  # <— THIS IS THE FIX

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

for model in genai.list_models():
    print(model.name)
