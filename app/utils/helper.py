import json
import ast
import httpx
from app.config.settings import settings

async def convert_string_to_json(input_string: str):
    try:
        # Find the index of the first curly brace
        start_index = input_string.find('{')
        
        # If no curly brace is found, return an error
        if start_index == -1:
            raise ValueError("No JSON object found in string")
        
        # Extract the JSON string
        json_string = input_string[start_index:]
        
        # Load the JSON
        data = json.loads(json_string)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    except ValueError as e:
        raise ValueError(str(e))

async def call_ai_model(prompt: str):
    if settings.USE_OPEN_ROUTER:
        return await call_open_router(prompt)
    else:
        try:
            return await call_ollama(prompt)
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            # Fallback to OpenRouter if Ollama fails
            return await call_open_router(prompt)
        
async def call_ollama(prompt: str):
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", settings.OLLAMA_ENDPOINT, json={
            "model": settings.AI_MODEL,
            "prompt": prompt
        }) as response:
            content = ""
            async for chunk in response.aiter_text():
                chunk = json.loads(chunk)
                content += chunk['response']
            return content

async def call_open_router(prompt: str):
    headers = {
        "Authorization": f"Bearer {settings.OPEN_ROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = json.dumps({
        "model": settings.OPEN_ROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    })
    async with httpx.AsyncClient() as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=data)
        return response.json()['choices'][0]['message']['content']