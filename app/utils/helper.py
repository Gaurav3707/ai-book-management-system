import json
import ast
import httpx
from app.config.settings import settings
from fastapi import HTTPException

async def call_ai_model(prompt: str):
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "prompt": prompt,
        "max_tokens": 200,
    }

    if settings.USE_OPEN_ROUTER:
        headers["Authorization"] = f"Bearer {settings.OPEN_ROUTER_API_KEY}"
        data["model"] = settings.OPEN_ROUTER_MODEL
        url = settings.OPEN_ROUTER_URL
    else:
        data["model"] = settings.AI_MODEL
        url = settings.LOCAL_AI_URL

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            content = response.json()
            return content["choices"][0]["text"].strip()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"AI Model API Error: {e}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to AI Model API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


def convert_string_to_json(input_string: str):
    try:
        # Manually replace single quotes with double quotes for valid JSON
        json_string = input_string.replace("'", "\"")
        data = json.loads(json_string)
        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None