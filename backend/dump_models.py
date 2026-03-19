import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

try:
    models = client.models.list()
    with open("models_full_list.txt", "w") as f:
        for m in models:
            f.write(f"{m.name}\n")
    print("Models written to models_full_list.txt")
except Exception as e:
    print(f"Error: {e}")
