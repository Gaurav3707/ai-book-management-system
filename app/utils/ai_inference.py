import json
import httpx
from app.config.settings import settings

class InferenceHelper:
    @staticmethod
    async def call_ai_model(prompt: str):
        if settings.USE_OPEN_ROUTER and settings.USE_OPEN_ROUTER is True:
            return await InferenceHelper.call_open_router(prompt)
        else:
            try:
                return await InferenceHelper.call_ollama(prompt)
            except Exception as e:
                print(f"Error calling Ollama: {e}")
                # Fallback to OpenRouter if Ollama fails
                return await InferenceHelper.call_open_router(prompt)

    @staticmethod
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

    @staticmethod
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
            print(f"Response: {response.text}")
            return response.json()['choices'][0]['message']['content']
