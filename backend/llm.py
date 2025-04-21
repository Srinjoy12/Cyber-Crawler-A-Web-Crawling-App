from openai import AsyncOpenAI
import os

# Initialize OpenAI client with API key from environment variable
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def ask_llm(question: str, context: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return "Error: OPENAI_API_KEY environment variable not set"
        
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
        ]
    )
    return response.choices[0].message.content
