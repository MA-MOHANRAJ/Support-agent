import os
import time
from typing import Optional, List
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError


load_dotenv()


class LLMClient:

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.primary_model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        self.model = self.primary_model

        # Fallback models available on endpoint if primary hits token limits
        self.fallback_models = [
            self.primary_model,
            "openai/gpt-oss-20b",
            "qwen/qwen3.6-27b"
        ]
        # Remove duplicates while preserving order
        self.fallback_models = list(dict.fromkeys(self.fallback_models))

        if not self.api_key:
            raise ValueError("LLM_API_KEY is missing. Add it to your .env file.")

        if not self.base_url:
            raise ValueError("LLM_BASE_URL is missing.")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        seed: Optional[int] = None,
        max_tokens: int = 2048,
        max_retries: int = 4
    ) -> str:
        """
        Generates completion with automatic retry, exponential backoff, and multi-model fallback.
        """
        last_error = None
        for model_candidate in self.fallback_models:
            backoff = 3.0
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=model_candidate,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=temperature,
                        seed=seed,
                        max_tokens=max_tokens
                    )
                    self.model = model_candidate
                    return response.choices[0].message.content
                except RateLimitError as rle:
                    last_error = rle
                    if attempt < max_retries - 1:
                        print(f"\n[Rate Limit on {model_candidate} (429). Retrying in {backoff:.1f}s...]")
                        time.sleep(backoff)
                        backoff *= 2.0
                    else:
                        print(f"\n[Failing over from {model_candidate} to next model...]")
                        break
                except APIError as apie:
                    last_error = apie
                    if attempt < max_retries - 1 and ("rate" in str(apie).lower() or "429" in str(apie)):
                        print(f"\n[API Rate Limit on {model_candidate}. Retrying in {backoff:.1f}s...]")
                        time.sleep(backoff)
                        backoff *= 2.0
                    else:
                        break

        if last_error:
            raise last_error
        raise RuntimeError("Failed to generate LLM completion after trying all fallback models.")