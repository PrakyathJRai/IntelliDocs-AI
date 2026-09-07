import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model=model,
    contents="Say hello and explain what IntelliDocs AI is in one sentence."
)

print("\nGemini response:")
print(response.text)