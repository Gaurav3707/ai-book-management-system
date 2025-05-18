import json
import ast
import httpx
from app.config.settings import settings

async def convert_string_to_json(response):
        try:
            start_idx = response.index('{') if '{' in response else None
            end_idx = response.rfind('}') if '}' in response else None

            if start_idx is not None and end_idx is not None:
                trimmed = response[start_idx:end_idx + 1]
            elif start_idx is not None:
                trimmed = response[start_idx:]
            elif end_idx is not None:
                trimmed = response[:end_idx + 1]
            else:
                trimmed = response

            trimmed = trimmed.replace("```json", "").replace("```", "")
        except Exception as e:
            trimmed = response

        try:
            return json.loads(trimmed)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(trimmed)
            except Exception as e:
                return response