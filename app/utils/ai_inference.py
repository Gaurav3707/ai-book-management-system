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
            if settings.USE_LOCAL_MODEL is True:
                logger.debug("Using Locally deployed Model for AI inference.")
                return await InferenceHelper.call_local_model(prompt)
            else:
                logger.debug("Using hosted AI model for AI inference.")
                return await InferenceHelper.call_hosted_model(prompt)
        except Exception as e:
            logger.error(f"Error during AI model call: {e}")
            logger.debug("Falling back to Ollama model.")
            return await InferenceHelper.call_hosted_model(prompt)

    @staticmethod
    async def call_local_model(prompt: str):
        logger.info("Calling Ollama model.")
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", settings.LOCALLY_DEPLOYED_LLM_ENDPOINT, json={
                "model": settings.LOCAL_AI_MODEL,
                "prompt": prompt
            }) as response:
                content = ""
                async for chunk in response.aiter_text():
                    chunk = json.loads(chunk)
                    content += chunk['response']
                logger.debug("Ollama response received.")
                return content

    @staticmethod
    async def call_hosted_model(prompt: str):
        logger.info("Calling hosted AI model.")
        headers = {
            "Authorization": f"Bearer {settings.HOSTED_MODEL_API_KEY}",
            "Content-Type": "application/json",
        }
        data = json.dumps({
            "model": settings.HOSTED_MODEL_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        })
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.HOSTED_MODEL_ENDPOINT, headers=headers, data=data)
            if response.status_code == 429:  # HTTP 429 Too Many Requests
                logger.error("Rate limit exceeded for hosted AI model.")
                return None
            logger.debug(f"Together AI response: {response.text}")
            if 'choices' in response.json():
                logger.debug("Hosted AI model response received.")
                return response.json()['choices'][0]['message']['content']
            else:
                logger.error("Invalid response from hosted AI model.")
                return None
    