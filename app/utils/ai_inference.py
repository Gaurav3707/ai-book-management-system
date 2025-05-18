import json
import httpx
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class InferenceHelper:
    @staticmethod
    async def call_ai_model(prompt: str):
        logger.info("Calling AI model.")
        try:
            if settings.USE_OPEN_ROUTER and settings.USE_OPEN_ROUTER is True:
                logger.debug("Using OpenRouter for AI inference.")
                return await InferenceHelper.call_open_router(prompt)
            else:
                logger.debug("Using Ollama for AI inference.")
                return await InferenceHelper.call_ollama(prompt)
        except Exception as e:
            logger.error(f"Error during AI model call: {e}")
            logger.debug("Falling back to Ollama model.")
            return await InferenceHelper.call_open_router(prompt)

    @staticmethod
    async def call_ollama(prompt: str):
        logger.info("Calling Ollama model.")
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", settings.OLLAMA_ENDPOINT, json={
                "model": settings.AI_MODEL,
                "prompt": prompt
            }) as response:
                content = ""
                async for chunk in response.aiter_text():
                    chunk = json.loads(chunk)
                    content += chunk['response']
                logger.debug("Ollama response received.")
                return content

    @staticmethod
    async def call_open_router(prompt: str):
        logger.info("Calling OpenRouter model.")
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
            logger.debug(f"OpenRouter response: {response.text}")
            return response.json()['choices'][0]['message']['content']
