from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Get the API key from environment
api_key = os.getenv("TELKOM_API_KEY")
print(f"API Key loaded: {api_key is not None}")

client = OpenAI(
    api_key=api_key,
    base_url="https://telkom-ai-dag-api.apilogy.id/Telkom-LLM/0.0.4/llm",
    default_headers={"x-api-key": api_key},
)

try:
    completions = client.chat.completions.create(
        model="telkom-ai",
        messages=[
            {
                "role": "user",
                "content": "Hello, what do you know about Telkom University?",
            }
        ],
    )

    print(completions.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")
