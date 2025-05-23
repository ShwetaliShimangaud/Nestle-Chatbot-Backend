import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

async def get_chat_response(message: str) -> str:
    return message
    # response = openai.ChatCompletion.create(
    #     model="gpt-4",
    #     messages=[{"role": "user", "content": message}],
    # )
    # return response['choices'][0]['message']['content']
