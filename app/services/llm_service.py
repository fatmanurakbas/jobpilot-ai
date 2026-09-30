"""LLM service integration."""
from openai import OpenAI

from app.config import settings


class LLMService:

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key
        )

    def parse(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model
    ):
        response = self.client.responses.parse(
            model=settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            text_format=response_model
        )

        return response.output_parsed


llm_service = LLMService()